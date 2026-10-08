export type ToolId =
  | "select"
  | "selection"
  | "brush"
  | "pencil"
  | "pick_color"
  | "erase"
  | "magic_erase"
  | "fill"
  | "shape"
  | "media"
  | "text"
  | "gradient"
  | "clone"
  | "crop"
  | "blur"
  | "sharpen"
  | "desaturate"
  | "bulge_pinch"
  | "animation";

export interface ToolDef {
  id: ToolId;
  title: string;
  /** group id, used to keep only one shape tool visible at a time */
  group?: "shape";
}

export interface Layer {
  id: number;
  name: string;
  visible: boolean;
  opacity: number;
  x: number;
  y: number;
  /** serialized canvas data URL */
  data: string;
}

export interface Rect {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface Point {
  x: number;
  y: number;
}

export interface Guide {
  id: number;
  type: "vertical" | "horizontal";
  position: number;
}

/** A field row inside a generated form dialog */
export type FieldType = "number" | "text" | "color" | "checkbox" | "select" | "radio" | "range";

export interface FieldDef {
  name: string;
  label: string;
  type: FieldType;
  value?: string | number | boolean;
  min?: number;
  max?: number;
  step?: number;
  /** value used when the reset button is pressed */
  reset?: string | number | boolean;
  options?: { value: string; label: string }[];
  /** span both table columns */
  wide?: boolean;
}

export interface DialogState {
  kind: "about" | "new" | "settings" | "shortcuts" | "form" | "alert";
  title: string;
  fields?: FieldDef[];
  html?: string;
  /** callback key used by form dialogs */
  action?: string;
}
