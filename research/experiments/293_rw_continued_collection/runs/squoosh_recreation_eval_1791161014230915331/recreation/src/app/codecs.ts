export type OptionKind = "range" | "select" | "toggle" | "text";

export type CodecOption = {
  key: string;
  label: string;
  kind?: OptionKind;
  /** Range bounds. */
  min?: number;
  max?: number;
  step?: number;
  /** Select choices. */
  choices?: string[];
  /** Advanced options live behind the collapsible section. */
  advanced?: boolean;
  /** Default value used when (re)selecting the codec. */
  value?: number | string | boolean;
  /** Label shown within an advanced section header. */
  suffix?: string;
};

export type Codec = {
  id: string;
  label: string;
  /** Chroma / quality unit hint. */
  unit?: string;
  options: CodecOption[];
  /** Browser-native encoders can't be inspected with the same settings. */
  qualityLabel?: string;
};

export const ORIGINAL_ID = "identity";

/** The encoder list, in the exact order the reference select presents them. */
export const CODECS: Codec[] = [
  {
    id: "avif",
    label: "AVIF",
    unit: "quality",
    options: [
      { key: "quality", label: "Quality:", kind: "range", min: 0, max: 100, step: 1, value: 50 },
      { key: "qualityAlpha", label: "Quality (alpha):", kind: "range", min: 0, max: 100, step: 1, value: 100, advanced: true },
      { key: "denoise", label: "Denoise:", kind: "range", min: 0, max: 100, step: 1, value: 0, advanced: true },
      { key: "speed", label: "Speed:", kind: "range", min: 0, max: 10, step: 1, value: 6, advanced: true, suffix: "0=slow, 10=fast" },
      { key: "subsample", label: "Subsample chroma:", kind: "toggle", value: true, advanced: true },
    ],
  },
  {
    id: "browserJPEG",
    label: "Browser JPEG",
    unit: "quality",
    options: [
      { key: "quality", label: "Quality:", kind: "range", min: 0, max: 100, step: 1, value: 75 },
    ],
  },
  {
    id: "browserPNG",
    label: "Browser PNG",
    options: [],
  },
  {
    id: "jxl",
    label: "JPEG XL (beta)",
    options: [
      { key: "quality", label: "Quality:", kind: "range", min: 0, max: 100, step: 1, value: 75 },
      { key: "effort", label: "Effort:", kind: "range", min: 1, max: 9, step: 1, value: 7, advanced: true },
      { key: "epf", label: "Edge preserving filter:", kind: "range", min: -1, max: 3, step: 1, value: -1, advanced: true },
      { key: "lossless", label: "Lossless:", kind: "toggle", value: false, advanced: true },
    ],
  },
  {
    id: "mozJPEG",
    label: "MozJPEG",
    unit: "quality",
    options: [
      { key: "quality", label: "Quality:", kind: "range", min: 0, max: 100, step: 1, value: 75 },
      { key: "progressive", label: "Progressive:", kind: "toggle", value: true, advanced: true },
      { key: "baseline", label: "Baseline:", kind: "toggle", value: false, advanced: true },
      { key: "chromaSubsample", label: "Chroma subsample:", kind: "select", choices: ["4:4:4", "4:2:2", "4:2:0"], value: "4:2:0", advanced: true },
      { key: "trellis", label: "Trellis quantization:", kind: "toggle", value: true, advanced: true },
      { key: "autoSubsample", label: "Auto subsample:", kind: "toggle", value: true, advanced: true },
      { key: "trellisMultipass", label: "Trellis multipass:", kind: "toggle", value: true, advanced: true },
      { key: "quantTable", label: "Quantization table:", kind: "range", min: 0, max: 8, step: 1, value: 3, advanced: true },
    ],
  },
  {
    id: "oxiPNG",
    label: "OxiPNG",
    options: [
      { key: "level", label: "Level:", kind: "range", min: 1, max: 6, step: 1, value: 2 },
      { key: "interlace", label: "Interlace:", kind: "toggle", value: false, advanced: true },
      { key: "reducePalette", label: "Reduce palette:", kind: "toggle", value: false, advanced: true },
      { key: "paletteColours", label: "Palette colours:", kind: "range", min: 2, max: 256, step: 1, value: 256, advanced: true },
    ],
  },
  {
    id: "qoi",
    label: "QOI",
    options: [],
  },
  {
    id: "webP",
    label: "WebP",
    unit: "quality",
    options: [
      { key: "quality", label: "Quality:", kind: "range", min: 0, max: 100, step: 1, value: 75 },
      { key: "method", label: "Method:", kind: "range", min: 0, max: 6, step: 1, value: 4, advanced: true },
      { key: "lossless", label: "Lossless:", kind: "toggle", value: false, advanced: true },
      { key: "alphaQuality", label: "Alpha quality:", kind: "range", min: 0, max: 100, step: 1, value: 100, advanced: true },
    ],
  },
  {
    id: "wp2",
    label: "WebP v2 (unstable)",
    options: [
      { key: "quality", label: "Quality:", kind: "range", min: 0, max: 100, step: 1, value: 75 },
      { key: "effort", label: "Effort:", kind: "range", min: 0, max: 9, step: 1, value: 5, advanced: true },
      { key: "lossless", label: "Lossless:", kind: "toggle", value: false, advanced: true },
    ],
  },
];

export function codecById(id: string): Codec | undefined {
  return CODECS.find((c) => c.id === id);
}

/** Short label shown on the post-compress results bubble. */
export function codecBadge(id: string): string {
  if (id === ORIGINAL_ID) return "Original";
  const found = codecById(id);
  return found ? found.label : id;
}

/** Default option values for a codec, keyed by option key. */
export function defaultValues(codec: Codec): Record<string, number | string | boolean> {
  const out: Record<string, number | string | boolean> = {};
  for (const opt of codec.options) {
    if (opt.value !== undefined) out[opt.key] = opt.value;
  }
  return out;
}
