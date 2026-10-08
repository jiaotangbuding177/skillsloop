import { useEffect, useMemo, useRef, useState } from "react";
import type { EditorApi } from "@/editor/useEditor";
import { cn } from "@/utils/cn";

const SWATCHES: string[] = [
  "#000000", "#333333", "#666666", "#999999", "#cccccc", "#ffffff", "#ff0000", "#ff7700", "#ffee00", "#00ff00",
  "#00ffcc", "#0099ff", "#0000ff", "#6600ff", "#ff00ff", "#ff0066", "#7a4b00", "#3b5323", "#0b5394", "#674ea7",
];

function hexToRgb(hex: string) {
  const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex.trim());
  if (!m) return { r: 0, g: 0, b: 0 };
  return { r: parseInt(m[1], 16), g: parseInt(m[2], 16), b: parseInt(m[3], 16) };
}
function rgbToHex(r: number, g: number, b: number) {
  const t = (n: number) => Math.max(0, Math.min(255, Math.round(n))).toString(16).padStart(2, "0");
  return `#${t(r)}${t(g)}${t(b)}`;
}
function hsvToRgb(h: number, s: number, v: number) {
  const c = v * s;
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = v - c;
  let r = 0, g = 0, b = 0;
  if (h < 60) [r, g, b] = [c, x, 0];
  else if (h < 120) [r, g, b] = [x, c, 0];
  else if (h < 180) [r, g, b] = [0, c, x];
  else if (h < 240) [r, g, b] = [0, x, c];
  else if (h < 300) [r, g, b] = [x, 0, c];
  else [r, g, b] = [c, 0, x];
  return { r: (r + m) * 255, g: (g + m) * 255, b: (b + m) * 255 };
}

type Tab = "picker" | "channels" | "swatches";

export function ColorPicker({ editor }: { editor: EditorApi }) {
  const [tab, setTab] = useState<Tab>("picker");
  const [hue, setHue] = useState(120);
  const [sat, setSat] = useState(1);
  const [val, setVal] = useState(0.5);
  const [hexText, setHexText] = useState(editor.color);

  const svRef = useRef<HTMLCanvasElement | null>(null);
  const hueRef = useRef<HTMLCanvasElement | null>(null);

  const rgb = useMemo(() => hexToRgb(editor.color), [editor.color]);

  /* push the color outward when the hue/sat/val change here */
  const commit = (h: number, s: number, v: number) => {
    const { r, g, b } = hsvToRgb(h, s, v);
    const hex = rgbToHex(r, g, b);
    setHexText(hex);
    editor.setColor(hex);
  };

  /* sync inbound color changes (picked, layer color, etc.) */
  useEffect(() => {
    const { r, g, b } = hexToRgb(editor.color);
    const max = Math.max(r, g, b) / 255;
    const min = Math.min(r, g, b) / 255;
    const d = max - min;
    let h = 0;
    if (d !== 0) {
      if (max === r / 255) h = (((g - b) / 255 / d) % 6) * 60;
      else if (max === g / 255) h = ((b - r) / 255 / d + 2) * 60;
      else h = ((r - g) / 255 / d + 4) * 60;
      if (h < 0) h += 360;
    }
    setHue(Math.round(h));
    setSat(max === 0 ? 0 : d / max);
    setVal(max);
    setHexText(editor.color);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editor.color]);

  /* paint saturation/value square */
  useEffect(() => {
    const c = svRef.current;
    if (!c) return;
    const ctx = c.getContext("2d")!;
    const w = c.width, h = c.height;
    const base = hsvToRgb(hue, 1, 1);
    const img = ctx.createImageData(w, h);
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const s = x / (w - 1);
        const v = 1 - y / (h - 1);
        const i = (y * w + x) * 4;
        img.data[i] = base.r * s * v + 255 * (1 - s) * v + 0;
        img.data[i] = Math.min(255, base.r * v * s + 255 * (1 - s) * v);
        img.data[i + 1] = Math.min(255, base.g * v * s + 255 * (1 - s) * v);
        img.data[i + 2] = Math.min(255, base.b * v * s + 255 * (1 - s) * v);
        img.data[i + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
  }, [hue]);

  /* paint hue strip */
  useEffect(() => {
    const c = hueRef.current;
    if (!c) return;
    const ctx = c.getContext("2d")!;
    const w = c.width, h = c.height;
    for (let y = 0; y < h; y++) {
      const { r, g, b } = hsvToRgb((y / (h - 1)) * 360, 1, 1);
      ctx.fillStyle = `rgb(${r},${g},${b})`;
      ctx.fillRect(0, y, w, 1);
    }
  }, []);

  const svDrag = useRef(false);
  const hueDrag = useRef(false);

  const pickSV = (e: React.PointerEvent, el: HTMLElement) => {
    const r = el.getBoundingClientRect();
    const s = Math.max(0, Math.min(1, (e.clientX - r.left) / r.width));
    const v = 1 - Math.max(0, Math.min(1, (e.clientY - r.top) / r.height));
    setSat(s);
    setVal(v);
    commit(hue, s, v);
  };
  const pickHue = (e: React.PointerEvent, el: HTMLElement) => {
    const r = el.getBoundingClientRect();
    const h = Math.max(0, Math.min(360, ((e.clientY - r.top) / r.height) * 360));
    setHue(h);
    commit(h, sat, val);
  };

  const chan = (label: string, value: number, onChange: (v: number) => void) => (
    <div className="mp-channel-row" key={label}>
      <label>{label}</label>
      <input
        type="text"
        value={Math.round(value)}
        onChange={(e) => {
          const v = parseInt(e.target.value, 10);
          if (!Number.isNaN(v)) onChange(v);
        }}
      />
      <input
        type="range"
        min={0}
        max={label === "H" ? 360 : 255}
        value={Math.round(value)}
        aria-label={label}
        onChange={(e) => onChange(parseInt(e.target.value, 10))}
      />
    </div>
  );

  return (
    <div>
      <div className="mp-color-head">
        <span className="mp-color-preview" style={{ background: editor.color }} aria-label="Current Color Preview" />
        <div className="mp-color-tabs" role="group">
          <button
            type="button"
            className="mp-color-tab"
            aria-pressed={tab === "picker"}
            aria-label="Toggle Color Picker"
            title="Toggle Color Picker"
            onClick={() => setTab("picker")}
          >
            <PatternIcon />
          </button>
          <button
            type="button"
            className="mp-color-tab"
            aria-pressed={tab === "channels"}
            aria-label="Toggle Color Channels"
            title="Toggle Color Channels"
            onClick={() => setTab("channels")}
          >
            <ChannelsIcon />
          </button>
          <button
            type="button"
            className="mp-color-tab"
            aria-pressed={tab === "swatches"}
            aria-label="Toggle Swatches"
            title="Toggle Swatches"
            onClick={() => setTab("swatches")}
          >
            <GridIcon />
          </button>
        </div>
      </div>

      {tab === "picker" && (
        <>
          <div className="mp-color-main" aria-label="Color Selection">
            <div
              className="mp-sv"
              onPointerDown={(e) => {
                svDrag.current = true;
                (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
                pickSV(e, e.currentTarget as HTMLElement);
              }}
              onPointerMove={(e) => svDrag.current && pickSV(e, e.currentTarget as HTMLElement)}
              onPointerUp={() => (svDrag.current = false)}
            >
              <canvas ref={svRef} width={150} height={110} />
              <span className="mp-sv-cursor" style={{ left: `${sat * 100}%`, top: `${(1 - val) * 100}%` }} />
            </div>
            <div
              className="mp-hue"
              onPointerDown={(e) => {
                hueDrag.current = true;
                (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
                pickHue(e, e.currentTarget as HTMLElement);
              }}
              onPointerMove={(e) => hueDrag.current && pickHue(e, e.currentTarget as HTMLElement)}
              onPointerUp={() => (hueDrag.current = false)}
            >
              <canvas ref={hueRef} width={22} height={110} />
              <span className="mp-hue-cursor" style={{ top: `${(hue / 360) * 100}%`, left: "50%" }} />
            </div>
          </div>
          <div className="mp-hex-row">
            <span id="hex-label">Hex</span>
            <input
              type="text"
              aria-label="Hex"
              value={hexText}
              onChange={(e) => {
                const v = e.target.value;
                setHexText(v);
                if (/^#?([a-f\d]{3}|[a-f\d]{6})$/i.test(v.trim())) {
                  editor.setColor(v.startsWith("#") ? v : `#${v}`);
                }
              }}
              onBlur={() => setHexText(editor.color)}
            />
          </div>
        </>
      )}

      {tab === "channels" && (
        <div className="mp-channels">
          {chan("H", hue, (v) => {
            setHue(v);
            commit(v, sat, val);
          })}
          {chan("R", rgb.r, (v) => editor.setColor(rgbToHex(v, rgb.g, rgb.b)))}
          {chan("G", rgb.g, (v) => editor.setColor(rgbToHex(rgb.r, v, rgb.b)))}
          {chan("B", rgb.b, (v) => editor.setColor(rgbToHex(rgb.r, rgb.g, v)))}
        </div>
      )}

      {tab === "swatches" && (
        <div className="mp-swatches">
          {SWATCHES.map((c) => (
            <button
              key={c}
              type="button"
              className="mp-swatch"
              style={{ background: c }}
              aria-label={c}
              title={c}
              onClick={() => editor.setColor(c)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function PatternIcon() {
  return (
    <svg width={16} height={14} viewBox="0 0 16 14" fill="none" stroke="currentColor" strokeWidth={2}>
      <circle cx="8" cy="7" r="5" />
      <path d="M8 2v10" />
    </svg>
  );
}
function ChannelsIcon() {
  return (
    <svg width={16} height={14} viewBox="0 0 16 14" fill="none" stroke="currentColor" strokeWidth={1.6}>
      <rect x="1" y="1" width="14" height="12" rx="1" />
      <path d="M5.5 1v12M10.5 1v12" />
    </svg>
  );
}
function GridIcon() {
  return (
    <svg width={16} height={14} viewBox="0 0 16 14" fill="none" stroke="currentColor" strokeWidth={1.6}>
      <rect x="1" y="1" width="14" height="12" rx="1" />
      <path d="M1 5h14M1 9h14M6 1v12M11 1v12" />
    </svg>
  );
}
