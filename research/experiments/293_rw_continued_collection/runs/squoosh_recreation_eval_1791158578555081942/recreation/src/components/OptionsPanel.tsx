import { useState, type ReactNode } from "react";
import {
  CaretIcon,
  CopyOverIcon,
  ImportSideIcon,
  SaveSideIcon,
} from "@/components/icons";
import { Toggle } from "@/components/Toggle";
import { CODECS, ORIGINAL_ID, type CodecOption } from "@/app/codecs";
import type { LoadedImage } from "@/app/demos";
import { cn } from "@/utils/cn";

export type OptionValue = number | string | boolean;

type Props = {
  side: "a" | "b";
  image: LoadedImage;
  /** Selected codec id, or "original". */
  codec: string;
  onCodecChange: (id: string) => void;
  /** Current option values for the selected codec. */
  values: Record<string, OptionValue>;
  onValueChange: (key: string, value: OptionValue) => void;
  resizeEnabled: boolean;
  onResizeToggle: (next: boolean) => void;
  resize: {
    width: number;
    height: number;
    method: string;
  };
  /** Edits one edge; the other follows the source aspect ratio. */
  onResizeEdge: (edge: "width" | "height", value: number) => void;
  paletteEnabled: boolean;
  onPaletteToggle: (next: boolean) => void;
  /** Copies this side's settings onto the other side. */
  onCopyOver?: () => void;
  /** Pushes settings into the saved slot (side A only). */
  onSave?: () => void;
  onImport?: () => void;
  canImport: boolean;
  /** Results bubble rendered beneath the compress section. */
  results?: ReactNode;
};

const RESIZE_METHODS = [
  "Triangle",
  "Catrom",
  "Mitchell",
  "Lanczos3",
  "Hqx",
  "Magic Kernel Sharp",
];

export function OptionsPanel(props: Props) {
  const {
    side,
    codec,
    onCodecChange,
    values,
    onValueChange,
    resizeEnabled,
    onResizeToggle,
    resize,
    onResizeEdge,
    paletteEnabled,
    onPaletteToggle,
  } = props;

  const codecDef = CODECS.find((c) => c.id === codec);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  // The resampling filter is presentational; the browser does the scaling.
  const [method, setMethod] = useState(resize.method);

  const basic = (codecDef?.options ?? []).filter((o) => !o.advanced);
  const advanced = (codecDef?.options ?? []).filter((o) => o.advanced);

  // Both sides always expose the full codec list; the original is not a codec.
  const selectable = CODECS;

  return (
    <div className={cn("opts-panel", side === "a" ? "side-a" : "side-b")}>
      <div className="opts-stack">
        {/* ---- Edit ------------------------------------------------------- */}
        <div className="opts-scroller">
          <h3 className="panel-title">
            Edit
            <span className="title-actions">
              <button
                className="title-btn copy-over-btn"
                type="button"
                title="Copy settings to other side"
                aria-label="Copy settings to other side"
                onClick={props.onCopyOver}
              >
                <CopyOverIcon />
              </button>
              <button
                className="title-btn save-btn"
                type="button"
                title="Save side settings"
                aria-label="Save side settings"
                onClick={props.onSave}
              >
                <SaveSideIcon />
              </button>
              <button
                className="title-btn import-btn"
                type="button"
                title="Import saved side settings"
                aria-label="Import saved side settings"
                disabled={!props.canImport}
                onClick={props.onImport}
              >
                <ImportSideIcon />
              </button>
            </span>
          </h3>

          <label className="option-row option-toggle">
            <span>Resize</span>
            <Toggle
              label="Resize"
              checked={resizeEnabled}
              onChange={onResizeToggle}
            />
          </label>

          {resizeEnabled && (
            <div className="opt-section">
              <div className="option-row">
                <div className="sel-wrap">
                  <select
                    aria-label="Resize method"
                    name="resizeMethod"
                    value={method}
                    onChange={(e) => setMethod(e.target.value)}
                  >
                    {RESIZE_METHODS.map((m) => (
                      <option key={m}>{m}</option>
                    ))}
                  </select>
                  <CaretIcon className="sel-arrow" />
                </div>
              </div>
              <div className="option-one-cell">
                <label className="range-row" style={{ padding: "0 0 6px" }}>
                  <span className="range-label">Width</span>
                  <input
                    className="range-number"
                    type="number"
                    name="width"
                    aria-label="Width"
                    min={1}
                    value={resize.width}
                    onChange={(e) =>
                      onResizeEdge("width", Number(e.target.value))
                    }
                  />
                </label>
                <label className="range-row" style={{ padding: "0" }}>
                  <span className="range-label">Height</span>
                  <input
                    className="range-number"
                    type="number"
                    name="height"
                    aria-label="Height"
                    min={1}
                    value={resize.height}
                    onChange={(e) =>
                      onResizeEdge("height", Number(e.target.value))
                    }
                  />
                </label>
              </div>
            </div>
          )}

          <label className="option-row option-toggle">
            <span>Reduce palette</span>
            <Toggle
              label="Reduce palette"
              checked={paletteEnabled}
              onChange={onPaletteToggle}
            />
          </label>

          {paletteEnabled && (
            <div className="opt-section">
              <div className="option-row">
                <div className="sel-wrap">
                  <select aria-label="Palette dithering" defaultValue="Floyd–Steinberg">
                    <option>None</option>
                    <option>Floyd–Steinberg</option>
                  </select>
                  <CaretIcon className="sel-arrow" />
                </div>
              </div>
              <OptionField
                opt={{
                  key: "paletteColours",
                  label: "Colors:",
                  kind: "range",
                  min: 2,
                  max: 256,
                  step: 1,
                }}
                value={values.paletteColours ?? 256}
                onChange={onValueChange}
              />
            </div>
          )}
        </div>

        {/* ---- Compress --------------------------------------------------- */}
        <div className="opts-scroller">
          <h3 className="panel-title">Compress</h3>

          <div className="option-one-cell">
            <div className="sel-wrap">
              <select
                aria-label="Compress codec"
                value={codec}
                onChange={(e) => onCodecChange(e.target.value)}
              >
                <option value={ORIGINAL_ID}>
                  Original Image ({props.image.filename})
                </option>
                {selectable.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.label}
                  </option>
                ))}
              </select>
              <CaretIcon className="sel-arrow" />
            </div>
          </div>

          {codecDef && codecDef.options.length > 0 && (
            <div className="opt-section">
              {basic.map((opt) => (
                <OptionField
                  key={opt.key}
                  opt={opt}
                  value={values[opt.key] ?? opt.value ?? 0}
                  onChange={onValueChange}
                />
              ))}

              {advanced.length > 0 && (
                <div className={cn("expander", advancedOpen && "open")}>
                  <div
                    className="expander-head"
                    role="button"
                    tabIndex={0}
                    aria-expanded={advancedOpen}
                    onClick={() => setAdvancedOpen((v) => !v)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        setAdvancedOpen((v) => !v);
                      }
                    }}
                  >
                    <CaretIcon className="caret" />
                    <span>Advanced settings</span>
                  </div>
                  {advancedOpen && (
                    <div className="expander-body">
                      {advanced.map((opt) => (
                        <OptionField
                          key={opt.key}
                          opt={opt}
                          value={values[opt.key] ?? opt.value ?? 0}
                          onChange={onValueChange}
                        />
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* ---- results ---------------------------------------------------- */}
        {props.results}
      </div>
    </div>
  );
}

function OptionField({
  opt,
  value,
  onChange,
}: {
  opt: CodecOption;
  value: OptionValue;
  onChange: (key: string, value: OptionValue) => void;
}) {
  if (opt.kind === "toggle") {
    return (
      <label className="option-row option-toggle">
        <span>{opt.label}</span>
        <Toggle
          label={opt.label}
          checked={Boolean(value)}
          onChange={(v) => onChange(opt.key, v)}
        />
      </label>
    );
  }

  if (opt.kind === "select") {
    return (
      <div className="option-row" style={{ gridTemplateColumns: "1fr 1fr" }}>
        <span>{opt.label}</span>
        <div className="sel-wrap">
          <select
            aria-label={opt.label}
            value={String(value)}
            onChange={(e) => onChange(opt.key, e.target.value)}
          >
            {(opt.choices ?? []).map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
          <CaretIcon className="sel-arrow" />
        </div>
      </div>
    );
  }

  // Range (default).
  const min = opt.min ?? 0;
  const max = opt.max ?? 100;
  const num = typeof value === "number" ? value : Number(value) || 0;
  return (
    <div className="range-row">
      <span className="range-label">
        {opt.label}
        {opt.suffix ? ` (${opt.suffix})` : ""}
      </span>
      <input
        className="range-number"
        type="number"
        min={min}
        max={max}
        value={num}
        aria-label={opt.label}
        onChange={(e) => onChange(opt.key, Number(e.target.value))}
      />
      <div className="range-track-wrap">
        <input
          type="range"
          min={min}
          max={max}
          step={opt.step ?? 1}
          value={num}
          aria-label={`${opt.label} ${num}`}
          onChange={(e) => onChange(opt.key, Number(e.target.value))}
        />
      </div>
    </div>
  );
}
