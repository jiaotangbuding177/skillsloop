import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CompareView } from "@/components/CompareView";
import {
  BackgroundIcon,
  MinusIcon,
  PlusIcon,
  RotateIcon,
  SmoothingIcon,
} from "@/components/icons";
import { OptionsPanel, type OptionValue } from "@/components/OptionsPanel";
import { ResultsBubble } from "@/components/ResultsBubble";
import {
  CODECS,
  ORIGINAL_ID,
  codecById,
  defaultValues,
} from "@/app/codecs";
import { estimateBytes, formatBytes, reductionPercent } from "@/app/encode";
import type { LoadedImage } from "@/app/demos";
import { cn } from "@/utils/cn";

type Props = {
  image: LoadedImage;
  onBack: () => void;
  onNotice: (message: string) => void;
  onTitle: (title: string) => void;
};

type SideState = {
  codec: string;
  values: Record<string, OptionValue>;
  resizeEnabled: boolean;
  resize: { width: number; height: number; percent: number; method: string };
  paletteEnabled: boolean;
};

function initialSide(image: LoadedImage, codec: string): SideState {
  const def = codecById(codec);
  return {
    codec,
    values: def ? defaultValues(def) : { quality: 75 },
    resizeEnabled: false,
    resize: {
      width: image.width,
      height: image.height,
      percent: 100,
      method: "Lanczos3",
    },
    paletteEnabled: false,
  };
}

export function EditorPage({ image, onBack, onNotice, onTitle }: Props) {
  const [sideA, setSideA] = useState<SideState>(() =>
    initialSide(image, ORIGINAL_ID),
  );
  const [sideB, setSideB] = useState<SideState>(() =>
    initialSide(image, image.codec),
  );

  const [zoom, setZoom] = useState(1);
  const [smoothing, setSmoothing] = useState(true);
  const [altBackground, setAltBackground] = useState(false);
  const [split, setSplit] = useState(0.5);
  const [busy, setBusy] = useState(true);
  const [savedSettings, setSavedSettings] = useState<SideState | null>(null);
  const [dragValid, setDragValid] = useState(false);
  const dragDepth = useRef(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const [reloads, setReloads] = useState(0);

  useEffect(() => {
    onTitle(`${image.filename} - Squoosh`);
  }, [image.filename, onTitle]);

  // Simulate the encode pipeline so the layout settles like the reference.
  useEffect(() => {
    setBusy(true);
    const t = window.setTimeout(() => setBusy(false), 420);
    return () => window.clearTimeout(t);
  }, [sideB.codec, sideB.values, sideB.resize, image.url]);

  const sourceBytes = image.bytes;

  const outputBytes = useMemo(() => {
    if (sideB.codec === ORIGINAL_ID) return sourceBytes;
    const quality =
      typeof sideB.values.quality === "number" ? sideB.values.quality : 75;
    let bytes = estimateBytes(sourceBytes, sideB.codec, quality);
    if (sideB.resizeEnabled) {
      const scale =
        (sideB.resize.width * sideB.resize.height) /
        Math.max(1, image.width * image.height);
      bytes = Math.round(bytes * Math.max(0.01, Math.min(1, scale)));
    }
    return bytes;
  }, [sideB, sourceBytes, image.width, image.height]);

  const outputLabel = formatBytes(outputBytes);
  const reduction = reductionPercent(sourceBytes, outputBytes);

  const setCodec = useCallback((which: "a" | "b", id: string) => {
    const setter = which === "a" ? setSideA : setSideB;
    const def = codecById(id);
    setter((prev) => ({
      ...prev,
      codec: id,
      values: def ? defaultValues(def) : {},
    }));
  }, []);

  const setValue = useCallback(
    (which: "a" | "b", key: string, value: OptionValue) => {
      const setter = which === "a" ? setSideA : setSideB;
      setter((prev) => ({ ...prev, values: { ...prev.values, [key]: value } }));
    },
    [],
  );

  const download = useCallback(async () => {
    setBusy(true);
    try {
      const href = await encodeToBlobUrl(image, sideB);
      const a = document.createElement("a");
      a.href = href;
      a.download = downloadName(image.filename, sideB.codec);
      document.body.appendChild(a);
      a.click();
      a.remove();
      onNotice(`${a.download} downloaded`);
    } catch {
      onNotice("Couldn't download that image");
    } finally {
      setBusy(false);
    }
  }, [image, sideB, onNotice]);

  const openFile = useCallback(
    (file: File | null | undefined) => {
      if (!file) return;
      if (!file.type.startsWith("image/")) {
        onNotice("That doesn't look like an image");
        return;
      }
      const url = URL.createObjectURL(file);
      const probe = new Image();
      probe.onload = () => {
        // Swap the active bitmap without a full route change.
        window.dispatchEvent(
          new CustomEvent("squoosh:replace", {
            detail: {
              url,
              filename: file.name,
              width: probe.naturalWidth,
              height: probe.naturalHeight,
              bytes: file.size,
              userProvided: true,
              codec: file.type === "image/png" ? "oxipng" : "mozjpeg",
            },
          }),
        );
      };
      probe.src = url;
    },
    [onNotice],
  );

  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail as LoadedImage;
      setSideA(() => initialSide(detail, ORIGINAL_ID));
      setSideB(() => initialSide(detail, detail.codec));
      setReloads((n) => n + 1);
    };
    window.addEventListener("squoosh:replace", handler);
    return () => window.removeEventListener("squoosh:replace", handler);
  }, []);

  const clampedZoom = Math.max(0.05, Math.min(16, zoom));

  const viewportImage = image.url;

  return (
    <div className="editor-root">
      <div
        className={cn("abs-fill editor-stage", dragValid && "drag-valid")}
        onDragEnter={(e) => {
          e.preventDefault();
          dragDepth.current += 1;
          setDragValid(true);
        }}
        onDragOver={(e) => e.preventDefault()}
        onDragLeave={() => {
          dragDepth.current -= 1;
          if (dragDepth.current <= 0) setDragValid(false);
        }}
        onDrop={(e) => {
          e.preventDefault();
          dragDepth.current = 0;
          setDragValid(false);
          openFile(e.dataTransfer?.files?.[0]);
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          className="visually-hidden"
          onChange={(e) => {
            openFile(e.target.files?.[0]);
            e.target.value = "";
          }}
        />

        {/* ---- image viewer ---------------------------------------------- */}
        <div className="viewer">
          <div
            className={cn("viewer-canvas", smoothing ? "smooth" : "crisp")}
            style={{
              width: `${image.width * clampedZoom}px`,
              height: `${image.height * clampedZoom}px`,
              maxWidth: "100%",
              maxHeight: "100%",
            }}
          >
            <CompareView
              leftSrc={viewportImage}
              rightSrc={viewportImage}
              leftAlt={`${image.filename}, original`}
              rightAlt={`${image.filename}, compressed`}
              split={split}
              onSplitChange={setSplit}
            />
          </div>
          <div className={cn("viewer-overlay", altBackground && "alt")} />
        </div>

        {/* ---- shell ----------------------------------------------------- */}
        <div className="editor-shell">
          <button
            className="back-btn"
            type="button"
            aria-label="Back"
            onClick={onBack}
          >
            <BackButtonGlyph />
          </button>

          <div className="viewer-controls">
            <div className="zoom-group">
              <button
                className="vc-btn"
                type="button"
                aria-label="Zoom out"
                onClick={() => setZoom((z) => Math.max(0.05, z / 1.2))}
              >
                <MinusIcon />
              </button>
              <span className="vc-zoom">
                <input
                  aria-label="Zoom"
                  value={Math.round(clampedZoom * 100)}
                  onChange={(e) =>
                    setZoom(Number(e.target.value.replace(/\D/g, "") || 100) / 100)
                  }
                />
                <span className="zoom-unit">%</span>
              </span>
              <button
                className="vc-btn"
                type="button"
                aria-label="Zoom in"
                onClick={() => setZoom((z) => Math.min(16, z * 1.2))}
              >
                <PlusIcon />
              </button>
            </div>

            <div className="tool-group">
              <button
                className="vc-btn"
                type="button"
                aria-label="Rotate"
                onClick={() => onNotice("Rotate is not available in this build")}
              >
                <RotateIcon />
              </button>
              <button
                className={cn("vc-btn", !smoothing && "is-active")}
                type="button"
                aria-label="Toggle smoothing"
                aria-pressed={!smoothing}
                onClick={() => setSmoothing((v) => !v)}
              >
                <SmoothingIcon />
              </button>
              <button
                className={cn("vc-btn", altBackground && "is-active")}
                type="button"
                aria-label="Toggle background"
                aria-pressed={altBackground}
                onClick={() => setAltBackground((v) => !v)}
              >
                <BackgroundIcon />
              </button>
            </div>
          </div>

          {/* left (original) results */}
          <div className="opts-panel side-a">
            <div className="opts-stack">
              <div className="opts-scroller">
                <h3
                  className={cn(
                    "panel-title",
                    sideA.codec === ORIGINAL_ID && "is-original-title",
                  )}
                >
                  Compress
                </h3>
                <div className="option-one-cell">
                  <div className="sel-wrap">
                    <select
                      aria-label="Original codec"
                      value={sideA.codec}
                      onChange={(e) => setCodec("a", e.target.value)}
                    >
                      <option value={ORIGINAL_ID}>
                        Original Image ({image.filename})
                      </option>
                      {CODECS.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.label}
                        </option>
                      ))}
                    </select>
                    <Caret />
                  </div>
                </div>
              </div>
              <ResultsBubble
                side="a"
                original={sideA.codec === ORIGINAL_ID}
                size={formatBytes(sourceBytes)}
                ratio={0}
                busy={false}
                onDownload={() => onNotice("That's the original image")}
              />
            </div>
          </div>

          {/* right (compressed) options + results */}
          <OptionsPanel
            side="b"
            image={image}
            codec={sideB.codec}
            onCodecChange={(id) => setCodec("b", id)}
            values={sideB.values}
            onValueChange={(k, v) => setValue("b", k, v)}
            resizeEnabled={sideB.resizeEnabled}
            onResizeToggle={(v) =>
              setSideB((p) => ({ ...p, resizeEnabled: v }))
            }
            resize={sideB.resize}
            onResizeChange={(patch) =>
              setSideB((p) => ({ ...p, resize: { ...p.resize, ...patch } }))
            }
            paletteEnabled={sideB.paletteEnabled}
            onPaletteToggle={(v) =>
              setSideB((p) => ({ ...p, paletteEnabled: v }))
            }
            onCopyOver={() =>
              setSideA({ ...sideB, codec: sideB.codec })
            }
            onSave={() => {
              setSavedSettings(sideB);
              onNotice("Settings saved");
            }}
            onImport={() => {
              if (savedSettings) {
                setSideB(savedSettings);
                onNotice("Settings restored");
              }
            }}
            canImport={savedSettings !== null}
            results={
              <ResultsBubble
                side="b"
                size={outputLabel}
                ratio={reduction}
                busy={busy}
                onDownload={() => void download()}
              />
            }
          />
        </div>

        {busy && reloads === 0 && (
          <div className="editor-loader">
            <span className="spinner" />
          </div>
        )}
      </div>
    </div>
  );
}

function BackButtonGlyph() {
  return (
    <svg viewBox="-1.25 -1.25 2.5 2.5" aria-hidden="true">
      <path
        className="back-blob"
        d="M1.0195 -0.0822C1.0178 0.1726 0.7931 0.6155 0.5963 0.7996C0.3996 0.9837 0.0936 1.0947 -0.1611 1.0225C-0.4158 0.9504 -0.8135 0.6074 -0.9319 0.3667C-1.0504 0.1261 -0.972 -0.2056 -0.8719 -0.4212C-0.7719 -0.6368 -0.5781 -0.8756 -0.3317 -0.927C-0.0853 -0.9783 0.3811 -0.87 0.6063 -0.7292C0.8315 -0.5884 1.0211 -0.3369 1.0195 -0.0822Z"
      />
      <path
        className="back-x"
        d="M-0.42 -0.42L0.42 0.42M0.42 -0.42L-0.42 0.42"
        stroke="#fff"
        strokeWidth="0.19"
        strokeLinecap="round"
        fill="none"
      />
    </svg>
  );
}

function Caret() {
  return (
    <svg className="sel-arrow" viewBox="0 0 10 6" aria-hidden="true">
      <path d="M0 0h10L5 6z" />
    </svg>
  );
}

/** Encodes the current image via canvas so downloads are real files. */
async function encodeToBlobUrl(
  image: LoadedImage,
  side: SideState,
): Promise<string> {
  if (side.codec === ORIGINAL_ID) return image.url;
  const img = await loadImg(image.url);
  const width = side.resizeEnabled ? side.resize.width : img.naturalWidth;
  const height = side.resizeEnabled ? side.resize.height : img.naturalHeight;
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, width);
  canvas.height = Math.max(1, height);
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("no 2d context");
  ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

  const quality =
    (typeof side.values.quality === "number" ? side.values.quality : 75) / 100;
  const mime = mimeFor(side.codec);
  const blob = await new Promise<Blob | null>((resolve) =>
    canvas.toBlob(resolve, mime, quality),
  );
  if (!blob) throw new Error("encode failed");
  return URL.createObjectURL(blob);
}

function loadImg(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = src;
  });
}

function mimeFor(codec: string): string {
  switch (codec) {
    case "browser-png":
    case "oxipng":
    case "qoi":
      return "image/png";
    case "webp":
    case "webp2":
      return "image/webp";
    default:
      return "image/jpeg";
  }
}

function downloadName(filename: string, codec: string): string {
  const stem = filename.replace(/\.[^.]+$/, "");
  const ext: Record<string, string> = {
    mozjpeg: "jpg",
    "browser-jpeg": "jpg",
    "browser-png": "png",
    oxipng: "png",
    qoi: "qoi",
    webp: "webp",
    webp2: "webp2",
    avif: "avif",
    jxl: "jxl",
    original: "png",
  };
  return `${stem}.${ext[codec] ?? "png"}`;
}
