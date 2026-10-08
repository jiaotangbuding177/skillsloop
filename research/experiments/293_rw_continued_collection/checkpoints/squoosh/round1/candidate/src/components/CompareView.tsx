import { useCallback, useEffect, useRef } from "react";
import { SplitKnobIcon } from "@/components/icons";

type Props = {
  leftSrc: string;
  rightSrc: string;
  /** Fraction 0-1 of the divider position. */
  split: number;
  onSplitChange: (next: number) => void;
  /** Alt text for the two layers. */
  leftAlt: string;
  rightAlt: string;
};

/**
 * Draggable two-up image comparison. Two stacked layers are clipped at the
 * divider; the handle moves with pointer drags.
 */
export function CompareView({
  leftSrc,
  rightSrc,
  split,
  onSplitChange,
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
      if (!dragging.current) return;
      updateFromClientX(e.clientX);
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

  const pct = `${split * 100}%`;

  return (
    <div
      className="two-up"
      ref={stageRef}
      style={{ ["--split-point" as string]: pct }}
    >
      <img
        src={leftSrc}
        alt={leftAlt}
        className="clip-left"
        draggable={false}
      />
      <img
        src={rightSrc}
        alt={rightAlt}
        className="clip-right"
        draggable={false}
      />
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
