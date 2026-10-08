import { useEffect, useMemo, useState, type ReactNode } from "react";
import type { EditorApi } from "@/editor/useEditor";
import type { FieldDef } from "@/editor/types";
import { ABOUT_ROWS, LAYOUTS, RESOLUTIONS, SHORTCUTS } from "@/editor/data";
import { LogoBadge } from "./LogoBadge";

export function DialogHost({ editor }: { editor: EditorApi }) {
  const d = editor.dialog;
  if (!d) return null;
  return (
    <div className="mp-overlay" onMouseDown={(e) => e.target === e.currentTarget && editor.closeDialog()}>
      <DialogFrame title={d.title} onClose={editor.closeDialog}>
        {d.kind === "about" && <AboutBody />}
        {d.kind === "new" && <NewFileBody editor={editor} />}
        {d.kind === "settings" && <SettingsBody editor={editor} />}
        {d.kind === "shortcuts" && <ShortcutsBody />}
        {d.kind === "form" && <FormBody editor={editor} fields={d.fields ?? []} action={d.action} />}
      </DialogFrame>
    </div>
  );
}

function DialogFrame({ title, onClose, children }: { title: string; onClose: () => void; children: ReactNode }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className="mp-dialog" role="dialog" aria-modal="true" aria-label={title}>
      <header>
        <h2>{title}</h2>
        <button type="button" className="mp-dialog-close" aria-label="Close" onClick={onClose}>
          &times;
        </button>
      </header>
      <div className="mp-dialog-body">{children}</div>
    </div>
  );
}

function AboutBody() {
  return (
    <div className="mp-about-body">
      <LogoBadge size={72} />
      <table>
        <tbody>
          {ABOUT_ROWS.map(([label, value]) => (
            <tr key={label}>
              <th scope="row">{label}</th>
              <td>
                {label === "Email:" ? (
                  <a href="mailto:www.viliusl@gmail.com">{value}</a>
                ) : label === "GitHub:" ? (
                  <a href="https://github.com/viliusle/miniPaint">{value}</a>
                ) : label === "Website:" ? (
                  <a href="https://viliusle.github.io/miniPaint/">{value}</a>
                ) : (
                  value
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <footer>
        <button type="button" className="mp-dialog-btn primary">Ok</button>
      </footer>
    </div>
  );
}

function NewFileBody({ editor }: { editor: EditorApi }) {
  const [w, setW] = useState(editor.width);
  const [h, setH] = useState(editor.height);
  const [preset, setPreset] = useState("custom");
  const [layout, setLayout] = useState("custom");
  const [transparent, setTransparent] = useState(false);
  const [locked, setLocked] = useState(true);
  const ratio = useMemo(() => w / Math.max(1, h), [w, h]);

  const applyPreset = (value: string) => {
    setPreset(value);
    const r = RESOLUTIONS.find((x) => x.value === value);
    if (r && value !== "custom") {
      setW(r.w);
      setH(r.h);
    }
  };
  const applyLayout = (value: string) => {
    setLayout(value);
    if (value === "landscape" && w < h) {
      setW(h);
      setH(w);
    } else if (value === "portrait" && w > h) {
      setW(h);
      setH(w);
    }
  };

  return (
    <>
      <table>
        <tbody>
          <tr>
            <th scope="row">Width:</th>
            <td>
              <div className="mp-dialog-num-row">
                <input
                  type="number"
                  className="mp-dialog-num"
                  aria-label="Width:"
                  value={w}
                  onChange={(e) => {
                    const v = parseInt(e.target.value, 10) || 1;
                    setW(v);
                    setPreset("custom");
                    if (locked) setH(Math.round(v / ratio));
                  }}
                />
                <span className="mp-inline-note">pixels</span>
              </div>
            </td>
          </tr>
          <tr>
            <th scope="row">Height:</th>
            <td>
              <div className="mp-dialog-num-row">
                <input
                  type="number"
                  className="mp-dialog-num"
                  aria-label="Height:"
                  value={h}
                  onChange={(e) => {
                    const v = parseInt(e.target.value, 10) || 1;
                    setH(v);
                    setPreset("custom");
                    if (locked) setW(Math.round(v * ratio));
                  }}
                />
                <span className="mp-inline-note">pixels</span>
              </div>
            </td>
          </tr>
          <tr>
            <th scope="row">Resolution:</th>
            <td>
              <div className="mp-scroll-box mp-radio-group" role="radiogroup" aria-label="Resolution:">
                {RESOLUTIONS.map((r) => (
                  <label key={r.value}>
                    <input
                      type="radio"
                      name="resolution"
                      value={r.value}
                      checked={preset === r.value}
                      onChange={() => applyPreset(r.value)}
                    />
                    {r.label}
                  </label>
                ))}
              </div>
            </td>
          </tr>
          <tr>
            <th scope="row">Layout:</th>
            <td>
              <div className="mp-radio-group bordered" role="radiogroup" aria-label="Layout:">
                {LAYOUTS.map((l) => (
                  <label key={l.value}>
                    <input
                      type="radio"
                      name="layout"
                      value={l.value}
                      checked={layout === l.value}
                      onChange={() => applyLayout(l.value)}
                    />
                    {l.label}
                  </label>
                ))}
              </div>
            </td>
          </tr>
          <tr>
            <th scope="row">Transparent:</th>
            <td>
              <input
                type="checkbox"
                aria-label="Toggle"
                checked={transparent}
                onChange={(e) => setTransparent(e.target.checked)}
              />
            </td>
          </tr>
        </tbody>
      </table>
      <footer>
        <button
          type="button"
          className="mp-dialog-btn"
          onClick={() => {
            editor.newDocument(w, h);
            editor.closeDialog();
          }}
        >
          Ok
        </button>
        <button type="button" className="mp-dialog-btn" onClick={editor.closeDialog}>
          Cancel
        </button>
      </footer>
    </>
  );
}

function SettingsBody({ editor }: { editor: EditorApi }) {
  const [transparent, setTransparent] = useState(false);
  const [bg, setBg] = useState("squares");
  const [theme, setTheme] = useState("dark");
  const [units, setUnits] = useState("pixels");
  const [resolution, setResolution] = useState(editor.resolution);
  const [snap, setSnap] = useState(true);
  const [guides, setGuides] = useState(true);
  const [safe, setSafe] = useState(true);
  const [exit, setExit] = useState(true);
  const [thick, setThick] = useState(false);
  const [autoresize, setAutoresize] = useState(true);

  const row = (label: string, control: ReactNode) => (
    <tr>
      <th scope="row">{label}</th>
      <td>{control}</td>
    </tr>
  );
  const toggle = (checked: boolean, set: (v: boolean) => void) => (
    <input type="checkbox" aria-label="Toggle" checked={checked} onChange={(e) => set(e.target.checked)} />
  );
  const select = (value: string, set: (v: string) => void, options: string[]) => (
    <select value={value} onChange={(e) => set(e.target.value)}>
      {options.map((o) => (
        <option key={o} value={o}>
          {o}
        </option>
      ))}
    </select>
  );

  return (
    <>
      <table>
        <tbody>
          {row("Transparent:", toggle(transparent, setTransparent))}
          {row("Transparency background:", select(bg, setBg, ["squares", "green", "grey"]))}
          {row("Theme", select(theme, setTheme, ["dark", "light", "green"]))}
          {row("Units", select(units, setUnits, ["pixels", "inches", "centimeters", "millimetres"]))}
          {row("Resolution:", select(resolution, setResolution, ["72", "150", "300", "600"]))}
          {row("Enable snap:", toggle(snap, setSnap))}
          {row("Enable guides:", toggle(guides, setGuides))}
          {row("Safe search:", toggle(safe, setSafe))}
          {row("Exit confirmation:", toggle(exit, setExit))}
          {row("Thick guides:", toggle(thick, setThick))}
          {row("Enable autoresize:", toggle(autoresize, setAutoresize))}
        </tbody>
      </table>
      <footer>
        <button
          type="button"
          className="mp-dialog-btn"
          onClick={() => {
            editor.setResolution(resolution);
            editor.closeDialog();
          }}
        >
          Ok
        </button>
        <button type="button" className="mp-dialog-btn" onClick={editor.closeDialog}>
          Cancel
        </button>
      </footer>
    </>
  );
}

function ShortcutsBody() {
  return (
    <>
      <table>
        <tbody>
          {SHORTCUTS.map((s) => (
            <tr key={s.label}>
              <th scope="row">{s.key}</th>
              <td>{s.label}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <footer>
        <button type="button" className="mp-dialog-btn primary">Ok</button>
      </footer>
    </>
  );
}

function FormBody({
  editor,
  fields,
  action,
}: {
  editor: EditorApi;
  fields: FieldDef[];
  action?: string;
}) {
  const [values, setValues] = useState<Record<string, string | number | boolean>>(() => {
    const v: Record<string, string | number | boolean> = {};
    fields.forEach((f) => (v[f.name] = f.value ?? (f.type === "checkbox" ? false : "")));
    return v;
  });

  const set = (name: string, value: string | number | boolean) => setValues((s) => ({ ...s, [name]: value }));

  const submit = () => {
    if (action === "resize") {
      editor.resize(Number(values.width) || editor.width, Number(values.height) || editor.height);
    } else if (action === "rotate") {
      editor.rotate(Number(values.angle) || 90);
    } else if (action === "canvas_size") {
      editor.resize(Number(values.width) || editor.width, Number(values.height) || editor.height);
    } else {
      editor.setStatus(`${editor.dialog?.title?.replace(" ...", "") ?? "Done"}`);
    }
    editor.closeDialog();
  };

  return (
    <>
      <table>
        <tbody>
          {fields.map((f) => (
            <tr key={f.name}>
              <th scope="row">{f.label}</th>
              <td>
                {f.type === "number" && (
                  <input
                    type="number"
                    aria-label={f.label}
                    value={Number(values[f.name]) || 0}
                    min={f.min}
                    max={f.max}
                    onChange={(e) => set(f.name, parseInt(e.target.value, 10) || 0)}
                  />
                )}
                {f.type === "text" && (
                  <input
                    type="text"
                    aria-label={f.label}
                    value={String(values[f.name])}
                    onChange={(e) => set(f.name, e.target.value)}
                  />
                )}
                {f.type === "color" && (
                  <input
                    type="color"
                    aria-label={f.label}
                    value={String(values[f.name])}
                    onChange={(e) => set(f.name, e.target.value)}
                  />
                )}
                {f.type === "checkbox" && (
                  <input
                    type="checkbox"
                    aria-label="Toggle"
                    checked={Boolean(values[f.name])}
                    onChange={(e) => set(f.name, e.target.checked)}
                  />
                )}
                {f.type === "select" && (
                  <select
                    aria-label={f.label}
                    value={String(values[f.name])}
                    onChange={(e) => set(f.name, e.target.value)}
                  >
                    {(f.options ?? []).map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                )}
                {f.type === "radio" && (
                  <div className="mp-radio-group bordered" role="radiogroup" aria-label={f.label}>
                    {(f.options ?? []).map((o) => (
                      <label key={o.value}>
                        <input
                          type="radio"
                          name={f.name}
                          checked={values[f.name] === o.value}
                          onChange={() => set(f.name, o.value)}
                        />
                        {o.label}
                      </label>
                    ))}
                  </div>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <footer>
        <button type="button" className="mp-dialog-btn" onClick={submit}>
          Ok
        </button>
        <button type="button" className="mp-dialog-btn" onClick={editor.closeDialog}>
          Cancel
        </button>
      </footer>
    </>
  );
}
