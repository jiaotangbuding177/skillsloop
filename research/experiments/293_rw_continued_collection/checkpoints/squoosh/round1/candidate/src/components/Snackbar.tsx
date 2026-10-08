import { useEffect, useRef, useState } from "react";

export type SnackOptions = {
  /** Optional trailing action label, e.g. "DISMISS". */
  action?: string;
};

type Snack = {
  message: string;
  action?: string;
  key: number;
};

/**
 * Imperative snackbar controller. Mirrors the reference's bottom-centre
 * toast with an optional green action button.
 */
export function useSnackbar(duration = 5000) {
  const [snack, setSnack] = useState<Snack | null>(null);
  const [hiding, setHiding] = useState(false);
  const timer = useRef<number | undefined>(undefined);
  const key = useRef(0);

  const clear = () => {
    if (timer.current) window.clearTimeout(timer.current);
  };

  const dismiss = () => {
    clear();
    setHiding(true);
    timer.current = window.setTimeout(() => {
      setSnack(null);
      setHiding(false);
    }, 300);
  };

  const show = (message: string, _options: SnackOptions = {}) => {
    clear();
    key.current += 1;
    setHiding(false);
    setSnack({ message, key: key.current });
    timer.current = window.setTimeout(dismiss, duration);
  };

  useEffect(() => clear, []);

  const node = snack ? (
    <div
      className={`snackbar${hiding ? " hiding" : ""}`}
      role="status"
      aria-live="polite"
    >
      <div className="snackbar-text">{snack.message}</div>
      <button className="snackbar-action" type="button" onClick={dismiss}>
        Dismiss
      </button>
    </div>
  ) : null;

  return { show, node };
}
