import { useEffect, useRef } from "react";
import type { EditorApi } from "@/editor/useEditor";
import { Block } from "./Block";
import { NumberInput } from "./NumberInput";
import { ColorPicker } from "./ColorPicker";
import { cn } from "@/utils/cn";

export function RightSidebar({ editor, open }: { editor: EditorApi; open?: boolean }) {
  return (
    <aside className={cn("mp-sidebar", open && "open")}>
      <PreviewBlock editor={editor} />
      <Block title="Colors" className="colors">
        <ColorPicker editor={editor} />
      </Block>
      <InformationBlock editor={editor} />
      <LayerDetails editor={editor} />
      <LayersBlock editor={editor} />
    </aside>
  );
}

function PreviewBlock({ editor }: { editor: EditorApi }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    let raf = 0;
    const loop = () => {
      const src = editor.displayRef.current;
      const dst = canvasRef.current;
      if (src && dst) {
        if (dst.width !== src.width || dst.height !== src.height) {
          dst.width = src.width;
          dst.height = src.height;
        }
        const ctx = dst.getContext("2d")!;
        ctx.clearRect(0, 0, dst.width, dst.height);
        ctx.drawImage(src, 0, 0);
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [editor.displayRef]);

  return (
    <Block title="Preview" className="preview">
      <div className="mp-preview-wrap" aria-label="Preview">
        <canvas ref={canvasRef} width={462} height={346} />
      </div>
      <div className="mp-preview-details">
        <div className="mp-preview-buttons">
          <button type="button" className="mp-mini-btn" title="Zoom out" onClick={editor.zoomOut}>
            -
          </button>
          <button type="button" className="mp-mini-btn" title="Original size" onClick={editor.zoomOriginal}>
            {Math.round(editor.zoom)}%
          </button>
          <button type="button" className="mp-mini-btn" title="Zoom in" onClick={editor.zoomIn}>
            +
          </button>
          <button type="button" className="mp-mini-btn" title="Fit window" onClick={editor.zoomFit}>
            Fit
          </button>
        </div>
        <input
          type="range"
          className="mp-range"
          min={10}
          max={500}
          value={Math.round(editor.zoom)}
          aria-label="Zoom"
          onChange={(e) => editor.setZoom(parseInt(e.target.value, 10))}
        />
      </div>
    </Block>
  );
}

function InformationBlock({ editor }: { editor: EditorApi }) {
  return (
    <Block title="Information">
      <dl className="mp-info">
        <dt>Size:</dt>
        <dd>
          {editor.width} x {editor.height} px
        </dd>
        <dt>Mouse:</dt>
        <dd>{editor.mouse ? `${Math.round(editor.mouse.x)} x ${Math.round(editor.mouse.y)} px` : "- px"}</dd>
        <dt>Resolution:</dt>
        <dd>{editor.resolution}</dd>
      </dl>
    </Block>
  );
}

function LayerDetails({ editor }: { editor: EditorApi }) {
  const layer = editor.layers.find((l) => l.id === editor.activeLayerId) ?? editor.layers[0];
  if (!layer) return null;
  return (
    <Block title="Layer details" className="details">
      <div className="mp-details-body">
        <div className="mp-detail-row">
          <span>X</span>
          <NumberInput value={layer.x} ariaLabel="X" onChange={(v) => editor.updateLayer({ x: v })} />
          <button className="mp-reset-btn" title="Reset" aria-label="Reset" onClick={() => editor.updateLayer({ x: 0 })}>
            &#8635;
          </button>
        </div>
        <div className="mp-detail-row">
          <span>Y:</span>
          <NumberInput value={layer.y} ariaLabel="Y:" onChange={(v) => editor.updateLayer({ y: v })} />
          <button className="mp-reset-btn" title="Reset" aria-label="Reset" onClick={() => editor.updateLayer({ y: 0 })}>
            &#8635;
          </button>
        </div>
        <div className="mp-detail-row">
          <span>Width:</span>
          <NumberInput value={NaN} disabled ariaLabel="Width:" onChange={() => {}} />
        </div>
        <div className="mp-detail-row">
          <span>Height:</span>
          <NumberInput value={NaN} disabled ariaLabel="Height:" onChange={() => {}} />
        </div>
        <div className="mp-details-sep" role="separator" />
        <div className="mp-detail-row">
          <span>Rotate:</span>
          <NumberInput value={0} ariaLabel="Rotate:" onChange={() => {}} />
          <button className="mp-reset-btn" title="Reset" aria-label="Reset" onClick={() => {}}>
            &#8635;
          </button>
        </div>
        <div className="mp-detail-row">
          <span>Opacity:</span>
          <NumberInput
            value={layer.opacity}
            min={0}
            max={100}
            ariaLabel="Opacity:"
            onChange={(v) => editor.updateLayer({ opacity: v })}
          />
          <button
            className="mp-reset-btn"
            title="Reset"
            aria-label="Reset"
            onClick={() => editor.updateLayer({ opacity: 100 })}
          >
            &#8635;
          </button>
        </div>
        <div className="mp-detail-row mp-detail-color">
          <span>Color:</span>
          <input
            type="text"
            value={editor.color}
            aria-label="Color:"
            onChange={(e) => editor.setColor(e.target.value)}
            onClick={() => editor.setTool("pick_color")}
          />
        </div>
      </div>
    </Block>
  );
}

function LayersBlock({ editor }: { editor: EditorApi }) {
  const named = editor.layers.find((l) => l.id === editor.activeLayerId);
  return (
    <Block title="Layers" className="layers">
      <div className="mp-layer-actions">
        <button type="button" className="mp-mini-btn" title="New layer" aria-label="New layer" onClick={editor.addLayer}>
          +
        </button>
        <button
          type="button"
          className="mp-mini-btn"
          title="Duplicate layer"
          aria-label="Duplicate layer"
          onClick={editor.duplicateLayer}
        >
          D
        </button>
        <button
          type="button"
          className="mp-mini-btn"
          title="Rename layer"
          aria-label="Rename layer"
          onClick={() => editor.setStatus("Rename layer")}
        >
          R
        </button>
        <button
          type="button"
          className="mp-mini-btn"
          title="Move down"
          aria-label="Move down"
          onClick={() => editor.moveLayer("down")}
        >
          &#8595;
        </button>
        <button
          type="button"
          className="mp-mini-btn"
          title="Move up"
          aria-label="Move up"
          onClick={() => editor.moveLayer("up")}
        >
          &#8593;
        </button>
      </div>
      <div className="mp-layer-list">
        {[...editor.layers].reverse().map((layer) => (
          <div key={layer.id} className={cn("mp-layer-row", layer.id === editor.activeLayerId && "active")}>
            <button
              type="button"
              className="mp-layer-vis"
              title="Hide"
              aria-label="Hide"
              onClick={() => editor.toggleLayerVisible(layer.id)}
            >
              {layer.visible ? (
                <svg width={15} height={11} viewBox="0 0 20 14" fill="none" stroke="currentColor" strokeWidth={1.6}>
                  <path d="M1 7s3.5-6 9-6 9 6 9 6-3.5 6-9 6-9-6-9-6z" />
                  <circle cx="10" cy="7" r="2.5" />
                </svg>
              ) : (
                <svg width={15} height={11} viewBox="0 0 20 14" fill="none" stroke="currentColor" strokeWidth={1.6}>
                  <path d="M1 7s3.5-6 9-6c2 0 3.7.7 5 1.6M19 7s-3.5 6-9 6c-1.4 0-2.7-.3-3.8-.9" />
                  <path d="M3 1l14 12" />
                </svg>
              )}
            </button>
            <button
              type="button"
              className="mp-layer-name"
              title={layer.name}
              aria-label={layer.name}
              onClick={() => editor.setActiveLayerId(layer.id)}
            >
              {layer.name}
            </button>
            <button
              type="button"
              className="mp-layer-del"
              title="Delete"
              aria-label="Delete"
              onClick={() => {
                editor.setActiveLayerId(layer.id);
                setTimeout(editor.deleteLayer, 0);
              }}
            >
              <svg width={11} height={11} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth={1.8}>
                <path d="M3 3l10 10M13 3L3 13" />
              </svg>
            </button>
          </div>
        ))}
      </div>
      {named ? null : null}
    </Block>
  );
}
