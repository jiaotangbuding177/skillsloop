import { useCallback, useEffect, useRef, useState } from "react";
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
import { CODECS, ORIGINAL_ID, codecById, defaultValues } from "@/app/codecs";
import { IDENTITY, fileNameFor } from "@/app/encoder";
import { formatBytes, reductionPercent } from "@/app/encode";
import { fileToImage, type LoadedImage } from "@/app/demos";
import {
  useEncodedImage,
  useSourceImage,
  type EncodeOptions,
} from "@/app/useImageEncoding";
import { cn } from "@/utils/cn";

type Props = {
  image: LoadedImage;
  onBack: () => void;
  onNotice: (message: string) => void;
  onTitle: (title: string) => void;
  onReplace: (image: LoadedImage) => void;
};

type SideState = {
  codec: string;
  values: Record<string, OptionValue>;
  resizeEnabled: boolean;
  resize: { width: number; height: number; method: string };
  paletteEnabled: boolean;
};

function initialSide(image: LoadedImage, codec: string): SideState {
  const def = codecById(codec);
  return {
    codec,
    values: def ? defaultValues(def) : { quality: 75 },
    resizeEnabled: false,
    resize: { width: image.width, height: image.height, method: "Lanczos3" },
    paletteEnabled: false,
  };
}

function qualityOf(side: SideState): number {
  const q = side.values.quality;
  return typeof q === "number" ? q : 75;
}

function encodeOptions(side: SideState, rotate: number): EncodeOptions {
  return {
    codec: side.codec === ORIGINAL_ID ? IDENTITY : side.codec,
    quality: qualityOf(side),
    width: side.resize.width,
    height: side.resize.height,
    resizeEnabled: side.resizeEnabled,
    rotate,
  };
}

export function EditorPage({
  image,
  onBack,
  onNotice,
  onTitle,
  onReplace,
}: Props) {
  const [sideA, setSideA] = useState<SideState>(() =>
    initialSide(image, ORIGINAL_ID),
  );
  const [sideB, setSideB] = useState<SideState>(() =>
    initialSide(image, image.codec),
  );

  const [zoom, setZoom] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [smoothing, setSmoothing] = useState(true);
  const [altBackground, setAltBackground] = useState(false);
  const [split, setSplit] = useState(0.5);
  const [savedSettings, setSavedSettings] = useState<SideState | null>(null);
  const [dragValid, setDragValid] = useState(false);
  const dragDepth = useRef(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    onTitle(`${image.filename} - Squoosh`);
  }, [image.filename, onTitle]);

  // Decode the source once; both sides encode from the same pixels.
  const sourceImg = useSourceImage(image.url);

  const outA = useEncodedImage(sourceImg, image.sourceBlob, encodeOptions(sideA, rotation));
  const outB = useEncodedImage(sourceImg, image.sourceBlob, encodeOptions(sideB, rotation));

  const sourceBytes = image.sourceBlob.size || image.bytes;
  const outputBytes = outB.bytes || 0;
  const reduction = outputBytes
    ? reductionPercent(sourceBytes, outputBytes)
    : 0;

  const setCodec = useCallback((which: "a" | "b", id: string) => {
    const def = codecById(id);
    const setter = which === "a" ? setSideA : setSideB;
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

  /** Resize keeps the source aspect ratio as either edge is edited. */
  const setResizeEdge = useCallback(
    (edge: "width" | "height", raw: number) => {
      const value = Math.max(1, Math.round(raw) || 1);
      setSideB((prev) => {
        const ratio = image.width / image.height;
        if (edge === "width") {
          return {
            ...prev,
            resize: {
              ...prev.resize,
              width: value,
              height: Math.max(1, Math.round(value / ratio)),
            },
          };
        }
        return {
          ...prev,
          resize: {
            ...prev.resize,
            height: value,
            width: Math.max(1, Math.round(value * ratio)),
          },
        };
      });
    },
    [image.width, image.height],
  );

  const resetResize = useCallback(() => {
    setSideB((prev) => ({
      ...prev,
      resize: {
        ...prev.resize,
        width: image.width,
        height: image.height,
      },
    }));
  }, [image.width, image.height]);

  const openFile = useCallback(
    async (file: File | null | undefined) => {
      if (!file) return;
      if (!file.type.startsWith("image/")) {
        onNotice("That doesn't look like an image");
        return;
      }
      onReplace(await fileToImage(file));
    },
    [onNotice, onReplace],
  );

  const clampedZoom = Math.max(0.05, Math.min(16, zoom));
  const busy = outA.busy || outB.busy;

  const downloadNameFor = (codec: string, producedType: string) => {
    const id = codec === ORIGINAL_ID ? IDENTITY : codec;
    return fileNameFor(id, image.filename, producedType);
  };

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
          void openFile(e.dataTransfer?.files?.[0]);
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          className="visually-hidden"
          onChange={(e) => {
            void openFile(e.target.files?.[0]);
            e.target.value = "";
          }}
        />

        {/* ---- image viewer ---------------------------------------------- */}
        <div className="viewer">
          <div className={cn("viewer-overlay", altBackground && "alt")} />
          <div className={cn("viewer-canvas", smoothing ? "smooth" : "crisp")}>
            <CompareView
              leftSrc={image.url}
              rightSrc={image.url}
              leftAlt={`${image.filename}, original`}
              rightAlt={`${image.filename}, compressed`}
              split={split}
              onSplitChange={setSplit}
              zoom={clampedZoom}
              rotate={rotation}
              imageWidth={image.width}
              imageHeight={image.height}
            />
          </div>
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
                    setZoom(
                      Number(e.target.value.replace(/\D/g, "") || 100) / 100,
                    )
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
                title="Rotate"
                onClick={() => setRotation((r) => (r + 90) % 360)}
              >
                <RotateIcon />
              </button>
              <button
                className={cn("vc-btn", !smoothing && "is-active")}
                type="button"
                aria-label="Toggle smoothing"
                title="Toggle smoothing"
                aria-pressed={!smoothing}
                onClick={() => setSmoothing((v) => !v)}
              >
                <SmoothingIcon />
              </button>
              <button
                className={cn("vc-btn", altBackground && "is-active")}
                type="button"
                aria-label="Toggle background"
                title="Toggle background"
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
                      aria-label="Compress codec"
                      name="codec-left"
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
                size={formatBytes(outA.bytes || sourceBytes)}
                ratio={0}
                busy={outA.busy}
                downloadUrl={outA.url}
                downloadName={downloadNameFor(sideA.codec, outA.type)}
                onDownloaded={() =>
                  onNotice(`${downloadNameFor(sideA.codec, outA.type)} downloaded`)
                }
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
            onResizeToggle={(v) => {
              if (v) resetResize();
              setSideB((p) => ({ ...p, resizeEnabled: v }));
            }}
            resize={sideB.resize}
            onResizeEdge={setResizeEdge}
            paletteEnabled={sideB.paletteEnabled}
            onPaletteToggle={(v) =>
              setSideB((p) => ({ ...p, paletteEnabled: v }))
            }
            onCopyOver={() => setSideA({ ...sideB })}
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
                size={outputBytes ? formatBytes(outputBytes) : "…"}
                ratio={reduction}
                busy={outB.busy}
                downloadUrl={outB.url}
                downloadName={downloadNameFor(sideB.codec, outB.type)}
                onDownloaded={() =>
                  onNotice(`${downloadNameFor(sideB.codec, outB.type)} downloaded`)
                }
              />
            }
          />
        </div>

        {busy && !outB.url && !outA.url && (
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
