interface Props {
  id?: string;
  value: number;
  min?: number;
  max?: number;
  step?: number;
  ariaLabel?: string;
  disabled?: boolean;
  onChange: (value: number) => void;
}

/** Text field with an up/down spinner, matching the editor house style. */
export function NumberInput({ id, value, min, max, step = 1, ariaLabel, disabled, onChange }: Props) {
  const clamp = (v: number) => {
    if (min !== undefined && v < min) return min;
    if (max !== undefined && v > max) return max;
    return v;
  };
  const bump = (dir: 1 | -1) => {
    const next = clamp((Number.isFinite(value) ? value : 0) + dir * step);
    onChange(next);
  };
  return (
    <div className="mp-number">
      <input
        id={id}
        type="number"
        aria-label={ariaLabel}
        value={Number.isFinite(value) ? value : ""}
        disabled={disabled}
        min={min}
        max={max}
        step={step}
        onChange={(e) => {
          const v = parseFloat(e.target.value);
          if (!Number.isNaN(v)) onChange(clamp(v));
        }}
      />
      <button type="button" className="mp-spin up" onClick={() => bump(1)} aria-label="Increase" disabled={disabled}>
        <span aria-hidden="true">&#9650;</span>
      </button>
      <button type="button" className="mp-spin down" onClick={() => bump(-1)} aria-label="Decrease" disabled={disabled}>
        <span aria-hidden="true">&#9660;</span>
      </button>
    </div>
  );
}
