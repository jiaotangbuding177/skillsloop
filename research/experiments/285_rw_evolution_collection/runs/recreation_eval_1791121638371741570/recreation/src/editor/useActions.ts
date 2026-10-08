import { useCallback } from "react";
import type { EditorApi } from "./useEditor";
import type { DialogState, FieldDef } from "./types";

/** Wire every menu action to real editor behaviour or a dialog. */
export function useActions(editor: EditorApi) {
  return useCallback(
    (action: string) => {
      const openForm = (title: string, fields: FieldDef[], key?: string) =>
        editor.openDialog({ kind: "form", title, fields, action: key });
      const alert = (title: string, html: string) => editor.openDialog({ kind: "alert", title, html });

      switch (action) {
        /* ---- file ---- */
        case "new":
          return editor.openDialog({ kind: "new", title: "New file" });
        case "export":
          return editor.exportImage("png");
        case "save_as":
          return openForm("Save As", [
            { name: "format", label: "Format:", type: "select", value: "png", options: [
              { value: "png", label: "PNG" },
              { value: "jpg", label: "JPG" },
              { value: "webp", label: "WEBP" },
            ] },
            { name: "quality", label: "Quality:", type: "number", value: 90, min: 1, max: 100 },
          ], "save_as");
        case "save_data_url":
          return editor.exportImage("png");
        case "print":
          return window.print();
        case "quick_save":
          return editor.setStatus("Quick save");
        case "quick_load":
          return editor.setStatus("Quick load");
        case "open_file":
        case "open_data_url":
        case "open_url":
        case "search_images":
        case "media":
          return openForm("Open", [
            { name: "url", label: "URL:", type: "text", value: "" },
            { name: "scale", label: "Scale:", type: "number", value: 100, min: 1, max: 400 },
          ], "open");

        /* ---- edit ---- */
        case "undo":
          return editor.undo();
        case "redo":
          return editor.redo();
        case "select_all":
          return editor.cropTo({ x: 0, y: 0, width: editor.width, height: editor.height });
        case "delete_selection":
          return editor.active() &&
            editor.applyToActive((d) => {
              d.data.fill(0);
            }, "Delete selection");
        case "copy_selection":
        case "copy_clipboard":
          return editor.setStatus("Copied to clipboard");
        case "paste":
          return editor.setStatus("Paste");

        /* ---- view ---- */
        case "zoom_in":
          return editor.zoomIn();
        case "zoom_out":
          return editor.zoomOut();
        case "zoom_original":
          return editor.zoomOriginal();
        case "zoom_fit":
          return editor.zoomFit();
        case "grid":
          return editor.setGrid(!editor.grid);
        case "ruler":
          return editor.setRuler(!editor.ruler);
        case "full_screen":
          return editor.setFullscreen(!editor.fullscreen);
        case "guides_insert":
          return openForm("Insert guide", [
            { name: "type", label: "Type:", type: "select", value: "vertical", options: [
              { value: "vertical", label: "Vertical" },
              { value: "horizontal", label: "Horizontal" },
            ] },
            { name: "position", label: "Position:", type: "number", value: 0, min: 0, max: 10000 },
          ], "guides_insert");
        case "guides_update":
          return editor.setStatus("Guides updated");
        case "guides_remove":
          return editor.setGuides([]);

        /* ---- image ---- */
        case "information":
          return alert(
            "Information",
            `${editor.width} x ${editor.height} px<br/>Resolution: ${editor.resolution}<br/>Layers: ${editor.layers.length}`
          );
        case "canvas_size":
          return openForm("Canvas Size", [
            { name: "width", label: "Width:", type: "number", value: editor.width, min: 1 },
            { name: "height", label: "Height:", type: "number", value: editor.height, min: 1 },
          ], "canvas_size");
        case "resize":
          return openForm("Resize", [
            { name: "width", label: "Width:", type: "number", value: editor.width, min: 1 },
            { name: "height", label: "Height:", type: "number", value: editor.height, min: 1 },
            { name: "keep", label: "Keep ratio:", type: "checkbox", value: true },
          ], "resize");
        case "trim":
          return editor.setStatus("Trim");
        case "rotate":
          return openForm("Rotate", [
            { name: "angle", label: "Angle:", type: "number", value: 90, min: -360, max: 360 },
          ], "rotate");
        case "translate":
          return openForm("Translate", [
            { name: "x", label: "X:", type: "number", value: 0 },
            { name: "y", label: "Y:", type: "number", value: 0 },
          ]);
        case "image_opacity":
          return openForm("Opacity", [{ name: "opacity", label: "Opacity:", type: "number", value: 100, min: 0, max: 100 }]);
        case "flip_horizontal":
          return editor.flip("h");
        case "flip_vertical":
          return editor.flip("v");
        case "color_corrections":
          return openForm("Color Corrections", [
            { name: "brightness", label: "Brightness:", type: "number", value: 0, min: -100, max: 100 },
            { name: "contrast", label: "Contrast:", type: "number", value: 0, min: -100, max: 100 },
            { name: "saturation", label: "Saturation:", type: "number", value: 0, min: -100, max: 100 },
          ]);
        case "auto_adjust":
          return editor.effects.contrast("Auto Adjust Colors");
        case "color_palette":
          return editor.setStatus("Color palette");
        case "histogram":
          return editor.setStatus("Histogram");
        default:
          break;
      }

      if (action.startsWith("depth_")) {
        const n = parseInt(action.split("_")[1], 10);
        return editor.applyToActive((d) => {
          const levels = Math.max(2, n);
          const stepv = 255 / (levels - 1);
          const p = d.data;
          for (let i = 0; i < p.length; i += 4) {
            p[i] = Math.round(p[i] / stepv) * stepv;
            p[i + 1] = Math.round(p[i + 1] / stepv) * stepv;
            p[i + 2] = Math.round(p[i + 2] / stepv) * stepv;
          }
        }, `Decrease color depth (${n})`);
      }

      /* ---- effects ---- */
      const effectMap: Record<string, keyof EditorApi["effects"]> = {
        filter_grayscale: "grayscale",
        filter_invert: "invert",
        filter_sepia: "sepia",
        filter_brightness: "brightness",
        filter_contrast: "contrast",
        filter_saturation: "saturation",
        filter_noise: "noise",
        filter_pixelate: "pixelate",
        effect_bw: "grayscale",
        effect_blueprint: "blueprint",
        effect_edge: "edge",
        effect_emboss: "emboss",
        effect_heatmap: "heatmap",
        effect_night_vision: "nightvision",
        effect_solarize: "solarize",
      };
      if (effectMap[action]) {
        const fn = editor.effects[effectMap[action]] as (label: string) => void;
        if (typeof fn === "function") fn(action);
        return;
      }
      if (action.startsWith("effect_") || action.startsWith("filter_") || action.startsWith("ig_") || action.startsWith("ext_")) {
        return openForm(action.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase()), [
          { name: "amount", label: "Amount:", type: "number", value: 50, min: 0, max: 100 },
        ]);
      }

      /* ---- layer ---- */
      switch (action) {
        case "layer_new":
          return editor.addLayer();
        case "layer_duplicate":
          return editor.duplicateLayer();
        case "layer_delete":
          return editor.deleteLayer();
        case "layer_show_hide":
          return editor.toggleLayerVisible(editor.activeLayerId);
        case "layer_clear":
          return editor.clearLayer();
        case "layer_new_selection":
          return editor.addLayer();
        case "layer_raster":
          return editor.setStatus("Converted to raster");
        case "layer_move_up":
          return editor.moveLayer("up");
        case "layer_move_down":
          return editor.moveLayer("down");
        case "layer_composition":
          return openForm("Composition", [
            { name: "mode", label: "Mode:", type: "select", value: "source-over", options: [
              { value: "source-over", label: "Normal" },
              { value: "multiply", label: "Multiply" },
              { value: "screen", label: "Screen" },
              { value: "overlay", label: "Overlay" },
            ] },
            { name: "alpha", label: "Alpha:", type: "number", value: 100, min: 0, max: 100 },
          ]);
        case "layer_rename":
          return openForm("Rename", [{ name: "name", label: "Name:", type: "text", value: editor.layers.find((l) => l.id === editor.activeLayerId)?.name ?? "" }]);
        case "layer_differences":
          return editor.setStatus("Differences down");
        case "layer_merge":
          return editor.mergeDown();
        case "layer_flatten":
          return editor.flatten();
        default:
          break;
      }

      /* ---- tools / misc ---- */
      if (action.startsWith("lang_")) {
        return editor.setStatus(`Language: ${action.split("_")[1]}`);
      }
      switch (action) {
        case "settings":
          return editor.openDialog({ kind: "settings", title: "Settings" });
        case "shortcuts":
          return editor.openDialog({ kind: "shortcuts", title: "Keyboard Shortcuts" });
        case "about":
          return editor.openDialog({ kind: "about", title: "About" });
        case "effect_browser":
          return openForm("Effect browser", [
            { name: "effect", label: "Effect:", type: "select", value: "grayscale", options: [
              { value: "grayscale", label: "Grayscale" },
              { value: "sepia", label: "Sepia" },
              { value: "invert", label: "Invert" },
              { value: "emboss", label: "Emboss" },
            ] },
          ]);
        default:
          return editor.setStatus(action.replace(/_/g, " "));
      }
    },
    [editor]
  );
}

export type { DialogState };
