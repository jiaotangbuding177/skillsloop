import { useEffect, useRef, useState } from "react";
import { useEditor } from "@/editor/useEditor";
import { useActions } from "@/editor/useActions";
import { MainMenu } from "@/components/MainMenu";
import { TopBar } from "@/components/TopBar";
import { Toolbar } from "@/components/Toolbar";
import { CanvasStage } from "@/components/CanvasStage";
import { RightSidebar } from "@/components/RightSidebar";
import { DialogHost } from "@/components/Dialog";
import { ShapesPopup } from "@/components/ShapesPopup";
import { cn } from "@/utils/cn";
import "@/editor/editor.css";

export function App() {
  const editor = useEditor();
  const dispatch = useActions(editor);
  const [leftOpen, setLeftOpen] = useState(false);
  const [rightOpen, setRightOpen] = useState(false);
  const keyTextRef = useRef<HTMLTextAreaElement | null>(null);

  /* global keyboard shortcuts (mirrors the reference app's bindings) */
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable)) return;

      const ctrl = e.ctrlKey || e.metaKey;
      if (ctrl && e.key.toLowerCase() === "z") {
        e.preventDefault();
        editor.undo();
        return;
      }
      if (ctrl && e.key.toLowerCase() === "y") {
        e.preventDefault();
        editor.redo();
        return;
      }
      if (ctrl && e.key.toLowerCase() === "a") {
        e.preventDefault();
        dispatch("select_all");
        return;
      }
      if (ctrl && e.key.toLowerCase() === "c") return dispatch("copy_clipboard");
      if (ctrl && e.key.toLowerCase() === "v") return dispatch("paste");

      switch (e.key) {
        case "F9":
          return dispatch("quick_save");
        case "F10":
          return dispatch("quick_load");
        case "F3":
          e.preventDefault();
          return dispatch("search");
        case "Delete":
          return dispatch("delete_selection");
        case "Escape":
          setLeftOpen(false);
          setRightOpen(false);
          return;
        case "+":
        case "=":
          return editor.zoomIn();
        case "-":
          return editor.zoomOut();
        default:
          break;
      }

      switch (e.key.toLowerCase()) {
        case "s":
          return dispatch("export");
        case "g":
          return dispatch("grid");
        case "i":
          return dispatch("information");
        case "n":
          return dispatch("layer_new");
        case "d":
          return dispatch("layer_duplicate");
        case "r":
          return dispatch("resize");
        case "l":
          return editor.rotate(-90);
        case "u":
          return dispatch("ruler");
        case "t":
          return dispatch("trim");
        case "o":
          return dispatch("open_file");
        case "h":
          return editor.setTool("shape");
        case "f":
          return dispatch("auto_adjust");
        default:
          break;
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [dispatch, editor]);

  return (
    <div className={cn("mp-app", editor.fullscreen && "mp-fullscreen")}>
      <div className="mp-mobile-bar">
        <button
          type="button"
          className="mp-hamburger"
          aria-label="Toggle Menu"
          aria-expanded={leftOpen}
          onClick={() => setLeftOpen((v) => !v)}
        >
          <span className="mp-bars" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
        </button>
        <MainMenu dispatch={dispatch} />
        <button
          type="button"
          className="mp-hamburger"
          aria-label="Toggle Menu"
          aria-expanded={rightOpen}
          onClick={() => setRightOpen((v) => !v)}
        >
          <span className="mp-bars" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
        </button>
      </div>

      <TopBar editor={editor} />

      <div className="mp-workspace">
        <Toolbar editor={editor} open={leftOpen} />
        <CanvasStage editor={editor} />
        <RightSidebar editor={editor} open={rightOpen} />
      </div>

      {(leftOpen || rightOpen) && (
        <div
          className="mp-backdrop"
          onClick={() => {
            setLeftOpen(false);
            setRightOpen(false);
          }}
        />
      )}

      <DialogHost editor={editor} />
      {editor.shapesOpen && <ShapesPopup editor={editor} />}

      <textarea
        ref={keyTextRef}
        className="mp-sr-only"
        aria-label="Text tool keyboard input"
        tabIndex={-1}
        readOnly
      />
    </div>
  );
}
