import { cn } from "@/utils/cn";

type Props = {
  checked: boolean;
  onChange: (next: boolean) => void;
  label: string;
  /** Form field name, mirroring the reference's setting keys. */
  name?: string;
  /** Optional class for the outer wrapper. */
  className?: string;
};

/** Pill switch matching the reference's black track / pink thumb control. */
export function Toggle({ checked, onChange, label, name, className }: Props) {
  return (
    <span className={cn("switch", className)}>
      <input
        type="checkbox"
        name={name}
        checked={checked}
        aria-label={label}
        onChange={(e) => onChange(e.target.checked)}
      />
      <span className="track">
        <span className="thumb-track">
          <span className="thumb" />
        </span>
      </span>
    </span>
  );
}
