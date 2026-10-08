/**
 * Real image encoding pipeline.
 *
 * Everything here is synchronous on purpose: the editor must be able to hand
 * a browser a ready-to-save file (a fetchable URL plus the exact byte count)
 * in the same render that its settings become valid — never a placeholder
 * `#` href that would resolve to the document itself.
 *
 *   - "Original"  → the untouched source bytes, as a Blob URL.
 *   - JPEG/WebP/PNG → the browser's own encoders, via canvas `toDataURL`.
 *   - QOI → a compact lossless encoder implemented below.
 *   - AVIF/JXL (which this browser cannot emit) degrade to real JPEG, and the
 *     file name reports the format actually produced.
 */

export const IDENTITY = "identity";

export type EncodeRequest = {
  /** Decoded source pixels. */
  source: CanvasImageSource;
  /** Exact bytes of the file the user opened (used for the "Original" codec). */
  sourceBlob: Blob;
  /** Source pixel size. */
  naturalWidth: number;
  naturalHeight: number;
  /** Requested output size before rotation. */
  width: number;
  height: number;
  /** Clockwise rotation in degrees (a multiple of 90). */
  rotate: number;
  codec: string;
  /** 0-100 quality for lossy codecs. */
  quality: number;
};

export type EncodeResult = {
  /** Fetchable URL (data: or blob:) of the produced bytes. */
  url: string;
  bytes: number;
  width: number;
  height: number;
  /** MIME type actually produced. */
  type: string;
};

/** Codec keys match the encoder identifiers the reference UI exposes. */
const NATIVE_MIME: Record<string, string | null> = {
  browserJPEG: "image/jpeg",
  mozJPEG: "image/jpeg",
  webP: "image/webp",
  wp2: "image/webp",
  browserPNG: "image/png",
  oxiPNG: "image/png",
  avif: "image/avif",
  jxl: "image/jxl",
  qoi: null,
};

/** Extension used when the browser produced exactly what was asked for. */
const EXTENSION: Record<string, string> = {
  browserJPEG: "jpg",
  mozJPEG: "jpg",
  webP: "webp",
  wp2: "webp2",
  browserPNG: "png",
  oxiPNG: "png",
  avif: "avif",
  jxl: "jxl",
  qoi: "qoi",
};

const EXT_BY_MIME: Record<string, string> = {
  "image/jpeg": "jpg",
  "image/png": "png",
  "image/webp": "webp",
  "image/qoi": "qoi",
  "image/avif": "avif",
  "application/octet-stream": "png",
};

/**
 * Names the saved file after the bytes we actually produced — so a codec the
 * browser can't emit (e.g. AVIF) downloads with its real, honest extension.
 */
export function fileNameFor(
  codec: string,
  sourceName: string,
  producedType: string,
): string {
  const stem = sourceName.replace(/\.[^.]+$/, "");
  if (codec === IDENTITY) {
    const match = sourceName.match(/\.([a-z0-9]+)$/i);
    return `${stem}.${match ? match[1].toLowerCase() : "png"}`;
  }
  const native = NATIVE_MIME[codec];
  if (native && producedType && producedType !== native) {
    return `${stem}.${EXT_BY_MIME[producedType] ?? "jpg"}`;
  }
  if (producedType && EXT_BY_MIME[producedType]) {
    return `${stem}.${EXT_BY_MIME[producedType]}`;
  }
  return `${stem}.${EXTENSION[codec] ?? "png"}`;
}

function outDimensions(req: EncodeRequest) {
  const quarterTurn = req.rotate % 180 !== 0;
  const w = Math.max(1, Math.round(req.width));
  const h = Math.max(1, Math.round(req.height));
  return quarterTurn ? { w: h, h: w } : { w, h };
}

/** Draws the source into a fresh canvas, honouring rotation. */
function renderCanvas(req: EncodeRequest): HTMLCanvasElement {
  const { w, h } = outDimensions(req);
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("2D context unavailable");
  ctx.save();
  ctx.translate(w / 2, h / 2);
  ctx.rotate((req.rotate * Math.PI) / 180);
  ctx.drawImage(req.source, -req.width / 2, -req.height / 2, req.width, req.height);
  ctx.restore();
  return canvas;
}

/** Byte length of the payload inside a `data:` URL, computed in O(1). */
function dataUrlBytes(dataUrl: string): number {
  const comma = dataUrl.indexOf(",");
  if (comma < 0) return 0;
  const body = dataUrl.length - comma - 1;
  let padding = 0;
  if (dataUrl.endsWith("==")) padding = 2;
  else if (dataUrl.endsWith("=")) padding = 1;
  return Math.floor((body * 3) / 4) - padding;
}

/** The untouched source file, ready to download. */
export function sourceResult(sourceBlob: Blob): EncodeResult {
  return {
    url: URL.createObjectURL(sourceBlob),
    bytes: sourceBlob.size,
    width: 0,
    height: 0,
    type: sourceBlob.type || "application/octet-stream",
  };
}

/** The untouched source at its true (possibly rotated) dimensions. */
export function originalResult(req: EncodeRequest): EncodeResult {
  const { w, h } = outDimensions(req);
  return { ...sourceResult(req.sourceBlob), width: w, height: h };
}

/**
 * Encodes one side of the comparison and returns ready-to-save bytes.
 * Never throws for an unknown codec — it degrades to JPEG.
 */
export function encodeImage(req: EncodeRequest): EncodeResult {
  if (req.codec === IDENTITY) return originalResult(req);

  const canvas = renderCanvas(req);
  const { w, h } = outDimensions(req);

  if (req.codec === "qoi") {
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("2D context unavailable");
    const pixels = ctx.getImageData(0, 0, w, h);
    const blob = encodeQoi(pixels.data, w, h);
    return {
      url: URL.createObjectURL(blob),
      bytes: blob.size,
      width: w,
      height: h,
      type: "image/qoi",
    };
  }

  const mime = NATIVE_MIME[req.codec] ?? "image/jpeg";
  const quality = Math.min(1, Math.max(0.01, req.quality / 100));

  let dataUrl = canvas.toDataURL(mime, quality);
  // Browsers silently substitute PNG when they can't honour the request.
  if (!dataUrl.startsWith(`data:${mime}`)) {
    dataUrl = canvas.toDataURL("image/jpeg", quality);
  }

  const actualMime = dataUrl.slice(5, dataUrl.indexOf(";")) || "image/jpeg";
  return {
    url: dataUrl,
    bytes: dataUrlBytes(dataUrl),
    width: w,
    height: h,
    type: actualMime,
  };
}

/* --------------------------------------------------------------------------
 * QOI — "Quite OK Image". A compact lossless format the browser can't write,
 * so it is implemented directly here.
 * ------------------------------------------------------------------------ */

const QOI_OP_RGB = 0xfe;
const QOI_OP_RGBA = 0xff;
const QOI_OP_INDEX = 0x00;
const QOI_OP_DIFF = 0x40;
const QOI_OP_LUMA = 0x80;
const QOI_OP_RUN = 0xc0;

function encodeQoi(
  rgba: Uint8ClampedArray,
  width: number,
  height: number,
): Blob {
  const headerSize = 14;
  const maxSize = width * height * 5 + headerSize + 8;
  const out = new Uint8Array(maxSize);
  let p = 0;

  // magic "qoif", width, height, channels, colorspace
  out[p++] = 0x71; // q
  out[p++] = 0x6f; // o
  out[p++] = 0x69; // i
  out[p++] = 0x66; // f
  out[p++] = (width >>> 24) & 0xff;
  out[p++] = (width >>> 16) & 0xff;
  out[p++] = (width >>> 8) & 0xff;
  out[p++] = width & 0xff;
  out[p++] = (height >>> 24) & 0xff;
  out[p++] = (height >>> 16) & 0xff;
  out[p++] = (height >>> 8) & 0xff;
  out[p++] = height & 0xff;
  out[p++] = 4; // channels (RGBA)
  out[p++] = 0; // sRGB with linear alpha

  const index = new Uint8Array(64 * 4);
  let r = 0;
  let g = 0;
  let b = 0;
  let a = 255;
  let run = 0;

  const hash = (rr: number, gg: number, bb: number, aa: number) =>
    (rr * 3 + gg * 5 + bb * 7 + aa * 11) % 64;

  for (let i = 0; i < width * height; i++) {
    const off = i * 4;
    const pr = r;
    const pg = g;
    const pb = b;
    const pa = a;
    r = rgba[off];
    g = rgba[off + 1];
    b = rgba[off + 2];
    a = rgba[off + 3];

    if (r === pr && g === pg && b === pb && a === pa) {
      run++;
      if (run === 62) {
        out[p++] = QOI_OP_RUN | (run - 1);
        run = 0;
      }
      continue;
    }
    if (run > 0) {
      out[p++] = QOI_OP_RUN | (run - 1);
      run = 0;
    }

    const slot = hash(r, g, b, a) * 4;
    if (
      index[slot] === r &&
      index[slot + 1] === g &&
      index[slot + 2] === b &&
      index[slot + 3] === a
    ) {
      out[p++] = QOI_OP_INDEX | (slot / 4);
      continue;
    }
    index[slot] = r;
    index[slot + 1] = g;
    index[slot + 2] = b;
    index[slot + 3] = a;

    if (a === pa) {
      const dr = r - pr;
      const dg = g - pg;
      const db = b - pb;
      if (dr > -3 && dr < 2 && dg > -3 && dg < 2 && db > -3 && db < 2) {
        out[p++] = QOI_OP_DIFF | ((dr + 2) << 4) | ((dg + 2) << 2) | (db + 2);
        continue;
      }
      const drdg = dr - dg;
      const dbdg = db - dg;
      if (dg > -33 && dg < 32 && drdg > -9 && drdg < 8 && dbdg > -9 && dbdg < 8) {
        out[p++] = QOI_OP_LUMA | (dg + 32);
        out[p++] = ((drdg + 8) << 4) | (dbdg + 8);
        continue;
      }
    }
    if (a === pa) {
      out[p++] = QOI_OP_RGB;
      out[p++] = r;
      out[p++] = g;
      out[p++] = b;
    } else {
      out[p++] = QOI_OP_RGBA;
      out[p++] = r;
      out[p++] = g;
      out[p++] = b;
      out[p++] = a;
    }
  }
  if (run > 0) out[p++] = QOI_OP_RUN | (run - 1);

  // 7 zero bytes + 0x01 terminator
  for (let i = 0; i < 8; i++) out[p++] = i === 7 ? 1 : 0;

  return new Blob([out.slice(0, p)], { type: "image/qoi" });
}
