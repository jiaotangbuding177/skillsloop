import type { ToolDef } from "./types";

export const TOOLS: ToolDef[] = [
  { id: "select", title: "Select object tool" },
  { id: "selection", title: "Selection" },
  { id: "brush", title: "Brush" },
  { id: "pencil", title: "Pencil" },
  { id: "pick_color", title: "Pick color" },
  { id: "erase", title: "Erase" },
  { id: "magic_erase", title: "Magic Eraser Tool" },
  { id: "fill", title: "Fill" },
  { id: "shape", title: "Shapes (H)", group: "shape" },
  { id: "media", title: "Search Images" },
  { id: "text", title: "Text" },
  { id: "gradient", title: "Gradient" },
  { id: "clone", title: "Clone" },
  { id: "crop", title: "Crop" },
  { id: "blur", title: "Blur" },
  { id: "sharpen", title: "Sharpen" },
  { id: "desaturate", title: "Desaturate" },
  { id: "bulge_pinch", title: "Bulge/Pinch Tool" },
  { id: "animation", title: "Animation" },
];

export interface MenuLeaf {
  label: string;
  shortcut?: string;
  action?: string;
  /** nested submenu */
  sub?: MenuLeaf[];
  /** a nested shape picker uses a flat list of shape tools */
  separatorAfter?: boolean;
}

export type MenuEntry = MenuLeaf | "separator";

export interface MenuDef {
  id: string;
  label: string;
  items: MenuEntry[];
}

export const MENU: MenuDef[] = [
  {
    id: "file",
    label: "File",
    items: [
      { label: "New", action: "new" },
      "separator",
      {
        label: "Open",
        sub: [
          { label: "Open File", action: "open_file" },
          { label: "Open Data URL", action: "open_data_url" },
          { label: "Open URL", action: "open_url" },
        ],
      },
      { label: "Search Images ...", action: "search_images" },
      "separator",
      { label: "Export ...", shortcut: "S", action: "export" },
      { label: "Save As ...", shortcut: "Shift + S", action: "save_as" },
      { label: "Save As Data URL ...", action: "save_data_url" },
      { label: "Print ...", shortcut: "Ctrl+P", action: "print" },
      "separator",
      { label: "Quick Save", shortcut: "F9", action: "quick_save" },
      { label: "Quick Load", shortcut: "F10", action: "quick_load" },
    ],
  },
  {
    id: "edit",
    label: "Edit",
    items: [
      { label: "Undo", shortcut: "Ctrl+Z", action: "undo" },
      { label: "Redo", shortcut: "Ctrl+Y", action: "redo" },
      "separator",
      { label: "Delete Selection", shortcut: "Del", action: "delete_selection" },
      { label: "Copy Selection", action: "copy_selection" },
      { label: "Copy to Clipboard", shortcut: "Ctrl+C", action: "copy_clipboard" },
      { label: "Paste", shortcut: "Ctrl+V", action: "paste" },
      "separator",
      { label: "Select All", shortcut: "Ctrl+A", action: "select_all" },
    ],
  },
  {
    id: "view",
    label: "View",
    items: [
      {
        label: "Zoom",
        sub: [
          { label: "Zoom In", action: "zoom_in" },
          { label: "Zoom Out", action: "zoom_out" },
          "separator",
          { label: "Original Size", action: "zoom_original" },
          { label: "Fit Window", action: "zoom_fit" },
        ],
      },
      { label: "Grid", shortcut: "G", action: "grid" },
      {
        label: "Guides",
        sub: [
          { label: "Insert ...", action: "guides_insert" },
          { label: "Update", action: "guides_update" },
          { label: "Remove all", action: "guides_remove" },
        ],
      },
      { label: "Ruler", action: "ruler" },
      "separator",
      { label: "Full Screen", action: "full_screen" },
    ],
  },
  {
    id: "image",
    label: "Image",
    items: [
      { label: "Information ...", shortcut: "I", action: "information" },
      { label: "Canvas Size ...", action: "canvas_size" },
      { label: "Trim ...", shortcut: "T", action: "trim" },
      "separator",
      { label: "Resize ...", shortcut: "R", action: "resize" },
      { label: "Rotate ...", action: "rotate" },
      {
        label: "Flip",
        sub: [
          { label: "Horizontal", action: "flip_horizontal" },
          { label: "Vertical", action: "flip_vertical" },
        ],
      },
      { label: "Translate ...", action: "translate" },
      { label: "Opacity ...", action: "image_opacity" },
      "separator",
      { label: "Color Corrections ...", action: "color_corrections" },
      { label: "Auto Adjust Colors", shortcut: "F", action: "auto_adjust" },
      {
        label: "Decrease Color Depth",
        sub: [
          { label: "2 colors", action: "depth_2" },
          { label: "4 colors", action: "depth_4" },
          { label: "8 colors", action: "depth_8" },
          { label: "16 colors", action: "depth_16" },
          { label: "32 colors", action: "depth_32" },
          { label: "64 colors", action: "depth_64" },
        ],
      },
      { label: "Color Palette ...", action: "color_palette" },
      "separator",
      { label: "Histogram ...", action: "histogram" },
    ],
  },
  {
    id: "layer",
    label: "Layer",
    items: [
      { label: "New", shortcut: "N", action: "layer_new" },
      { label: "New from Selection", action: "layer_new_selection" },
      "separator",
      { label: "Duplicate", shortcut: "D", action: "layer_duplicate" },
      { label: "Show / Hide", action: "layer_show_hide" },
      { label: "Delete", action: "layer_delete" },
      { label: "Convert to Raster", action: "layer_raster" },
      "separator",
      {
        label: "Move",
        sub: [
          { label: "Up", action: "layer_move_up" },
          { label: "Down", action: "layer_move_down" },
        ],
      },
      { label: "Composition ...", action: "layer_composition" },
      { label: "Rename ...", action: "layer_rename" },
      { label: "Clear", action: "layer_clear" },
      "separator",
      { label: "Differences Down", action: "layer_differences" },
      { label: "Merge Down", action: "layer_merge" },
      { label: "Flatten Image", action: "layer_flatten" },
    ],
  },
  {
    id: "effects",
    label: "Effects",
    items: [
      { label: "Effect browser ...", action: "effect_browser" },
      "separator",
      {
        label: "Common Filters",
        sub: [
          { label: "Gaussian Blur Fast", action: "filter_gaussian_fast" },
          { label: "Gaussian Blur", action: "filter_gaussian" },
          { label: "Laplacian", action: "filter_laplacian" },
          { label: "Sobel", action: "filter_sobel" },
          { label: "Erode", action: "filter_erode" },
          { label: "Dilate", action: "filter_dilate" },
          { label: "Border", action: "filter_border" },
          { label: "Sepia", action: "filter_sepia" },
          { label: "Grayscale", action: "filter_grayscale" },
          { label: "Invert", action: "filter_invert" },
          { label: "Brightness", action: "filter_brightness" },
          { label: "Contrast", action: "filter_contrast" },
          { label: "Saturation", action: "filter_saturation" },
          { label: "Noise", action: "filter_noise" },
          { label: "Pixelate", action: "filter_pixelate" },
        ],
      },
      {
        label: "Instagram Filters",
        sub: [
          { label: "1977", action: "ig_1977" },
          { label: "Aden", action: "ig_aden" },
          { label: "Clarendon", action: "ig_clarendon" },
          { label: "Gingham", action: "ig_gingham" },
          { label: "Moon", action: "ig_moon" },
          { label: "Reyes", action: "ig_reyes" },
          { label: "Walden", action: "ig_walden" },
        ],
      },
      { label: "Black and White ...", action: "effect_bw" },
      { label: "Borders ...", action: "effect_borders" },
      { label: "Blueprint", action: "effect_blueprint" },
      { label: "Box Blur ...", action: "effect_box_blur" },
      { label: "Denoise ...", action: "effect_denoise" },
      { label: "Dither ...", action: "effect_dither" },
      { label: "Dot Screen ...", action: "effect_dot_screen" },
      { label: "Edge", action: "effect_edge" },
      { label: "Emboss", action: "effect_emboss" },
      { label: "Enrich ...", action: "effect_enrich" },
      { label: "Grains ...", action: "effect_grains" },
      { label: "Heatmap", action: "effect_heatmap" },
      { label: "Mosaic ...", action: "effect_mosaic" },
      { label: "Night Vision", action: "effect_night_vision" },
      { label: "Oil ...", action: "effect_oil" },
      { label: "Pencil", action: "effect_pencil" },
      { label: "Sharpen ...", action: "effect_sharpen" },
      { label: "Solarize", action: "effect_solarize" },
      { label: "Tilt Shift ...", action: "effect_tilt_shift" },
      { label: "Vignette ...", action: "effect_vignette" },
      { label: "Vibrance ...", action: "effect_vibrance" },
      { label: "Vintage ...", action: "effect_vintage" },
      { label: "Zoom Blur ...", action: "effect_zoom_blur" },
    ],
  },
  {
    id: "tools",
    label: "Tools",
    items: [
      { label: "Sprites", action: "sprites" },
      { label: "Key-Points", action: "key_points" },
      { label: "Content Fill ...", action: "content_fill" },
      "separator",
      { label: "Color Zoom ...", action: "color_zoom" },
      { label: "Replace Color ...", action: "replace_color" },
      { label: "Restore Alpha ...", action: "restore_alpha" },
      {
        label: "External",
        sub: [
          { label: "Vibrance", action: "ext_vibrance" },
          { label: "Histogram", action: "ext_histogram" },
          { label: "Color Balance", action: "ext_color_balance" },
          { label: "Curves", action: "ext_curves" },
        ],
      },
      "separator",
      {
        label: "Language",
        sub: [
          { label: "English", action: "lang_en" },
          "separator",
          { label: "عربي", action: "lang_ar" },
          { label: "简体中文", action: "lang_zh" },
          { label: "Deutsch", action: "lang_de" },
          { label: "Dutch", action: "lang_nl" },
          { label: "English (UK)", action: "lang_en_uk" },
          { label: "Español", action: "lang_es" },
          { label: "Français", action: "lang_fr" },
          { label: "Greek", action: "lang_el" },
          { label: "Italiano", action: "lang_it" },
          { label: "日本語", action: "lang_ja" },
          { label: "한국어", action: "lang_ko" },
          { label: "Lietuvių", action: "lang_lt" },
          { label: "Português", action: "lang_pt" },
          { label: "русский язык", action: "lang_ru" },
          { label: "Türkçe", action: "lang_tr" },
        ],
      },
      { label: "Search ...", shortcut: "F3", action: "search" },
      { label: "Settings ...", action: "settings" },
    ],
  },
  {
    id: "help",
    label: "Help",
    items: [
      { label: "Keyboard Shortcuts ...", action: "shortcuts" },
      { label: "Report Issues", action: "report_issues" },
      "separator",
      { label: "About ...", action: "about" },
    ],
  },
];

export const SHORTCUTS: { key: string; label: string }[] = [
  { key: "F", label: "Auto Adjust Colors" },
  { key: "F3 / ⌘ + F", label: "Search" },
  { key: "Ctrl + C", label: "Copy to Clipboard" },
  { key: "D", label: "Duplicate" },
  { key: "S", label: "Export" },
  { key: "G", label: "Grid on/off" },
  { key: "I", label: "Information" },
  { key: "N", label: "New layer" },
  { key: "O", label: "Open" },
  { key: "CTRL + V", label: "Paste" },
  { key: "F10", label: "Quick Load" },
  { key: "F9", label: "Quick Save" },
  { key: "R", label: "Resize" },
  { key: "L", label: "Rotate left" },
  { key: "U", label: "Ruler" },
  { key: "Shift + S", label: "Save As" },
  { key: "CTRL + A", label: "Select All" },
  { key: "H", label: "Shapes" },
  { key: "T", label: "Trim" },
  { key: "CTRL + Z", label: "Undo" },
  { key: "Scroll up", label: "Zoom in" },
  { key: "Scroll down", label: "Zoom out" },
];

export const ABOUT_ROWS: [string, string][] = [
  ["Name:", "miniPaint"],
  ["Version:", "4.14.3"],
  ["Description:", "Online image editor."],
  ["Author:", "ViliusL"],
  ["Email:", "www.viliusl@gmail.com"],
  ["GitHub:", "https://github.com/viliusle/miniPaint"],
  ["Website:", "https://viliusle.github.io/miniPaint/"],
];

/** literal inline SVG per tool (30x25 button, drawn ~17x17 centred) */
export const RESOLUTIONS: { label: string; value: string; w: number; h: number }[] = [
  { label: "Custom", value: "custom", w: 462, h: 347 },
  { label: "640x480 - 480p", value: "640x480", w: 640, h: 480 },
  { label: "800x600 - SVGA", value: "800x600", w: 800, h: 600 },
  { label: "1024x768 - XGA", value: "1024x768", w: 1024, h: 768 },
  { label: "1280x720 - hdtv, 720p", value: "1280x720", w: 1280, h: 720 },
  { label: "1600x1200 - UXGA", value: "1600x1200", w: 1600, h: 1200 },
  { label: "1920x1080 - Full HD, 1080p", value: "1920x1080", w: 1920, h: 1080 },
  { label: "3840x2160 - 4K UHD", value: "3840x2160", w: 3840, h: 2160 },
];

export const LAYOUTS: { label: string; value: string }[] = [
  { label: "Custom", value: "custom" },
  { label: "Landscape", value: "landscape" },
  { label: "Portrait", value: "portrait" },
];
