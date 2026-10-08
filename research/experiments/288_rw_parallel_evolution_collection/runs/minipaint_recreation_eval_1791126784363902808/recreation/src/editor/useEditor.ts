import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { DialogState, FieldDef, Layer, Point, Rect, ToolId } from "./types";
import { RESOLUTIONS } from "./data";
import { buildProject, stringifyProject } from "./project";

interface LayerRuntime extends Omit<Layer, "data"> {
  canvas: HTMLCanvasElement;
}

interface Snapshot {
  layers: { id: number; name: string; visible: boolean; opacity: number; x: number; y: number; pixels: ImageData }[];
  activeId: number;
  width: number;
  height: number;
}

let layerSeq = 1;

function makeCanvas(w: number, h: number): HTMLCanvasElement {
  const c = document.createElement("canvas");
  c.width = Math.max(1, Math.round(w));
  c.height = Math.max(1, Math.round(h));
  return c;
}

function hexToRgb(hex: string) {
  const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex.trim());
  if (!m) return { r: 0, g: 0, b: 0 };
  return { r: parseInt(m[1], 16), g: parseInt(m[2], 16), b: parseInt(m[3], 16) };
}

function rgbToHex(r: number, g: number, b: number) {
  const t = (n: number) => Math.max(0, Math.min(255, Math.round(n))).toString(16).padStart(2, "0");
  return `#${t(r)}${t(g)}${t(b)}`;
}

/** HSV (h 0..360, s/v 0..1) -> rgb */
function hsvToRgb(h: number, s: number, v: number) {
  const c = v * s;
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = v - c;
  let r = 0,
    g = 0,
    b = 0;
  if (h < 60) [r, g, b] = [c, x, 0];
  else if (h < 120) [r, g, b] = [x, c, 0];
  else if (h < 180) [r, g, b] = [0, c, x];
  else if (h < 240) [r, g, b] = [0, x, c];
  else if (h < 300) [r, g, b] = [x, 0, c];
  else [r, g, b] = [c, 0, x];
  return { r: (r + m) * 255, g: (g + m) * 255, b: (b + m) * 255 };
}

/** Trigger a browser download for a URL without leaving a stray anchor behind. */
function triggerDownload(url: string, filename: string) {
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.style.display = "none";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

/* Standard document sizes, largest first. A new document starts at the biggest
   one that still fits the visible canvas area, otherwise a matching custom size
   (leaving a small margin for the surrounding chrome). */
const SIZE_PRESETS: [number, number][] = [
  [3840, 2160],
  [1920, 1080],
  [1600, 1200],
  [1280, 720],
  [1024, 768],
  [800, 600],
  [640, 480],
];

export function pickInitialSize(availW: number, availH: number): { w: number; h: number } {
  for (const [w, h] of SIZE_PRESETS) {
    if (w <= availW && h <= availH) return { w, h };
  }
  /* nothing standard fits: fill the area, leaving a small margin */
  const w = Math.max(1, Math.round(availW - 15));
  const h = Math.max(1, Math.round(availH - 10));
  return { w, h };
}

function rgbToHsv(r: number, g: number, b: number) {
  r /= 255;
  g /= 255;
  b /= 255;
  const max = Math.max(r, g, b),
    min = Math.min(r, g, b);
  const d = max - min;
  let h = 0;
  if (d !== 0) {
    if (max === r) h = ((g - b) / d) % 6;
    else if (max === g) h = (b - r) / d + 2;
    else h = (r - g) / d + 4;
    h *= 60;
    if (h < 0) h += 360;
  }
  const s = max === 0 ? 0 : d / max;
  return { h, s, v: max };
}

export function useEditor() {
  const [width, setWidth] = useState(462);
  const [height, setHeight] = useState(347);
  const [layerMeta, setLayerMeta] = useState<Layer[]>([]);
  const [activeLayerId, setActiveLayerId] = useState(1);
  const [tool, setTool] = useState<ToolId>("brush");
  const [shapeTool, setShapeTool] = useState("rectangle");
  const [color, setColor] = useState("#008000");
  const [zoom, setZoom] = useState(100);
  const [mouse, setMouse] = useState<Point | null>(null);
  const [grid, setGrid] = useState(false);
  const [ruler, setRuler] = useState(false);
  const [guides, setGuides] = useState<{ id: number; type: "vertical" | "horizontal"; position: number }[]>([]);
  const [fullscreen, setFullscreen] = useState(false);
  const [resolution, setResolution] = useState("72");
  const [dialog, setDialog] = useState<DialogState | null>(null);
  const [status, setStatus] = useState("");
  const [selection, setSelection] = useState<Rect | null>(null);

  /** per-tool attribute values (stroke, power, radius, alpha, delay, ...) */
  const [attrs, setAttrs] = useState<Record<string, number | string | boolean>>({
    auto_select: true,
    global: false,
    size: 4,
    pressure: false,
    circle: true,
    strict: true,
    power: 50,
    anti_aliasing: true,
    contiguous: false,
    color_1: "#000000",
    color_2: "#ffffff",
    alpha: 100,
    radial: false,
    radial_power: 50,
    radius: 100,
    bulge: true,
    strength: 50,
    source_layer: "Current",
    delay: 200,
    play: false,
    stroke_size: 1,
    kerning: 0,
    leading: 0,
    font: "Arial",
    stroke: "#000000",
    fill: "#008000",
  });
  const setAttr = useCallback(
    (key: string, value: number | string | boolean) => setAttrs((s) => ({ ...s, [key]: value })),
    []
  );
  const brushSize = Number(attrs.size) || 1;
  const pressure = Boolean(attrs.pressure);
  const setBrushSize = useCallback((v: number) => setAttr("size", v), [setAttr]);
  const setPressure = useCallback((v: boolean) => setAttr("pressure", v), [setAttr]);

  /** shapes picker popup (opened by the shape tool) */
  const [shapesOpen, setShapesOpen] = useState(false);
  const [shapesDraft, setShapesDraft] = useState("rectangle");

  const [, forceRender] = useState(0);

  const reRender = useCallback(() => forceRender((n) => n + 1), []);

  const layerRefs = useRef<Map<number, LayerRuntime>>(new Map());
  const displayRef = useRef<HTMLCanvasElement | null>(null);
  const history = useRef<Snapshot[]>([]);
  const future = useRef<Snapshot[]>([]);
  const clipRef = useRef<HTMLCanvasElement | null>(null);

  /* ---- layer creation ---- */
  const initLayers = useCallback((w: number, h: number, fill = "#ffffff") => {
    layerRefs.current.clear();
    const id = layerSeq++;
    const rt: LayerRuntime = { id, name: "Brush #1", visible: true, opacity: 100, x: 0, y: 0, canvas: makeCanvas(w, h) };
    const ctx = rt.canvas.getContext("2d", { willReadFrequently: true })!;
    ctx.fillStyle = fill;
    ctx.fillRect(0, 0, w, h);
    layerRefs.current.set(id, rt);
    setActiveLayerId(id);
    return id;
  }, []);

  useEffect(() => {
    /* measure the actual canvas area so the starting document matches what the
       workspace can display */
    const area = document.querySelector(".mp-canvas-area");
    const rect = area?.getBoundingClientRect();
    const availW = rect && rect.width > 0 ? rect.width : window.innerWidth - 250;
    const availH = rect && rect.height > 0 ? rect.height : window.innerHeight - 112;
    const { w, h } = pickInitialSize(availW, availH);
    setWidth(w);
    setHeight(h);
    initLayers(w, h);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const W = width;
  const H = height;

  /** offscreen buffer the full document is composited into at native resolution */
  const renderBuffer = useRef<HTMLCanvasElement | null>(null);

  /* ---- composite ---- */
  /* The document is composited at its native size into an offscreen buffer, then
     blitted into the (zoom-scaled) display canvas. Zoom changes the display
     backing store, never the document dimensions. */
  const composite = useCallback(() => {
    const disp = displayRef.current;
    if (!disp) return;
    if (!renderBuffer.current) renderBuffer.current = makeCanvas(W, H);
    const buf = renderBuffer.current;
    if (buf.width !== W || buf.height !== H) {
      buf.width = W;
      buf.height = H;
    }
    const bctx = buf.getContext("2d", { willReadFrequently: true })!;
    bctx.clearRect(0, 0, W, H);
    for (const [, rt] of layerRefs.current) {
      if (!rt.visible) continue;
      bctx.globalAlpha = Math.max(0, Math.min(1, rt.opacity / 100));
      bctx.drawImage(rt.canvas, rt.x, rt.y);
    }
    bctx.globalAlpha = 1;

    const ctx = disp.getContext("2d", { willReadFrequently: true })!;
    ctx.clearRect(0, 0, disp.width, disp.height);
    ctx.save();
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(buf, 0, 0, disp.width, disp.height);
    ctx.restore();
  }, [W, H]);

  /** keep the display backing store in sync with the current zoom level */
  const resizeDisplay = useCallback(
    (docW: number, docH: number, z: number) => {
      const disp = displayRef.current;
      if (!disp) return;
      const w = Math.max(1, Math.round(docW * z));
      const h = Math.max(1, Math.round(docH * z));
      if (disp.width !== w || disp.height !== h) {
        disp.width = w;
        disp.height = h;
      }
    },
    []
  );

  /* re-raster the display layer whenever zoom or document size changes */
  useEffect(() => {
    resizeDisplay(W, H, zoom / 100);
    composite();
  }, [W, H, zoom, resizeDisplay, composite]);

  /* ---- snapshots / history ---- */
  const snapshot = useCallback((): Snapshot => {
    const layers = [...layerRefs.current.values()].map((rt) => ({
      id: rt.id,
      name: rt.name,
      visible: rt.visible,
      opacity: rt.opacity,
      x: rt.x,
      y: rt.y,
      pixels: (() => {
        const c = rt.canvas.getContext("2d", { willReadFrequently: true })!;
        return c.getImageData(0, 0, rt.canvas.width, rt.canvas.height);
      })(),
    }));
    return { layers, activeId: activeLayerId, width: W, height: H };
  }, [activeLayerId, W, H]);

  const pushHistory = useCallback(() => {
    history.current.push(snapshot());
    if (history.current.length > 40) history.current.shift();
    future.current = [];
  }, [snapshot]);

  const restore = useCallback((s: Snapshot) => {
    layerRefs.current.clear();
    for (const l of s.layers) {
      const c = makeCanvas(s.width, s.height);
      c.getContext("2d", { willReadFrequently: true })!.putImageData(l.pixels, 0, 0);
      layerRefs.current.set(l.id, {
        id: l.id,
        name: l.name,
        visible: l.visible,
        opacity: l.opacity,
        x: l.x,
        y: l.y,
        canvas: c,
      });
    }
    setWidth(s.width);
    setHeight(s.height);
    setActiveLayerId(s.activeId);
    reRender();
    requestAnimationFrame(() => composite());
  }, [composite, reRender]);

  const undo = useCallback(() => {
    const prev = history.current.pop();
    if (!prev) return setStatus("Nothing to undo");
    future.current.push(snapshot());
    restore(prev);
    setStatus("Undo");
  }, [restore, snapshot]);

  const redo = useCallback(() => {
    const next = future.current.pop();
    if (!next) return setStatus("Nothing to redo");
    history.current.push(snapshot());
    restore(next);
    setStatus("Redo");
  }, [restore, snapshot]);

  /* keep meta list in sync with runtime map */
  const syncMeta = useCallback(() => {
    setLayerMeta(
      [...layerRefs.current.values()].map((rt) => ({
        id: rt.id,
        name: rt.name,
        visible: rt.visible,
        opacity: rt.opacity,
        x: rt.x,
        y: rt.y,
        data: "",
      }))
    );
    reRender();
    composite();
  }, [composite, reRender]);

  useEffect(() => {
    syncMeta();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const active = useCallback((): LayerRuntime | null => {
    return layerRefs.current.get(activeLayerId) ?? [...layerRefs.current.values()].pop() ?? null;
  }, [activeLayerId]);

  /* ---- coordinate mapping ---- */
  /* The display canvas backing store is doc size x scale, and its CSS box is the
     same size, so image coords = (client - rect.left) / scale. */
  const toImageCoords = useCallback(
    (clientX: number, clientY: number): Point | null => {
      const disp = displayRef.current;
      if (!disp) return null;
      const r = disp.getBoundingClientRect();
      const scale = disp.width / Math.max(1, W);
      const sx = r.width > 0 ? r.width / Math.max(1, disp.width) : 1;
      return { x: ((clientX - r.left) * sx) / scale, y: ((clientY - r.top) * sx) / scale };
    },
    [W]
  );

  /* ---- effects on pixel data ---- */
  const applyToActive = useCallback(
    (fn: (d: ImageData) => void, label: string) => {
      const rt = active();
      if (!rt) return;
      pushHistory();
      const ctx = rt.canvas.getContext("2d", { willReadFrequently: true })!;
      const img = ctx.getImageData(0, 0, rt.canvas.width, rt.canvas.height);
      fn(img);
      ctx.putImageData(img, 0, 0);
      setStatus(label);
      syncMeta();
    },
    [active, pushHistory, syncMeta]
  );

  const eachPixel = (d: ImageData, fn: (r: number, g: number, b: number, a: number) => [number, number, number, number]) => {
    const p = d.data;
    for (let i = 0; i < p.length; i += 4) {
      const [r, g, b, a] = fn(p[i], p[i + 1], p[i + 2], p[i + 3]);
      p[i] = r;
      p[i + 1] = g;
      p[i + 2] = b;
      p[i + 3] = a;
    }
  };

  const effects: Record<string, (label: string) => void> = useMemo(
    () => ({
      grayscale: (l) => applyToActive((d) => eachPixel(d, (r, g, b, a) => { const v = 0.299 * r + 0.587 * g + 0.114 * b; return [v, v, v, a]; }), l),
      invert: (l) => applyToActive((d) => eachPixel(d, (r, g, b, a) => [255 - r, 255 - g, 255 - b, a]), l),
      sepia: (l) =>
        applyToActive(
          (d) =>
            eachPixel(d, (r, g, b, a) => [
              Math.min(255, 0.393 * r + 0.769 * g + 0.189 * b),
              Math.min(255, 0.349 * r + 0.686 * g + 0.168 * b),
              Math.min(255, 0.272 * r + 0.534 * g + 0.131 * b),
              a,
            ]),
          l
        ),
      brightness: (l) => applyToActive((d) => eachPixel(d, (r, g, b, a) => [r + 20, g + 20, b + 20, a]), l),
      contrast: (l) =>
        applyToActive((d) => eachPixel(d, (r, g, b, a) => { const f = 1.3; return [f * (r - 128) + 128, f * (g - 128) + 128, f * (b - 128) + 128, a]; }), l),
      saturation: (l) =>
        applyToActive((d) => eachPixel(d, (r, g, b, a) => { const v = 0.299 * r + 0.587 * g + 0.114 * b; const f = 1.4; return [v + f * (r - v), v + f * (g - v), v + f * (b - v), a]; }), l),
      noise: (l) =>
        applyToActive((d) => eachPixel(d, (r, g, b, a) => { const n = (Math.random() - 0.5) * 60; return [r + n, g + n, b + n, a]; }), l),
      pixelate: (l) =>
        applyToActive((d) => {
          const s = 8;
          const { width: w, height: h, data: p } = d;
          for (let y = 0; y < h; y += s)
            for (let x = 0; x < w; x += s) {
              let r = 0, g = 0, b = 0, a = 0, n = 0;
              for (let yy = y; yy < Math.min(y + s, h); yy++)
                for (let xx = x; xx < Math.min(x + s, w); xx++) {
                  const i = (yy * w + xx) * 4;
                  r += p[i]; g += p[i + 1]; b += p[i + 2]; a += p[i + 3]; n++;
                }
              r /= n; g /= n; b /= n; a /= n;
              for (let yy = y; yy < Math.min(y + s, h); yy++)
                for (let xx = x; xx < Math.min(x + s, w); xx++) {
                  const i = (yy * w + xx) * 4;
                  p[i] = r; p[i + 1] = g; p[i + 2] = b; p[i + 3] = a;
                }
            }
        }, l),
      emboss: (l) =>
        applyToActive((d) => {
          const { width: w, height: h, data: p } = d;
          const copy = new Uint8ClampedArray(p);
          const k = [-2, -1, 0, -1, 1, 1, 0, 1, 2];
          for (let y = 1; y < h - 1; y++)
            for (let x = 1; x < w - 1; x++) {
              let r = 0, g = 0, b = 0;
              let n = 0;
              for (let dy = -1; dy <= 1; dy++)
                for (let dx = -1; dx <= 1; dx++) {
                  const i = ((y + dy) * w + (x + dx)) * 4;
                  const kk = k[n++];
                  r += copy[i] * kk; g += copy[i + 1] * kk; b += copy[i + 2] * kk;
                }
              const i = (y * w + x) * 4;
              p[i] = r + 128; p[i + 1] = g + 128; p[i + 2] = b + 128;
            }
        }, l),
      blueprint: (l) =>
        applyToActive((d) => eachPixel(d, (r, g, b, a) => { const v = 0.299 * r + 0.587 * g + 0.114 * b; return [v * 0.2, v * 0.4, 255 - v * 0.2, a]; }), l),
      nightvision: (l) =>
        applyToActive((d) => eachPixel(d, (r, g, b, a) => { const v = 0.299 * r + 0.587 * g + 0.114 * b; return [v * 0.1, Math.min(255, v * 1.4) , v * 0.1, a]; }), l),
      heatmap: (l) =>
        applyToActive((d) => eachPixel(d, (r, g, b, a) => { const v = (0.299 * r + 0.587 * g + 0.114 * b) / 255; return [Math.min(255, v * 510), Math.min(255, v * 510 - 255), Math.max(0, 255 - v * 510), a]; }), l),
      solarize: (l) => applyToActive((d) => eachPixel(d, (r, g, b, a) => [r > 128 ? 255 - r : r, g > 128 ? 255 - g : g, b > 128 ? 255 - b : b, a]), l),
      edge: (l) =>
        applyToActive((d) => {
          const { width: w, height: h, data: p } = d;
          const copy = new Uint8ClampedArray(p);
          for (let y = 1; y < h - 1; y++)
            for (let x = 1; x < w - 1; x++) {
              const i = (y * w + x) * 4;
              const gx = -copy[i - 4] + copy[i + 4];
              const gy = -copy[i - w * 4] + copy[i + w * 4];
              const m = Math.min(255, Math.hypot(gx, gy));
              p[i] = m; p[i + 1] = m; p[i + 2] = m;
            }
        }, l),
    }),
    [applyToActive]
  );

  /* ---- drawing primitives ---- */
  /* `k` scales stroke widths so they look identical in document space whether we
     are drawing into a native-res layer (k=1) or a zoomed preview (k=zoom). */
  const drawShape = useCallback(
    (ctx: CanvasRenderingContext2D, from: Point, to: Point, shape: string, dashed = false, k = 1) => {
      const x1 = from.x, y1 = from.y, x2 = to.x, y2 = to.y;
      ctx.save();
      ctx.strokeStyle = color;
      ctx.fillStyle = color;
      ctx.lineWidth = Math.max(1, brushSize * k);
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      if (dashed) ctx.setLineDash([5 * k, 4 * k]);
      const w = x2 - x1, h = y2 - y1;
      ctx.beginPath();
      switch (shape) {
        case "line":
          ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
          break;
        case "arrow": {
          ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
          const ang = Math.atan2(y2 - y1, x2 - x1);
          const hl = (12 + brushSize) * k;
          ctx.beginPath();
          ctx.moveTo(x2, y2);
          ctx.lineTo(x2 - hl * Math.cos(ang - 0.4), y2 - hl * Math.sin(ang - 0.4));
          ctx.lineTo(x2 - hl * Math.cos(ang + 0.4), y2 - hl * Math.sin(ang + 0.4));
          ctx.closePath(); ctx.fill();
          break;
        }
        case "rectangle":
          ctx.rect(x1, y1, w, h); ctx.stroke();
          break;
        case "ellipse":
          ctx.ellipse((x1 + x2) / 2, (y1 + y2) / 2, Math.abs(w / 2), Math.abs(h / 2), 0, 0, Math.PI * 2); ctx.stroke();
          break;
        case "triangle":
          ctx.moveTo((x1 + x2) / 2, y1); ctx.lineTo(x2, y2); ctx.lineTo(x1, y2); ctx.closePath(); ctx.stroke();
          break;
        case "right_triangle":
          ctx.moveTo(x1, y1); ctx.lineTo(x1, y2); ctx.lineTo(x2, y2); ctx.closePath(); ctx.stroke();
          break;
        case "romb":
          ctx.moveTo((x1 + x2) / 2, y1); ctx.lineTo(x2, (y1 + y2) / 2); ctx.lineTo((x1 + x2) / 2, y2); ctx.lineTo(x1, (y1 + y2) / 2); ctx.closePath(); ctx.stroke();
          break;
        case "parallelogram":
          ctx.moveTo(x1 + Math.abs(w) * 0.25, y1); ctx.lineTo(x2, y1); ctx.lineTo(x2 - Math.abs(w) * 0.25, y2); ctx.lineTo(x1, y2); ctx.closePath(); ctx.stroke();
          break;
        case "trapezoid":
          ctx.moveTo(x1 + Math.abs(w) * 0.2, y1); ctx.lineTo(x2 - Math.abs(w) * 0.2, y1); ctx.lineTo(x2, y2); ctx.lineTo(x1, y2); ctx.closePath(); ctx.stroke();
          break;
        case "plus": {
          const t = Math.min(Math.abs(w), Math.abs(h)) / 3;
          ctx.moveTo(x1 + t, y1); ctx.lineTo(x2 - t, y1); ctx.lineTo(x2 - t, y2 - (Math.abs(h) - t) / 2);
          ctx.lineTo(x2, y2 - (Math.abs(h) - t) / 2); ctx.lineTo(x2, y2 + (Math.abs(h) - t) / 2);
          ctx.lineTo(x2 - t, y2 + (Math.abs(h) - t) / 2); ctx.lineTo(x2 - t, y2); ctx.lineTo(x1 + t, y2);
          ctx.lineTo(x1 + t, y2 + (Math.abs(h) - t) / 2); ctx.lineTo(x1, y2 + (Math.abs(h) - t) / 2);
          ctx.lineTo(x1, y2 - (Math.abs(h) - t) / 2); ctx.lineTo(x1 + t, y2 - (Math.abs(h) - t) / 2);
          ctx.closePath(); ctx.stroke();
          break;
        }
        case "pentagon":
        case "hexagon":
        case "polygon": {
          const sides = shape === "pentagon" ? 5 : shape === "hexagon" ? 6 : 6;
          const cx = (x1 + x2) / 2, cy = (y1 + y2) / 2;
          const rx = Math.abs(w / 2), ry = Math.abs(h / 2);
          for (let i = 0; i <= sides; i++) {
            const a = -Math.PI / 2 + (i * 2 * Math.PI) / sides;
            const px = cx + rx * Math.cos(a), py = cy + ry * Math.sin(a);
            if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
          }
          ctx.closePath(); ctx.stroke();
          break;
        }
        case "star": {
          const cx = (x1 + x2) / 2, cy = (y1 + y2) / 2;
          const R = Math.min(Math.abs(w), Math.abs(h)) / 2, r2 = R * 0.4;
          for (let i = 0; i < 10; i++) {
            const a = -Math.PI / 2 + (i * Math.PI) / 5;
            const rad = i % 2 === 0 ? R : r2;
            const px = cx + rad * Math.cos(a), py = cy + rad * Math.sin(a);
            if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
          }
          ctx.closePath(); ctx.stroke();
          break;
        }
        case "heart": {
          const cx = (x1 + x2) / 2, cy = (y1 + y2) / 2;
          const sx = Math.abs(w) / 2, sy = Math.abs(h) / 2;
          ctx.moveTo(cx, cy + sy * 0.8);
          ctx.bezierCurveTo(cx - sx * 1.4, cy - sy * 0.4, cx - sx * 0.5, cy - sy * 1.2, cx, cy - sy * 0.35);
          ctx.bezierCurveTo(cx + sx * 0.5, cy - sy * 1.2, cx + sx * 1.4, cy - sy * 0.4, cx, cy + sy * 0.8);
          ctx.closePath(); ctx.stroke();
          break;
        }
        case "cylinder": {
          const rx = Math.abs(w / 2), ry = Math.min(Math.abs(h) / 4, 20);
          ctx.ellipse((x1 + x2) / 2, y1 + ry, rx, ry, 0, 0, Math.PI * 2);
          ctx.moveTo(x1, y1 + ry); ctx.lineTo(x1, y2 - ry);
          ctx.moveTo(x2, y1 + ry); ctx.lineTo(x2, y2 - ry);
          ctx.moveTo(x1, y2 - ry);
          ctx.bezierCurveTo(x1, y2 - ry + ry, x2, y2 - ry + ry, x2, y2 - ry);
          ctx.stroke();
          break;
        }
        case "moon": {
          const cx = (x1 + x2) / 2, cy = (y1 + y2) / 2;
          ctx.arc(cx, cy, Math.abs(w / 2), 0, Math.PI * 2);
          ctx.stroke();
          ctx.beginPath();
          ctx.arc(cx + Math.abs(w) * 0.22, cy - Math.abs(h) * 0.08, Math.abs(w / 2) * 0.92, 0, Math.PI * 2);
          ctx.stroke();
          break;
        }
        case "callout":
          ctx.rect(x1, y1, w, h * 0.7);
          ctx.moveTo(x1 + Math.abs(w) * 0.2, y1 + h * 0.7);
          ctx.lineTo(x1 + Math.abs(w) * 0.2, y2);
          ctx.lineTo(x1 + Math.abs(w) * 0.45, y1 + h * 0.7);
          ctx.stroke();
          break;
        case "human": {
          const cx = (x1 + x2) / 2;
          const top = Math.min(y1, y2);
          ctx.arc(cx, top + Math.abs(h) * 0.12, Math.abs(h) * 0.12, 0, Math.PI * 2); ctx.stroke();
          ctx.beginPath();
          ctx.moveTo(cx, top + Math.abs(h) * 0.24); ctx.lineTo(cx, top + Math.abs(h) * 0.62);
          ctx.moveTo(cx - Math.abs(w) * 0.25, top + Math.abs(h) * 0.38); ctx.lineTo(cx + Math.abs(w) * 0.25, top + Math.abs(h) * 0.38);
          ctx.moveTo(cx, top + Math.abs(h) * 0.62); ctx.lineTo(cx - Math.abs(w) * 0.25, y2);
          ctx.moveTo(cx, top + Math.abs(h) * 0.62); ctx.lineTo(cx + Math.abs(w) * 0.25, y2);
          ctx.stroke();
          break;
        }
        default:
          ctx.rect(x1, y1, w, h); ctx.stroke();
      }
      ctx.restore();
    },
    [brushSize, color]
  );

  /* ---- pointer interaction ---- */
  const drag = useRef<{ start: Point; last: Point; active: boolean; preview: boolean } | null>(null);

  /* freehand geometry is recorded per layer so a saved project can describe the
     drawing, not just its flattened pixels. Format: x1,y1,w,x2,y2,w,... */
  const strokeData = useRef<Map<number, number[]>>(new Map());

  const paintStroke = useCallback(
    (from: Point, to: Point, erase: boolean) => {
      const rt = active();
      if (!rt) return;
      const ctx = rt.canvas.getContext("2d", { willReadFrequently: true })!;
      const width = erase ? brushSize * 3 : tool === "pencil" ? 1 : brushSize;
      ctx.save();
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      if (erase) {
        ctx.globalCompositeOperation = "destination-out";
      } else {
        ctx.globalCompositeOperation = "source-over";
        ctx.strokeStyle = color;
      }
      ctx.lineWidth = width;
      ctx.beginPath();
      ctx.moveTo(from.x, from.y);
      ctx.lineTo(to.x, to.y);
      ctx.stroke();
      ctx.restore();

      const log = strokeData.current.get(rt.id) ?? [];
      log.push(
        Math.round(from.x * 100) / 100,
        Math.round(from.y * 100) / 100,
        width,
        Math.round(to.x * 100) / 100,
        Math.round(to.y * 100) / 100,
        width
      );
      if (log.length > 20000) log.splice(0, log.length - 20000);
      strokeData.current.set(rt.id, log);
    },
    [active, brushSize, color, tool]
  );

  const floodFill = useCallback(
    (pt: Point) => {
      const rt = active();
      if (!rt) return;
      const ctx = rt.canvas.getContext("2d", { willReadFrequently: true })!;
      const img = ctx.getImageData(0, 0, rt.canvas.width, rt.canvas.height);
      const { width: w, height: h, data: p } = img;
      const sx = Math.floor(pt.x), sy = Math.floor(pt.y);
      if (sx < 0 || sy < 0 || sx >= w || sy >= h) return;
      const idx = (x: number, y: number) => (y * w + x) * 4;
      const start = idx(sx, sy);
      const target = [p[start], p[start + 1], p[start + 2], p[start + 3]];
      const { r, g, b } = hexToRgb(color);
      const fill = [r, g, b, 255];
      if (target.every((v, i) => Math.abs(v - fill[i]) < 4)) return;
      const match = (i: number) =>
        Math.abs(p[i] - target[0]) < 24 &&
        Math.abs(p[i + 1] - target[1]) < 24 &&
        Math.abs(p[i + 2] - target[2]) < 24 &&
        Math.abs(p[i + 3] - target[3]) < 24;
      const stack: number[] = [sx, sy];
      const seen = new Uint8Array(w * h);
      while (stack.length) {
        const y = stack.pop()!;
        const x = stack.pop()!;
        if (x < 0 || y < 0 || x >= w || y >= h) continue;
        if (seen[y * w + x]) continue;
        const i = idx(x, y);
        if (!match(i)) continue;
        seen[y * w + x] = 1;
        p[i] = fill[0]; p[i + 1] = fill[1]; p[i + 2] = fill[2]; p[i + 3] = fill[3];
        stack.push(x + 1, y, x - 1, y, x, y + 1, x, y - 1);
      }
      ctx.putImageData(img, 0, 0);
    },
    [active, color]
  );

  const onPointerDown = useCallback(
    (e: React.PointerEvent<HTMLCanvasElement>) => {
      const pt = toImageCoords(e.clientX, e.clientY);
      if (!pt) return;
      (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
      if (tool === "pick_color") {
        const buf = renderBuffer.current;
        if (!buf) return;
        const d = buf
          .getContext("2d", { willReadFrequently: true })!
          .getImageData(Math.floor(pt.x), Math.floor(pt.y), 1, 1).data;
        setColor(rgbToHex(d[0], d[1], d[2]));
        setStatus("Color picked");
        return;
      }
      if (tool === "fill") {
        pushHistory();
        floodFill(pt);
        setStatus("Fill");
        syncMeta();
        return;
      }
      if (tool === "crop" || tool === "selection" || tool === "select") {
        drag.current = { start: pt, last: pt, active: true, preview: true };
        setSelection({ x: pt.x, y: pt.y, width: 0, height: 0 });
        return;
      }
      if (tool === "text") {
        const rt = active();
        if (!rt) return;
        const val = typeof window !== "undefined" ? window.prompt("Text:", "") : null;
        if (val) {
          pushHistory();
          const ctx = rt.canvas.getContext("2d", { willReadFrequently: true })!;
          ctx.fillStyle = color;
          ctx.font = `${Math.max(12, brushSize * 4)}px Arial`;
          ctx.fillText(val, pt.x, pt.y);
          syncMeta();
        }
        return;
      }
      if (["blur", "sharpen", "desaturate", "bulge_pinch", "clone"].includes(tool)) {
        pushHistory();
        applyToActive(
          (d) => {
            const { width: w, data: p } = d;
            const radius = 18;
            const copy = new Uint8ClampedArray(p);
            for (let y = Math.floor(pt.y - radius); y <= pt.y + radius; y++)
              for (let x = Math.floor(pt.x - radius); x <= pt.x + radius; x++) {
                if (x < 0 || y < 0 || x >= w || y >= d.height) continue;
                if (Math.hypot(x - pt.x, y - pt.y) > radius) continue;
                const i = (y * w + x) * 4;
                if (tool === "desaturate") {
                  const v = 0.299 * copy[i] + 0.587 * copy[i + 1] + 0.114 * copy[i + 2];
                  p[i] = p[i + 1] = p[i + 2] = v;
                } else if (tool === "sharpen") {
                  for (let c = 0; c < 3; c++) {
                    const cur = copy[i + c];
                    const avg = (copy[i + c - 4] + copy[i + c + 4] + copy[i + c - w * 4] + copy[i + c + w * 4]) / 4;
                    p[i + c] = cur + (cur - avg) * 0.8;
                  }
                } else if (tool === "blur") {
                  for (let c = 0; c < 3; c++) {
                    p[i + c] = (copy[i + c] + copy[i + c - 4] + copy[i + c + 4] + copy[i + c - w * 4] + copy[i + c + w * 4]) / 5;
                  }
                }
              }
          },
          tool
        );
        syncMeta();
        return;
      }
      if (tool === "gradient") {
        drag.current = { start: pt, last: pt, active: true, preview: true };
        return;
      }
      if (tool === "shape") {
        drag.current = { start: pt, last: pt, active: true, preview: true };
        return;
      }
      // brush / pencil / erase
      pushHistory();
      drag.current = { start: pt, last: pt, active: true, preview: false };
      paintStroke(pt, { x: pt.x + 0.01, y: pt.y }, tool === "erase");
      composite();
    },
    [applyToActive, composite, floodFill, paintStroke, pushHistory, syncMeta, toImageCoords, tool]
  );

  const drawOverlay = useCallback(
    (pt: Point) => {
      const d = drag.current;
      if (!d) return;
      const ctx = displayRef.current!.getContext("2d", { willReadFrequently: true })!;
      const k = zoom / 100;
      if (tool === "shape") {
        ctx.save();
        ctx.setTransform(k, 0, 0, k, 0, 0);
        drawShape(ctx, d.start, pt, shapeTool, true, k);
        ctx.restore();
      } else if (tool === "gradient") {
        ctx.save();
        ctx.setTransform(k, 0, 0, k, 0, 0);
        ctx.strokeStyle = "#ffffff";
        ctx.setLineDash([5, 4]);
        ctx.lineWidth = 1 / k + 1;
        ctx.beginPath();
        ctx.moveTo(d.start.x, d.start.y);
        ctx.lineTo(pt.x, pt.y);
        ctx.stroke();
        ctx.restore();
      } else if (selection) {
        ctx.save();
        ctx.setTransform(k, 0, 0, k, 0, 0);
        ctx.strokeStyle = "#ffffff";
        ctx.setLineDash([5, 4]);
        ctx.lineWidth = 1 / k + 1;
        ctx.strokeRect(selection.x, selection.y, selection.width, selection.height);
        ctx.restore();
      }
    },
    [drawShape, selection, shapeTool, tool, zoom]
  );

  const onPointerMove = useCallback(
    (e: React.PointerEvent<HTMLCanvasElement>) => {
      const pt = toImageCoords(e.clientX, e.clientY);
      if (!pt) return;
      setMouse(pt);
      const d = drag.current;
      if (!d || !d.active) return;
      const k = zoom / 100;
      if (tool === "shape" || tool === "gradient") {
        d.last = pt;
        composite();
        drawOverlay(pt);
        return;
      }
      if (tool === "selection" || tool === "select" || tool === "crop") {
        const r: Rect = {
          x: Math.min(d.start.x, pt.x),
          y: Math.min(d.start.y, pt.y),
          width: Math.abs(pt.x - d.start.x),
          height: Math.abs(pt.y - d.start.y),
        };
        setSelection(r);
        composite();
        const ctx = displayRef.current!.getContext("2d", { willReadFrequently: true })!;
        ctx.save();
        ctx.setTransform(k, 0, 0, k, 0, 0);
        ctx.strokeStyle = "#f4f3f3";
        ctx.setLineDash([5, 4]);
        ctx.lineWidth = 1 / k + 1;
        ctx.strokeRect(r.x, r.y, r.width, r.height);
        ctx.restore();
        return;
      }
      paintStroke(d.last, pt, tool === "erase");
      d.last = pt;
      composite();
    },
    [composite, drawOverlay, paintStroke, tool, toImageCoords, zoom]
  );

  const onPointerUp = useCallback(
    (e: React.PointerEvent<HTMLCanvasElement>) => {
      const d = drag.current;
      if (!d) return;
      const pt = toImageCoords(e.clientX, e.clientY) || d.last;
      if (tool === "shape") {
        const rt = active();
        if (rt) {
          pushHistory();
          drawShape(rt.canvas.getContext("2d", { willReadFrequently: true })!, d.start, pt, shapeTool, false);
        }
      } else if (tool === "gradient") {
        const rt = active();
        if (rt) {
          pushHistory();
          const ctx = rt.canvas.getContext("2d", { willReadFrequently: true })!;
          const grad = ctx.createLinearGradient(d.start.x, d.start.y, pt.x, pt.y);
          grad.addColorStop(0, color);
          grad.addColorStop(1, "rgba(255,255,255,0)");
          ctx.fillStyle = grad;
          ctx.fillRect(0, 0, rt.canvas.width, rt.canvas.height);
        }
      } else if (tool === "crop" && selection && selection.width > 2 && selection.height > 2) {
        cropTo(selection);
        setSelection(null);
      }
      drag.current = null;
      syncMeta();
    },
    [active, color, drawShape, pushHistory, selection, shapeTool, syncMeta, toImageCoords, tool]
  );

  /* ---- document operations ---- */
  const newDocument = useCallback(
    (w: number, h: number) => {
      layerRefs.current.clear();
      history.current = [];
      future.current = [];
      setWidth(w);
      setHeight(h);
      const id = layerSeq++;
      const rt: LayerRuntime = { id, name: "Brush #1", visible: true, opacity: 100, x: 0, y: 0, canvas: makeCanvas(w, h) };
      const ctx = rt.canvas.getContext("2d", { willReadFrequently: true })!;
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, w, h);
      layerRefs.current.set(id, rt);
      setActiveLayerId(id);
      setZoom(100);
      setSelection(null);
      resizeDisplay(w, h, 1);
      setStatus(`New ${w}x${h} document`);
      syncMeta();
    },
    [syncMeta]
  );

  const cropTo = useCallback(
    (r: Rect) => {
      const x = Math.max(0, Math.round(r.x));
      const y = Math.max(0, Math.round(r.y));
      const w = Math.max(1, Math.round(r.width));
      const h = Math.max(1, Math.round(r.height));
      pushHistory();
      const next = new Map<number, LayerRuntime>();
      for (const [id, rt] of layerRefs.current) {
        const c = makeCanvas(w, h);
        const ctx = c.getContext("2d", { willReadFrequently: true })!;
        ctx.drawImage(rt.canvas, x - rt.x, y - rt.y, w, h, 0, 0, w, h);
        next.set(id, { ...rt, canvas: c, x: 0, y: 0 });
      }
      layerRefs.current = next;
      setWidth(w);
      setHeight(h);
      resizeDisplay(w, h, zoom / 100);
      setStatus("Cropped");
      syncMeta();
    },
    [pushHistory, syncMeta]
  );

  const resize = useCallback(
    (w: number, h: number) => {
      pushHistory();
      for (const rt of layerRefs.current.values()) {
        const c = makeCanvas(w, h);
        c.getContext("2d", { willReadFrequently: true })!.drawImage(rt.canvas, 0, 0, w, h);
        rt.canvas = c;
      }
      setWidth(w);
      setHeight(h);
      resizeDisplay(w, h, zoom / 100);
      syncMeta();
    },
    [pushHistory, syncMeta]
  );

  const rotate = useCallback(
    (deg: number) => {
      pushHistory();
      const rad = (deg * Math.PI) / 180;
      for (const rt of layerRefs.current.values()) {
        const sw = rt.canvas.width, sh = rt.canvas.height;
        const nw = deg % 180 === 0 ? sw : sh;
        const nh = deg % 180 === 0 ? sh : sw;
        const c = makeCanvas(nw, nh);
        const ctx = c.getContext("2d", { willReadFrequently: true })!;
        ctx.translate(nw / 2, nh / 2);
        ctx.rotate(rad);
        ctx.drawImage(rt.canvas, -sw / 2, -sh / 2);
        rt.canvas = c;
      }
      if (deg % 180 !== 0) {
        const t = W; setWidth(H); setHeight(t);
        resizeDisplay(H, W, zoom / 100);
      }
      syncMeta();
    },
    [H, W, pushHistory, resizeDisplay, syncMeta, zoom]
  );

  const flip = useCallback(
    (dir: "h" | "v") => {
      applyToActive((d) => {
        const { width: w, height: h, data: p } = d;
        const out = new Uint8ClampedArray(p.length);
        for (let y = 0; y < h; y++)
          for (let x = 0; x < w; x++) {
            const sx = dir === "h" ? w - 1 - x : x;
            const sy = dir === "v" ? h - 1 - y : y;
            const si = (sy * w + sx) * 4;
            const di = (y * w + x) * 4;
            out[di] = p[si]; out[di + 1] = p[si + 1]; out[di + 2] = p[si + 2]; out[di + 3] = p[si + 3];
          }
        p.set(out);
      }, dir === "h" ? "Flip horizontal" : "Flip vertical");
    },
    [applyToActive]
  );

  /* ---- layers ---- */
  const addLayer = useCallback(() => {
    pushHistory();
    const id = layerSeq++;
    const names = [...layerRefs.current.values()].length + 1;
    const rt: LayerRuntime = { id, name: `Layer #${names}`, visible: true, opacity: 100, x: 0, y: 0, canvas: makeCanvas(W, H) };
    layerRefs.current.set(id, rt);
    setActiveLayerId(id);
    syncMeta();
    setStatus("Layer added");
  }, [H, W, pushHistory, syncMeta]);

  const duplicateLayer = useCallback(() => {
    const rt = active();
    if (!rt) return;
    pushHistory();
    const id = layerSeq++;
    const c = makeCanvas(rt.canvas.width, rt.canvas.height);
    c.getContext("2d", { willReadFrequently: true })!.drawImage(rt.canvas, 0, 0);
    layerRefs.current.set(id, { ...rt, id, name: `${rt.name} copy`, canvas: c });
    setActiveLayerId(id);
    syncMeta();
  }, [active, pushHistory, syncMeta]);

  const deleteLayer = useCallback(() => {
    if (layerRefs.current.size <= 1) return;
    pushHistory();
    layerRefs.current.delete(activeLayerId);
    const next = [...layerRefs.current.keys()].pop()!;
    setActiveLayerId(next);
    syncMeta();
  }, [activeLayerId, pushHistory, syncMeta]);

  const toggleLayerVisible = useCallback(
    (id: number) => {
      const rt = layerRefs.current.get(id);
      if (!rt) return;
      rt.visible = !rt.visible;
      syncMeta();
    },
    [syncMeta]
  );

  const clearLayer = useCallback(() => {
    const rt = active();
    if (!rt) return;
    pushHistory();
    rt.canvas.getContext("2d", { willReadFrequently: true })!.clearRect(0, 0, rt.canvas.width, rt.canvas.height);
    syncMeta();
  }, [active, pushHistory, syncMeta]);

  const moveLayer = useCallback(
    (dir: "up" | "down") => {
      const entries = [...layerRefs.current.entries()];
      const idx = entries.findIndex(([id]) => id === activeLayerId);
      const swap = dir === "up" ? idx + 1 : idx - 1;
      if (swap < 0 || swap >= entries.length) return;
      [entries[idx], entries[swap]] = [entries[swap], entries[idx]];
      layerRefs.current = new Map(entries);
      syncMeta();
    },
    [activeLayerId, syncMeta]
  );

  const flatten = useCallback(() => {
    pushHistory();
    const rt = active();
    if (!rt) return;
    const ctx = rt.canvas.getContext("2d", { willReadFrequently: true })!;
    ctx.clearRect(0, 0, rt.canvas.width, rt.canvas.height);
    for (const l of layerRefs.current.values()) {
      if (!l.visible) continue;
      ctx.globalAlpha = l.opacity / 100;
      ctx.drawImage(l.canvas, l.x, l.y);
    }
    ctx.globalAlpha = 1;
    const keep = rt;
    layerRefs.current = new Map([[keep.id, keep]]);
    setActiveLayerId(keep.id);
    syncMeta();
    setStatus("Flattened");
  }, [active, pushHistory, syncMeta]);

  const mergeDown = useCallback(() => {
    const entries = [...layerRefs.current.values()];
    const idx = entries.findIndex((l) => l.id === activeLayerId);
    if (idx <= 0) return setStatus("Nothing to merge");
    const above = entries[idx];
    const below = entries[idx - 1];
    pushHistory();
    const ctx = below.canvas.getContext("2d", { willReadFrequently: true })!;
    ctx.globalAlpha = above.opacity / 100;
    ctx.drawImage(above.canvas, above.x - below.x, above.y - below.y);
    ctx.globalAlpha = 1;
    layerRefs.current.delete(above.id);
    setActiveLayerId(below.id);
    syncMeta();
    setStatus("Merged down");
  }, [activeLayerId, pushHistory, syncMeta]);

  /* ---- layer details ---- */
  const updateLayer = useCallback(
    (patch: Partial<Layer>) => {
      const rt = active();
      if (!rt) return;
      Object.assign(rt, patch);
      syncMeta();
    },
    [active, syncMeta]
  );

  /* ---- export ---- */
  /** composite every visible layer at native document resolution */
  const renderFlattened = useCallback((): HTMLCanvasElement => {
    const c = makeCanvas(W, H);
    const ctx = c.getContext("2d", { willReadFrequently: true })!;
    for (const rt of layerRefs.current.values()) {
      if (!rt.visible) continue;
      ctx.globalAlpha = rt.opacity / 100;
      ctx.drawImage(rt.canvas, rt.x, rt.y);
    }
    ctx.globalAlpha = 1;
    return c;
  }, [W, H]);

  const exportImage = useCallback(
    (format = "png", fileName?: string) => {
      const url = renderFlattened().toDataURL(`image/${format}`);
      triggerDownload(url, `${fileName || "export"}.${format}`);
      setStatus(`Exported ${format.toUpperCase()}`);
    },
    [renderFlattened]
  );

  /* ---- project (structured document) serialization ---- */
  const buildProjectJson = useCallback((): string => {
    const inputs = [...layerRefs.current.values()].map((rt, i) => {
      const log = strokeData.current.get(rt.id);
      return {
        id: rt.id,
        name: rt.name,
        x: rt.x,
        y: rt.y,
        visible: rt.visible,
        opacity: rt.opacity,
        order: i + 1,
        color,
        width: rt.canvas.width,
        height: rt.canvas.height,
        isVector: false,
        strokeData: log && log.length ? log.join(",") : undefined,
      };
    });
    return stringifyProject(
      buildProject({ width: W, height: H, activeLayerId, layers: inputs, guides })
    );
  }, [W, H, activeLayerId, color, guides]);

  const saveProject = useCallback(
    (fileName = "project") => {
      const json = buildProjectJson();
      triggerDownload(`data:application/json;charset=utf-8,${encodeURIComponent(json)}`, `${fileName}.json`);
      setStatus("Saved project");
    },
    [buildProjectJson]
  );

  const quickSave = useCallback(() => {
    try {
      localStorage.setItem("quicksave_data", buildProjectJson());
      setStatus("Quick saved");
    } catch {
      setStatus("Quick save failed");
    }
  }, [buildProjectJson]);

  const quickLoad = useCallback(() => {
    const raw = localStorage.getItem("quicksave_data");
    if (!raw) return setStatus("Nothing saved");
    try {
      const project = JSON.parse(raw) as { info?: { width?: number; height?: number } };
      const w = project.info?.width;
      const h = project.info?.height;
      if (w && h) {
        newDocument(w, h);
        setStatus("Quick loaded");
      }
    } catch {
      setStatus("Quick load failed");
    }
  }, [newDocument]);

  /* ---- zoom helpers (10% steps, matching the reference) ---- */
  const zoomIn = useCallback(() => setZoom((z) => Math.min(2000, Math.round(z) + 10)), []);
  const zoomOut = useCallback(() => setZoom((z) => Math.max(10, Math.round(z) - 10)), []);
  const zoomFit = useCallback(() => setZoom(100), []);
  const zoomOriginal = useCallback(() => setZoom(100), []);

  /* ---- size / resolution ---- */
  const pxSize = useMemo(() => {
    const dpi = parseInt(resolution, 10) || 72;
    return { w: ((W / dpi) * 2.54).toFixed(2), h: ((H / dpi) * 2.54).toFixed(2) };
  }, [W, H, resolution]);

  /* ---- form dialog helpers ---- */
  const openDialog = useCallback((d: DialogState) => setDialog(d), []);
  const closeDialog = useCallback(() => setDialog(null), []);

  return {
    // state
    width: W,
    height: H,
    layers: layerMeta,
    activeLayerId,
    tool,
    shapeTool,
    color,
    brushSize,
    pressure,
    zoom,
    mouse,
    grid,
    ruler,
    guides,
    fullscreen,
    resolution,
    dialog,
    status,
    selection,
    pxSize,
    attrs,
    setAttr,
    shapesOpen,
    setShapesOpen,
    shapesDraft,
    setShapesDraft,
    setTool,
    setShapeTool,
    setColor,
    setBrushSize,
    setPressure,
    setZoom,
    setGrid,
    setRuler,
    setGuides,
    setResolution,
    setFullscreen,
    setStatus,
    openDialog,
    closeDialog,
    setLayerMeta,
    // canvas wiring
    displayRef,
    composite,
    onPointerDown,
    onPointerMove,
    onPointerUp,
    // ops
    undo,
    redo,
    pushHistory,
    newDocument,
    cropTo,
    resize,
    rotate,
    flip,
    addLayer,
    duplicateLayer,
    deleteLayer,
    toggleLayerVisible,
    clearLayer,
    moveLayer,
    flatten,
    mergeDown,
    updateLayer,
    setActiveLayerId,
    exportImage,
    renderFlattened,
    buildProjectJson,
    saveProject,
    quickSave,
    quickLoad,
    zoomIn,
    zoomOut,
    zoomFit,
    zoomOriginal,
    effects,
    applyToActive,
    active,
    reRender,
  };
}

export type EditorApi = ReturnType<typeof useEditor>;

export const RESOLUTION_PRESETS = RESOLUTIONS;
export type { FieldDef, DialogState };
