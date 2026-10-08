import { useEffect, useMemo, useRef, useState } from "react";
import {
  IDENTITY,
  encodeImage,
  originalResult,
  sourceResult,
  type EncodeResult,
} from "@/app/encoder";

/** Loads the editor's source bitmap once per URL. */
export function useSourceImage(url: string | undefined) {
  const [img, setImg] = useState<HTMLImageElement | null>(null);

  useEffect(() => {
    if (!url) return;
    let cancelled = false;
    const el = new Image();
    el.decoding = "async";
    el.onload = () => {
      if (!cancelled) setImg(el);
    };
    el.onerror = () => {
      if (!cancelled) setImg(null);
    };
    el.src = url;
    return () => {
      cancelled = true;
      setImg(null);
    };
  }, [url]);

  return img;
}

export type EncodeOptions = {
  codec: string;
  quality: number;
  /** Output size before rotation. */
  width: number;
  height: number;
  resizeEnabled: boolean;
  rotate: number;
};

export type EncodeState = {
  /** Fetchable URL of the produced bytes. */
  url: string;
  bytes: number;
  width: number;
  height: number;
  type: string;
  /** True until the bitmap has decoded and the real codec pass has run. */
  busy: boolean;
};

/**
 * Encodes one side of the editor synchronously from the decoded bitmap.
 *
 * Until the bitmap is ready the result falls back to the untouched source
 * bytes, so the download link is always backed by a real, fetchable file
 * rather than a placeholder.
 */
export function useEncodedImage(
  img: HTMLImageElement | null,
  sourceBlob: Blob | null,
  options: EncodeOptions,
): EncodeState {
  const { codec, quality, width, height, resizeEnabled, rotate } = options;

  const fallback = useMemo<EncodeState | null>(() => {
    if (!sourceBlob) return null;
    return { ...sourceResult(sourceBlob), busy: true };
  }, [sourceBlob]);

  // Object URLs handed out by the fallback, revoked when they go out of use.
  const fallbackUrl = fallback?.url ?? null;
  const lastFallback = useRef<string | null>(null);
  useEffect(() => {
    const previous = lastFallback.current;
    lastFallback.current = fallbackUrl;
    return () => {
      if (previous && previous !== fallbackUrl) URL.revokeObjectURL(previous);
    };
  }, [fallbackUrl]);

  const encoded = useMemo<EncodeState | null>(() => {
    if (!sourceBlob) return null;
    // The untouched source needs no decoding — it is ready immediately.
    if (codec === IDENTITY) {
      try {
        const result = originalResult({
          source: null as unknown as CanvasImageSource,
          sourceBlob,
          naturalWidth: 0,
          naturalHeight: 0,
          codec,
          quality,
          width,
          height,
          rotate,
        });
        return { ...result, busy: false };
      } catch {
        return null;
      }
    }
    if (!img) return null;
    const naturalWidth = img.naturalWidth || img.width;
    const naturalHeight = img.naturalHeight || img.height;
    if (!naturalWidth || !naturalHeight) return null;
    try {
      const result: EncodeResult = encodeImage({
        source: img,
        sourceBlob,
        naturalWidth,
        naturalHeight,
        codec,
        quality,
        width: resizeEnabled ? width : naturalWidth,
        height: resizeEnabled ? height : naturalHeight,
        rotate,
      });
      return { ...result, busy: false };
    } catch {
      return null;
    }
  }, [
    img,
    sourceBlob,
    codec,
    quality,
    width,
    height,
    resizeEnabled,
    rotate,
  ]);

  return (
    encoded ??
    fallback ?? {
      url: "",
      bytes: 0,
      width: 0,
      height: 0,
      type: "",
      busy: true,
    }
  );
}
