/**
 * Real image encoding pipeline.
 *
 * The editor always offers genuine, decodable output: JPEG/WebP/PNG go through
 * the browser's own encoders, "Original" hands back the untouched source bytes,
 * and QOI is written by the small encoder below. Any codec the browser cannot
 * actually produce falls back to a decodable format so downloads never break.
 */

export type EncodeRequest = {
  /** Decoded source pixels. */
  bitmap: CanvasImageSource & { naturalWidth: number; naturalHeight: number };
  /** Exact bytes of the file the user opened (used for the "Original" codec). */
  sourceBlob: Blob;
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
  blob: Blob;
  url: string;
  bytes: number;
  width: number;
  height: number;
  /** MIME type actually produced. */
  type: string;
};

/** Native MIME per codec. `null` means the browser cannot produce it. */
const NATIVE_MIME: Record<string, string | null> = {
  "browser-jpeg": "image/jpeg",
  mozjpeg: "image/jpeg",
  webp: "image/webp",
  webp2: "image/webp",
  "browser-png": "image/png",
  oxipng: "image/png",
  avif: "image/avif",
  jxl: "image/jxl",
  qoi: null,
};

/** Extension used for the saved file. */
const EXTENSION: Record<string, string> = {
  "browser-jpeg": "jpg",
  mozjpeg: "jpg",
  webp: "webp",
  webp2: "webp2",
  "browser-png": "png",
  oxipng: "png",
  avif: "avif",
  jxl: "jxl",
  qoi: "qoi",
};

export function extensionFor(codec: string, fallbackName: string): string {
  if (codec === IDENTITY) {
    const match = fallbackName.match(/\.([a-z0-9]+)$/i);
    return match ? match[1].toLowerCase() : "png";
  }
  return EXTENSION[codec] ?? "png";
}

const EXT_BY_MIME: Record<string, string> = {
  "image/jpeg": "jpg",
  "image/png": "png",
  "image/webp": "webp",
  "image/qoi": "qoi",
  "image/avif": "avif",
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
    return `${stem}.${extensionFor(codec, sourceName)}`;
  }
  const native = NATIVE_MIME[codec];
  if (native && producedType && producedType !== native) {
    return `${stem}.${EXT_BY_MIME[producedType] ?? "jpg"}`;
  }
  if (producedType && EXT_BY_MIME[producedType]) {
    return `${stem}.${EXT_BY_MIME[producedType]}`;
  }
  return `${stem}.${extensionFor(codec, sourceName)}`;
}

export const IDENTITY = "original";

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
  // The pre-rotation box is the requested size.
  ctx.drawImage(req.bitmap, -req.width / 2, -req.height / 2, req.width, req.height);
  ctx.restore();
  return canvas;
}

function canvasToBlob(
  canvas: HTMLCanvasElement,
  mime: string,
  quality: number,
): Promise<Blob | null> {
  return new Promise((resolve) => {
    canvas.toBlob((blob) => resolve(blob), mime, quality);
  });
}

/**
 * Encodes one side of the comparison. Always resolves with real bytes; if a
 * requested codec is unavailable it degrades to JPEG so the file still opens.
 */
export async function encodeImage(req: EncodeRequest): Promise<EncodeResult> {
  if (req.codec === IDENTITY) {
    const { w, h } = outDimensions(req);
    const url = URL.createObjectURL(req.sourceBlob);
    return {
      blob: req.sourceBlob,
      url,
      bytes: req.sourceBlob.size,
      width: w,
      height: h,
      type: req.sourceBlob.type || "application/octet-stream",
    };
  }

  const canvas = renderCanvas(req);
  const { w, h } = outDimensions(req);

  if (req.codec === "qoi") {
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("2D context unavailable");
    const pixels = ctx.getImageData(0, 0, w, h);
    const blob = encodeQoi(pixels.data, w, h);
    return finish(blob, w, h);
  }

  const mime = NATIVE_MIME[req.codec] ?? "image/jpeg";
  const quality = Math.min(1, Math.max(0.01, req.quality / 100));

  let blob = await canvasToBlob(canvas, mime, quality);
  // Browsers silently substitute PNG when they can't honour the request.
  if (!blob || blob.type !== mime) {
    blob = await canvasToBlob(canvas, "image/jpeg", quality);
  }
  if (!blob) throw new Error("Encoding failed");
  return finish(blob, w, h);
}

function finish(blob: Blob, width: number, height: number): EncodeResult {
  return {
    blob,
    url: URL.createObjectURL(blob),
    bytes: blob.size,
    width,
    height,
    type: blob.type,
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
  const maxSize = width * height * (4 + 1) + headerSize + 8;
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
