import { TOOLS } from "@/editor/data";
import type { EditorApi } from "@/editor/useEditor";
import {
  SHAPE_TOOL_DEFS,
  SHAPE_TOOL_ICONS,
  TOOL_ICONS,
} from "./Icons";
import { cn } from "@/utils/cn";

interface Props {
  editor: EditorApi;
  open?: boolean;
}

export function Toolbar({ editor, open }: Props) {
  const shapesActive = editor.tool === "shape";

  return (
    <div className={cn("mp-toolbar", open && "open")} id="tools_container">
      {TOOLS.map((tool) => {
        const Icon = TOOL_ICONS[tool.id];
        const active = editor.tool === tool.id;
        return (
          <button
            key={tool.id}
            type="button"
            className={cn("mp-tool", active && "active")}
            title={tool.title}
            aria-label={tool.title}
            aria-pressed={active}
            onClick={() => {
              editor.setTool(tool.id);
              if (tool.id === "shape") {
                editor.setShapesDraft(editor.shapeTool);
                editor.setShapesOpen(true);
              }
            }}
          >
            {tool.id === "shape" && shapesActive ? (
              <ShapeStackIcon />
            ) : (
              <Icon />
            )}
          </button>
        );
      })}

      {shapesActive &&
        SHAPE_TOOL_DEFS.map((s) => {
          const Icon = SHAPE_TOOL_ICONS[s.id];
          const active = editor.shapeTool === s.id;
          return (
            <button
              key={s.id}
              type="button"
              className={cn("mp-tool", active && "active")}
              title={s.title}
              aria-label={s.title}
              aria-pressed={active}
              onClick={() => {
                editor.setShapeTool(s.id);
                editor.setTool("shape");
              }}
            >
              <Icon />
            </button>
          );
        })}
    </div>
  );
}

/** Small stacked preview shown on the shape tool when it is expanded. */
function ShapeStackIcon() {
  return (
    <svg width={21} height={18} viewBox="0 0 24 20" fill="none" stroke="currentColor" strokeWidth={1.6}>
      <rect x="2.5" y="2.5" width="10" height="10" />
      <circle cx="16.5" cy="6.5" r="4.5" />
      <path d="M6 17.5L11 12l5 5.5z" />
    </svg>
  );
}
