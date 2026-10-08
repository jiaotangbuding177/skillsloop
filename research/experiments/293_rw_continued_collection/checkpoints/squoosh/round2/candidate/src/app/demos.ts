import avatarArtwork from "@/assets/img/avatar-artwork.jpg";
import avatarDevice from "@/assets/img/avatar-device.jpg";
import avatarLogo from "@/assets/img/avatar-logo.png";
import avatarPhoto from "@/assets/img/avatar-photo.jpg";
import demoArtwork from "@/assets/img/demo-artwork.jpg";
import demoDevice from "@/assets/img/demo-device.png";
import demoPhoto from "@/assets/img/demo-photo.jpg";
import demoSquoosh from "@/assets/img/demo-squoosh.svg";

export type Demo = {
  /** Stable key used for the loading snackbar and aria labels. */
  id: string;
  /** Alt text / accessible name of the sample. */
  label: string;
  /** Human-readable source size shown under the avatar. */
  size: string;
  /** Square avatar used in the intro grid. */
  avatar: string;
  /** Full-resolution file loaded into the editor. */
  source: string;
  /** File name used for the document title and download. */
  filename: string;
  /** Intrinsic pixel dimensions of the source file. */
  width: number;
  height: number;
  /** Codec pre-selected when the sample opens in the editor. */
  codec: string;
};

export const DEMOS: Demo[] = [
  {
    id: "photo",
    label: "Large photo",
    size: "2.8MB",
    avatar: avatarPhoto,
    source: demoPhoto,
    filename: "photo.jpg",
    width: 3872,
    height: 2592,
    codec: "mozjpeg",
  },
  {
    id: "artwork",
    label: "Artwork",
    size: "2.9MB",
    avatar: avatarArtwork,
    source: demoArtwork,
    filename: "art.jpg",
    width: 3960,
    height: 1532,
    codec: "mozjpeg",
  },
  {
    id: "device",
    label: "Device screen",
    size: "1.6MB",
    avatar: avatarDevice,
    source: demoDevice,
    filename: "pixel3.png",
    width: 706,
    height: 1442,
    codec: "webp",
  },
  {
    id: "logo",
    label: "SVG icon",
    size: "13KB",
    avatar: avatarLogo,
    source: demoSquoosh,
    filename: "squoosh.svg",
    width: 600,
    height: 600,
    codec: "oxipng",
  },
];

export type LoadedImage = {
  /** Object URL / asset URL of the loaded bitmap. */
  url: string;
  filename: string;
  width: number;
  height: number;
  /** Source byte size. */
  bytes: number;
  /** Exact bytes of the opened file, reused for the "Original" export. */
  sourceBlob: Blob;
  /** True when the file was supplied by the user rather than a demo. */
  userProvided: boolean;
  codec: string;
};

export function demoToImage(demo: Demo, sourceBlob: Blob): LoadedImage {
  return {
    url: demo.source,
    filename: demo.filename,
    width: demo.width,
    height: demo.height,
    bytes: sourceBlob.size || bytesForDemo(demo),
    sourceBlob,
    userProvided: false,
    codec: demo.codec,
  };
}

/** Fetches a bundled asset into a Blob so it can be handed back verbatim. */
export async function fetchBlob(url: string): Promise<Blob> {
  const response = await fetch(url);
  return response.blob();
}

const KB = 1024;
const MB = KB * 1024;

/** Approximate source sizes, matching the badges on the intro page. */
function bytesForDemo(demo: Demo): number {
  switch (demo.id) {
    case "photo":
      return 2.79 * MB;
    case "artwork":
      return 2.93 * MB;
    case "device":
      return 1.62 * MB;
    default:
      return 10.7 * KB;
  }
}

export async function fileToImage(file: File): Promise<LoadedImage> {
  const url = URL.createObjectURL(file);
  const dims = await measure(url);
  return {
    url,
    filename: file.name,
    width: dims.width,
    height: dims.height,
    bytes: file.size,
    // The user's exact bytes — reused untouched for the "Original" export.
    sourceBlob: file,
    userProvided: true,
    codec: pickCodec(file.type),
  };
}

/** SVG needs rasterising before any pixel codec can consume it. */
export function isVector(mime: string): boolean {
  return mime === "image/svg+xml";
}

function pickCodec(mime: string): string {
  if (mime === "image/png") return "oxipng";
  if (mime === "image/svg+xml") return "oxipng";
  if (mime === "image/webp") return "webp";
  return "mozjpeg";
}

/** Decodes a blob into the pixels used by the encoder. */
export async function decodeBitmap(blob: Blob): Promise<ImageBitmap> {
  return createImageBitmap(blob);
}

function measure(url: string): Promise<{ width: number; height: number }> {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () =>
      resolve({ width: img.naturalWidth, height: img.naturalHeight });
    img.onerror = () => resolve({ width: 0, height: 0 });
    img.src = url;
  });
}
