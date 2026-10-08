import { useEffect } from "react";
import type { EditorApi } from "@/editor/useEditor";
import { SHAPE_TOOL_DEFS } from "./Icons";
import { ShapePreview } from "./ShapePreview";

export function ShapesPopup({ editor }: { editor: EditorApi }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && editor.setShapesOpen(false);
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [editor]);

  return (
    <div className="mp-overlay" onMouseDown={(e) => e.target === e.currentTarget && editor.setShapesOpen(false)}>
      <div className="mp-popup wide" role="dialog" aria-modal="true" aria-label="Shapes">
        <header>
          <h2>Shapes</h2>
          <button type="button" className="mp-dialog-close" aria-label="Close" onClick={() => editor.setShapesOpen(false)}>
            &times;
          </button>
        </header>
        <div className="mp-popup-content">
          <div className="mp-shape-grid">
            {SHAPE_TOOL_DEFS.map((s) => (
              <button
                key={s.id}
                type="button"
                className="mp-shape-cell"
                aria-pressed={editor.shapesDraft === s.id}
                title={s.title}
                onClick={() => editor.setShapesDraft(s.id)}
                onDoubleClick={() => {
                  editor.setShapeTool(s.id);
                  editor.setShapesOpen(false);
                }}
              >
                <ShapePreview shape={s.id} />
                <span className="mp-shape-title">{s.title}</span>
              </button>
            ))}
          </div>
        </div>
        <footer>
          <button
            type="button"
            className="mp-dialog-btn"
            onClick={() => {
              editor.setShapeTool(editor.shapesDraft);
              editor.setShapesOpen(false);
            }}
          >
            Ok
          </button>
          <button type="button" className="mp-dialog-btn" onClick={() => editor.setShapesOpen(false)}>
            Cancel
          </button>
        </footer>
      </div>
    </div>
  );
}
