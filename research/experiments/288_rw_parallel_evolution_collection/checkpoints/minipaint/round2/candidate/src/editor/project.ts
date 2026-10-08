/** Project serialization for the editor.
 *
 * A "project" is a small structured JSON document describing every layer so it
 * can be reopened later. Image exports use the canvas blob instead.
 */

export const PROJECT_VERSION = "4.14.3";

export interface ProjectInfo {
  width: number;
  height: number;
  about: string;
  date: string;
  version: string;
  layer_active: number;
  guides: { type: string; position: number }[];
}

export interface ProjectLayer {
  id: number;
  parent_id: number;
  name: string;
  type: null;
  link: null;
  x: number;
  y: number;
  width: null;
  width_original: null;
  height: null;
  height_original: null;
  visible: boolean;
  is_vector: boolean;
  hide_selection_if_active: boolean;
  opacity: number;
  order: number;
  composition: string;
  rotate: number;
  /** freehand stroke geometry: x1,y1,width,x2,y2,width,... */
  data: string | null;
  params: Record<string, unknown>;
  status: null;
  color: string;
  filters: unknown[];
  render_function: null;
}

export interface Project {
  info: ProjectInfo;
  user_fonts: Record<string, unknown>;
  layers: ProjectLayer[];
  data: unknown[];
}

export interface ProjectLayerInput {
  id: number;
  name: string;
  x: number;
  y: number;
  visible: boolean;
  opacity: number;
  order: number;
  color: string;
  /** optional captured stroke geometry */
  strokeData?: string;
  width?: number;
  height?: number;
  isVector?: boolean;
}

export function buildProject(opts: {
  width: number;
  height: number;
  activeLayerId: number;
  layers: ProjectLayerInput[];
  guides?: { type: string; position: number }[];
}): Project {
  const { width, height, activeLayerId, layers, guides = [] } = opts;
  const date = new Date().toISOString().slice(0, 10);
  return {
    info: {
      width,
      height,
      about:
        "Image data with multi-layers. Can be opened using miniPaint - https://github.com/viliusle/miniPaint",
      date,
      version: PROJECT_VERSION,
      layer_active: activeLayerId,
      guides,
    },
    user_fonts: {},
    layers: layers.map((l) => ({
      id: l.id,
      parent_id: 0,
      name: l.name,
      type: null,
      link: null,
      x: l.x,
      y: l.y,
      width: l.width ?? null,
      width_original: null,
      height: l.height ?? null,
      height_original: null,
      visible: l.visible,
      is_vector: l.isVector ?? false,
      hide_selection_if_active: false,
      opacity: l.opacity,
      order: l.order,
      composition: "source-over",
      rotate: 0,
      data: l.strokeData ?? null,
      params: {},
      status: null,
      color: l.color,
      filters: [],
      render_function: null,
    })),
    data: [],
  };
}

export function stringifyProject(project: Project): string {
  return JSON.stringify(project, null, "\t");
}

/** Human readable byte size, e.g. "791 B", "1.2 KB". */
export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export const SAVE_TYPES: { value: string; label: string }[] = [
  { value: "PNG", label: "PNG - Portable Network Graphics" },
  { value: "JPG", label: "JPG - JPG/JPEG Format" },
  { value: "WEBP", label: "WEBP - Weppy File Format" },
  { value: "GIF", label: "GIF - Graphics Interchange Format" },
  { value: "BMP", label: "BMP - Windows Bitmap" },
  { value: "TIFF", label: "TIFF - Tag Image File Format" },
];

export const PROJECT_TYPE = { value: "JSON", label: "JSON - Full layers data" };
