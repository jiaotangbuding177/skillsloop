import { useCallback, useEffect, useRef } from "react";
import { SplitKnobIcon } from "@/components/icons";

type Props = {
  leftSrc: string;
  rightSrc: string;
  /** Fraction 0-1 of the divider position across the viewport. */
  split: number;
  onSplitChange: (next: number) => void;
  /** Display scale applied to both layers. */
  zoom: number;
  /** Clockwise rotation in degrees applied to both layers. */
  rotate: number;
  /** Natural pixel size of the bitmap being shown. */
  imageWidth: number;
  imageHeight: number;
  leftAlt: string;
  rightAlt: string;
};

/**
 * Draggable two-up comparison. Each side is a viewport-sized layer clipped at
 * the divider; the bitmap inside sits at its natural size (centred, scaled by
 * the zoom control) so the split always spans the visible area.
 */
export function CompareView({
  leftSrc,
  rightSrc,
  split,
  onSplitChange,
  zoom,
  rotate,
  imageWidth,
  imageHeight,
  leftAlt,
  rightAlt,
}: Props) {
  const stageRef = useRef<HTMLDivElement>(null);
  const dragging = useRef(false);

  const updateFromClientX = useCallback(
    (clientX: number) => {
      const rect = stageRef.current?.getBoundingClientRect();
      if (!rect || rect.width === 0) return;
      const ratio = (clientX - rect.left) / rect.width;
      onSplitChange(Math.max(0, Math.min(1, ratio)));
    },
    [onSplitChange],
  );

  useEffect(() => {
    const onMove = (e: PointerEvent) => {
      if (dragging.current) updateFromClientX(e.clientX);
    };
    const onUp = () => {
      dragging.current = false;
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
  }, [updateFromClientX]);

  const transform = `translate(-50%, -50%) rotate(${rotate}deg) scale(${zoom})`;
  const imgStyle = {
    width: `${imageWidth}px`,
    height: `${imageHeight}px`,
    transform,
  };

  return (
    <div
      className="two-up"
      ref={stageRef}
      style={{ ["--split-point" as string]: `${split * 100}%` }}
    >
      <div className="layer clip-left">
        <img src={leftSrc} alt={leftAlt} style={imgStyle} draggable={false} />
      </div>
      <div className="layer clip-right">
        <img src={rightSrc} alt={rightAlt} style={imgStyle} draggable={false} />
      </div>
      <div
        className="two-up-handle"
        role="slider"
        aria-label="Comparison position"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(split * 100)}
        tabIndex={0}
        onPointerDown={(e) => {
          dragging.current = true;
          (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
        }}
        onKeyDown={(e) => {
          if (e.key === "ArrowLeft") onSplitChange(Math.max(0, split - 0.02));
          if (e.key === "ArrowRight") onSplitChange(Math.min(1, split + 0.02));
        }}
      >
        <span className="two-up-knob">
          <SplitKnobIcon />
        </span>
      </div>
    </div>
  );
}
