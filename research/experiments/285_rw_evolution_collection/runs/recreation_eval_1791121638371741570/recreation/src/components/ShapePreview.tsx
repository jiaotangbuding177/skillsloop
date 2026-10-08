import { useEffect, useRef } from "react";
import type { Point } from "@/editor/types";

/** Draw a filled shape outline into a canvas context, in the given box. */
export function paintShape(
  ctx: CanvasRenderingContext2D,
  shape: string,
  box: { x: number; y: number; w: number; h: number },
  opts: { fill?: string; stroke?: string; lineWidth?: number; filled?: boolean } = {}
) {
  const { fill = "#d9dde0", stroke = "#4a5254", lineWidth = 2, filled = true } = opts;
  const x1 = box.x;
  const y1 = box.y;
  const x2 = box.x + box.w;
  const y2 = box.y + box.h;
  ctx.save();
  ctx.lineWidth = lineWidth;
  ctx.lineJoin = "round";
  ctx.lineCap = "round";
  const w = box.w;
  const h = box.h;
  ctx.beginPath();
  switch (shape) {
    case "line":
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      break;
    case "arrow": {
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      const ang = Math.atan2(y2 - y1, x2 - x1);
      const hl = Math.min(w, h) * 0.28;
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2 - hl * Math.cos(ang - 0.45), y2 - hl * Math.sin(ang - 0.45));
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2 - hl * Math.cos(ang + 0.45), y2 - hl * Math.sin(ang + 0.45));
      break;
    }
    case "callout": {
      const bh = h * 0.72;
      ctx.rect(x1, y1, w, bh);
      ctx.moveTo(x1 + w * 0.12, y1 + bh);
      ctx.lineTo(x1 + w * 0.12, y2);
      ctx.lineTo(x1 + w * 0.42, y1 + bh);
      break;
    }
    case "cog": {
      const cx = (x1 + x2) / 2;
      const cy = (y1 + y2) / 2;
      const R = Math.min(w, h) / 2;
      const teeth = 9;
      for (let i = 0; i <= teeth * 2; i++) {
        const a = (i * Math.PI) / teeth;
        const rad = i % 2 === 0 ? R : R * 0.78;
        const px = cx + rad * Math.cos(a);
        const py = cy + rad * Math.sin(a);
        i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
      }
      ctx.closePath();
      ctx.moveTo(cx + R * 0.32, cy);
      ctx.arc(cx, cy, R * 0.32, 0, Math.PI * 2);
      break;
    }
    case "cylinder": {
      const rx = w / 2;
      const ry = Math.min(h / 4, 16);
      ctx.moveTo(x1, y1 + ry);
      ctx.ellipse((x1 + x2) / 2, y1 + ry, rx, ry, 0, Math.PI, 0, true);
      ctx.lineTo(x2, y2 - ry);
      ctx.ellipse((x1 + x2) / 2, y2 - ry, rx, ry, 0, 0, Math.PI, true);
      ctx.lineTo(x1, y1 + ry);
      ctx.closePath();
      ctx.moveTo(x1, y1 + ry);
      ctx.ellipse((x1 + x2) / 2, y1 + ry, rx, ry, 0, Math.PI, Math.PI * 2, true);
      break;
    }
    case "ellipse":
      ctx.ellipse((x1 + x2) / 2, (y1 + y2) / 2, w / 2, h / 2, 0, 0, Math.PI * 2);
      break;
    case "heart": {
      const cx = (x1 + x2) / 2;
      const cy = (y1 + y2) / 2;
      const sx = w / 2;
      const sy = h / 2;
      ctx.moveTo(cx, cy + sy * 0.8);
      ctx.bezierCurveTo(cx - sx * 1.4, cy - sy * 0.4, cx - sx * 0.5, cy - sy * 1.2, cx, cy - sy * 0.35);
      ctx.bezierCurveTo(cx + sx * 0.5, cy - sy * 1.2, cx + sx * 1.4, cy - sy * 0.4, cx, cy + sy * 0.8);
      ctx.closePath();
      break;
    }
    case "hexagon":
    case "pentagon":
    case "polygon": {
      const sides = shape === "hexagon" ? 6 : shape === "pentagon" ? 5 : 6;
      const cx = (x1 + x2) / 2;
      const cy = (y1 + y2) / 2;
      const rx = w / 2;
      const ry = h / 2;
      for (let i = 0; i <= sides; i++) {
        const a = -Math.PI / 2 + (i * 2 * Math.PI) / sides;
        const px = cx + rx * Math.cos(a);
        const py = cy + ry * Math.sin(a);
        i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
      }
      ctx.closePath();
      break;
    }
    case "human": {
      const cx = (x1 + x2) / 2;
      ctx.moveTo(cx + h * 0.11, y1 + h * 0.12);
      ctx.arc(cx, y1 + h * 0.12, h * 0.11, 0, Math.PI * 2);
      ctx.moveTo(cx, y1 + h * 0.23);
      ctx.lineTo(cx, y1 + h * 0.6);
      ctx.moveTo(cx - w * 0.24, y1 + h * 0.36);
      ctx.lineTo(cx + w * 0.24, y1 + h * 0.36);
      ctx.moveTo(cx, y1 + h * 0.6);
      ctx.lineTo(cx - w * 0.24, y2);
      ctx.moveTo(cx, y1 + h * 0.6);
      ctx.lineTo(cx + w * 0.24, y2);
      break;
    }
    case "moon": {
      const cx = (x1 + x2) / 2;
      const cy = (y1 + y2) / 2;
      const R = Math.min(w, h) / 2;
      ctx.arc(cx, cy, R, -Math.PI * 0.5, Math.PI * 0.5, false);
      ctx.arc(cx + R * 0.42, cy, R * 0.86, Math.PI * 0.5, -Math.PI * 0.5, true);
      ctx.closePath();
      break;
    }
    case "parallelogram":
      ctx.moveTo(x1 + w * 0.24, y1);
      ctx.lineTo(x2, y1);
      ctx.lineTo(x2 - w * 0.24, y2);
      ctx.lineTo(x1, y2);
      ctx.closePath();
      break;
    case "plus": {
      const t = Math.min(w, h) / 3;
      const cx = (x1 + x2) / 2;
      const cy = (y1 + y2) / 2;
      ctx.moveTo(cx - t / 2, y1);
      ctx.lineTo(cx + t / 2, y1);
      ctx.lineTo(cx + t / 2, cy - t / 2);
      ctx.lineTo(x2, cy - t / 2);
      ctx.lineTo(x2, cy + t / 2);
      ctx.lineTo(cx + t / 2, cy + t / 2);
      ctx.lineTo(cx + t / 2, y2);
      ctx.lineTo(cx - t / 2, y2);
      ctx.lineTo(cx - t / 2, cy + t / 2);
      ctx.lineTo(x1, cy + t / 2);
      ctx.lineTo(x1, cy - t / 2);
      ctx.lineTo(cx - t / 2, cy - t / 2);
      ctx.closePath();
      break;
    }
    case "rectangle":
      ctx.rect(x1, y1, w, h);
      break;
    case "right_triangle":
      ctx.moveTo(x1, y1);
      ctx.lineTo(x1, y2);
      ctx.lineTo(x2, y2);
      ctx.closePath();
      break;
    case "romb":
      ctx.moveTo((x1 + x2) / 2, y1);
      ctx.lineTo(x2, (y1 + y2) / 2);
      ctx.lineTo((x1 + x2) / 2, y2);
      ctx.lineTo(x1, (y1 + y2) / 2);
      ctx.closePath();
      break;
    case "star": {
      const cx = (x1 + x2) / 2;
      const cy = (y1 + y2) / 2;
      const R = Math.min(w, h) / 2;
      for (let i = 0; i < 10; i++) {
        const a = -Math.PI / 2 + (i * Math.PI) / 5;
        const rad = i % 2 === 0 ? R : R * 0.42;
        const px = cx + rad * Math.cos(a);
        const py = cy + rad * Math.sin(a);
        i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
      }
      ctx.closePath();
      break;
    }
    case "tear": {
      const cx = (x1 + x2) / 2;
      ctx.moveTo(cx, y1);
      ctx.bezierCurveTo(x2, y1 + h * 0.4, x2, y1 + h * 0.7, x2 - w * 0.15, y2 - h * 0.18);
      ctx.bezierCurveTo(x1 + w * 0.15, y2 + h * 0.05, x1 + w * 0.15, y1 + h * 0.35, cx, y1);
      ctx.closePath();
      break;
    }
    case "trapezoid":
      ctx.moveTo(x1 + w * 0.2, y1);
      ctx.lineTo(x2 - w * 0.2, y1);
      ctx.lineTo(x2, y2);
      ctx.lineTo(x1, y2);
      ctx.closePath();
      break;
    case "triangle":
      ctx.moveTo((x1 + x2) / 2, y1);
      ctx.lineTo(x2, y2);
      ctx.lineTo(x1, y2);
      ctx.closePath();
      break;
    case "bezier_curve": {
      ctx.moveTo(x1, y1);
      ctx.bezierCurveTo(x2, y1, x1, y2, x2, y2);
      break;
    }
    default:
      ctx.rect(x1, y1, w, h);
  }
  if (filled && stroke !== "none") {
    ctx.fillStyle = fill;
    ctx.fill();
  }
  if (stroke !== "none") {
    ctx.strokeStyle = stroke;
    ctx.stroke();
  }
  ctx.restore();
}

export function ShapePreview({ shape, size = 150, height = 120 }: { shape: string; size?: number; height?: number }) {
  const ref = useRef<HTMLCanvasElement | null>(null);
  useEffect(() => {
    const c = ref.current;
    if (!c) return;
    const ctx = c.getContext("2d", { willReadFrequently: true })!;
    ctx.clearRect(0, 0, c.width, c.height);
    const pad = 14;
    paintShape(
      ctx,
      shape,
      { x: pad, y: pad, w: c.width - pad * 2, h: c.height - pad * 2 },
      { fill: "#d8dcde", stroke: "#3f4648", lineWidth: 2.5 }
    );
  }, [shape]);

  return <canvas ref={ref} width={size} height={height} className="mp-shape-canvas" />;
}

export type { Point };
