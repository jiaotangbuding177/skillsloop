import { useEffect } from "react";
import type { EditorApi } from "@/editor/useEditor";

export function CanvasStage({ editor }: { editor: EditorApi }) {
  const scale = editor.zoom / 100;
  const dispW = Math.max(1, Math.round(editor.width * scale));
  const dispH = Math.max(1, Math.round(editor.height * scale));

  useEffect(() => {
    editor.composite();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editor.width, editor.height, editor.zoom, editor.layers.length]);

  return (
    <div className="mp-canvas-area">
      {editor.ruler && <div className="mp-ruler-top" aria-hidden="true" />}
      {editor.ruler && <div className="mp-ruler-left" aria-hidden="true" />}
      <div
        className="mp-canvas-stage"
        style={{ width: dispW, height: dispH, marginLeft: editor.ruler ? 20 : 0, marginTop: editor.ruler ? 20 : 0 }}
      >
        <div className="mp-checker" aria-hidden="true" />
        <canvas
          ref={editor.displayRef}
          width={editor.width}
          height={editor.height}
          style={{ width: dispW, height: dispH }}
          onPointerDown={editor.onPointerDown}
          onPointerMove={editor.onPointerMove}
          onPointerUp={editor.onPointerUp}
          onPointerLeave={() => editor.setStatus(editor.status)}
        />
        {editor.grid && (
          <div
            className="mp-grid-overlay"
            aria-hidden="true"
            style={{
              position: "absolute",
              inset: 0,
              pointerEvents: "none",
              backgroundImage:
                "linear-gradient(to right, rgba(0,0,0,0.25) 1px, transparent 1px), linear-gradient(to bottom, rgba(0,0,0,0.25) 1px, transparent 1px)",
              backgroundSize: `${Math.max(4, 10 * scale)}px ${Math.max(4, 10 * scale)}px`,
            }}
          />
        )}
        {editor.selection && (
          <div
            className="mp-selection-box"
            aria-hidden="true"
            style={{
              position: "absolute",
              left: editor.selection.x * scale,
              top: editor.selection.y * scale,
              width: editor.selection.width * scale,
              height: editor.selection.height * scale,
              border: "1px dashed #000",
              pointerEvents: "none",
            }}
          />
        )}
        {editor.guides.map((g) => (
          <div
            key={g.id}
            className="mp-guide"
            aria-hidden="true"
            style={{
              position: "absolute",
              pointerEvents: "none",
              background: "#37c3ff",
              ...(g.type === "vertical"
                ? { left: g.position * scale, top: 0, bottom: 0, width: 1 }
                : { top: g.position * scale, left: 0, right: 0, height: 1 }),
            }}
          />
        ))}
      </div>
      <span className="mp-sr-only" role="status">
        {editor.status}
      </span>
    </div>
  );
}
