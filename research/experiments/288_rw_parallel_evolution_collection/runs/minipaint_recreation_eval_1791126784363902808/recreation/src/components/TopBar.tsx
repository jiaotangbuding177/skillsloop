import type { EditorApi } from "@/editor/useEditor";
import { NumberInput } from "./NumberInput";
import { LogoBadge } from "./LogoBadge";

const FONTS = [
  "",
  "[Add Font...]",
  "Amatic SC",
  "Arial",
  "Arimo",
  "Codystar",
  "Courier",
  "Creepster",
  "Helvetica",
  "Impact",
  "Indie Flower",
  "Lato",
  "Lora",
  "Merriweather",
  "Monospace",
  "Monoton",
  "Montserrat",
  "Mukta",
  "Muli",
  "Nosifer",
  "Nunito",
  "Orbitron",
  "Oswald",
  "PT Sans",
  "PT Serif",
  "Pacifico",
  "Playfair Display",
  "Poppins",
  "Raleway",
  "Roboto",
  "Rubik",
  "Special Elite",
  "Tahoma",
  "Tangerine",
  "Times New Roman",
  "Titillium Web",
  "Ubuntu",
  "Verdana",
];

export function TopBar({ editor }: { editor: EditorApi }) {
  const { attrs, setAttr, tool } = editor;

  const Toggle = ({ id }: { id: string }) => {
    const value = Boolean(attrs[id]);
    const label = {
      auto_select: "Auto select",
      global: "Global",
      circle: "Circle",
      strict: "Strict",
      anti_aliasing: "Anti aliasing",
      contiguous: "Contiguous",
      radial: "Radial",
      bulge: "Bulge",
      play: "Play",
      pressure: "Pressure",
    }[id] ?? id;
    return (
      <button type="button" className="mp-toggle" id={id} aria-pressed={value} onClick={() => setAttr(id, !value)}>
        {label}
      </button>
    );
  };

  const Num = ({ id, label, min = 1, max = 999 }: { id: string; label: string; min?: number; max?: number }) => (
    <div className="mp-attr">
      <span aria-hidden="true">{label}</span>
      <NumberInput
        ariaLabel={label}
        value={Number(attrs[id])}
        min={min}
        max={max}
        onChange={(v) => setAttr(id, v)}
      />
    </div>
  );

  const ColorIn = ({ id, label }: { id: string; label: string }) => (
    <div className="mp-attr">
      <span aria-hidden="true">{label}</span>
      <span className="mp-color-input">
        <input
          type="color"
          aria-label={label}
          value={String(attrs[id] ?? "#000000")}
          onChange={(e) => setAttr(id, e.target.value)}
        />
      </span>
    </div>
  );

  const Select = ({
    id,
    label,
    options,
  }: {
    id: string;
    label: string;
    options: { value: string; label: string }[];
  }) => (
    <div className="mp-attr">
      <span aria-hidden="true">{label}</span>
      <select aria-label={label} value={String(attrs[id])} onChange={(e) => setAttr(id, e.target.value)}>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );

  return (
    <div className="mp-submenu">
      <a
        className="mp-logo"
        href="#"
        onClick={(e) => {
          e.preventDefault();
          editor.setStatus("miniPaint");
        }}
      >
        <LogoBadge />
        <span>miniPaint</span>
      </a>
      <div className="mp-attributes" id="action_attributes">
        {tool === "select" && <Toggle id="auto_select" />}
        {tool === "pick_color" && <Toggle id="global" />}

        {(tool === "brush" || tool === "pencil") && (
          <>
            <Num id="size" label="Size:" max={200} />
            <Toggle id="pressure" />
          </>
        )}

        {tool === "erase" && (
          <>
            <Num id="size" label="Size:" />
            <Toggle id="circle" />
            <Toggle id="strict" />
          </>
        )}

        {(tool === "magic_erase" || tool === "fill") && (
          <>
            <Num id="power" label="Power:" min={1} max={100} />
            <Toggle id="anti_aliasing" />
            <Toggle id="contiguous" />
          </>
        )}

        {tool === "media" && <Num id="size" label="Size:" />}

        {tool === "text" && (
          <>
            <Select id="font" label="Font:" options={FONTS.map((f) => ({ value: f, label: f }))} />
            <Num id="size" label="Size:" />
            <ColorIn id="fill" label="Fill:" />
            <ColorIn id="stroke" label="Stroke:" />
            <Num id="stroke_size" label="Stroke size:" min={0} />
            <Num id="kerning" label="Kerning:" min={-100} max={100} />
            <Num id="leading" label="Leading:" min={-100} max={100} />
          </>
        )}

        {tool === "gradient" && (
          <>
            <ColorIn id="color_1" label="Color 1:" />
            <ColorIn id="color_2" label="Color 2:" />
            <Num id="alpha" label="Alpha:" />
            <Toggle id="radial" />
            <Num id="radial_power" label="Radial power:" min={1} max={100} />
          </>
        )}

        {tool === "clone" && (
          <>
            <Num id="size" label="Size:" />
            <Toggle id="anti_aliasing" />
            <Select
              id="source_layer"
              label="Source layer:"
              options={[
                { value: "Current", label: "Current" },
                { value: "Previous", label: "Previous" },
              ]}
            />
          </>
        )}

        {tool === "shape" && (
          <>
            <Num id="size" label="Size:" />
            <ColorIn id="stroke" label="Stroke:" />
          </>
        )}

        {tool === "crop" && <span className="mp-attr">Crop</span>}

        {tool === "blur" && (
          <>
            <Num id="size" label="Size:" />
            <Num id="strength" label="Strength:" min={1} max={100} />
          </>
        )}

        {tool === "sharpen" && <Num id="size" label="Size:" />}

        {tool === "desaturate" && (
          <>
            <Num id="size" label="Size:" />
            <Toggle id="anti_aliasing" />
          </>
        )}

        {tool === "bulge_pinch" && (
          <>
            <Num id="radius" label="Radius:" />
            <Num id="power" label="Power:" min={1} max={100} />
            <Toggle id="bulge" />
          </>
        )}

        {tool === "animation" && (
          <>
            <Toggle id="play" />
            <Num id="delay" label="Delay:" />
          </>
        )}
      </div>
    </div>
  );
}
