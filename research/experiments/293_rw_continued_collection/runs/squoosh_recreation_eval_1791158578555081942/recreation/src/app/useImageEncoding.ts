import { useEffect, useRef, useState } from "react";
import { encodeImage, type EncodeResult } from "@/app/encoder";

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
  /** Object URL of the encoded bytes, or null while the first pass runs. */
  url: string | null;
  bytes: number;
  width: number;
  height: number;
  type: string;
  busy: boolean;
};

const EMPTY: EncodeState = {
  url: null,
  bytes: 0,
  width: 0,
  height: 0,
  type: "",
  busy: true,
};

/**
 * Encodes one side of the editor whenever its settings settle. Results carry
 * the real byte size and pixel dimensions of the produced file.
 */
export function useEncodedImage(
  img: HTMLImageElement | null,
  sourceBlob: Blob | null,
  options: EncodeOptions,
): EncodeState {
  const [state, setState] = useState<EncodeState>(EMPTY);
  const urlRef = useRef<string | null>(null);

  const { codec, quality, width, height, resizeEnabled, rotate } = options;

  useEffect(() => {
    if (!img || !sourceBlob) return;
    let cancelled = false;

    setState((prev) => ({ ...prev, busy: true }));

    const timer = window.setTimeout(async () => {
      try {
        const result: EncodeResult = await encodeImage({
          bitmap: img,
          sourceBlob,
          codec,
          quality,
          width: resizeEnabled ? width : img.naturalWidth,
          height: resizeEnabled ? height : img.naturalHeight,
          rotate,
        });
        if (cancelled) {
          URL.revokeObjectURL(result.url);
          return;
        }
        if (urlRef.current) URL.revokeObjectURL(urlRef.current);
        urlRef.current = result.url;
        setState({
          url: result.url,
          bytes: result.bytes,
          width: result.width,
          height: result.height,
          type: result.type,
          busy: false,
        });
      } catch {
        if (!cancelled) setState((prev) => ({ ...prev, busy: false }));
      }
    }, 140);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [img, sourceBlob, codec, quality, width, height, resizeEnabled, rotate]);

  useEffect(
    () => () => {
      if (urlRef.current) URL.revokeObjectURL(urlRef.current);
    },
    [],
  );

  return state;
}
