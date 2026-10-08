import { useCallback, useEffect, useState } from "react";

export const EDITOR_PATH = "/editor";

/** True when the bundle is opened straight from disk rather than a server. */
const fileProtocol =
  typeof window !== "undefined" && window.location.protocol === "file:";

function currentPath(): string {
  if (fileProtocol) {
    // Derive a path from the hash so navigation still works offline.
    const hash = window.location.hash.replace(/^#/, "");
    return hash || "/";
  }
  return window.location.pathname;
}

/**
 * Minimal history-based router. Keeps the real URL paths (`/`, `/editor`)
 * instead of hash routing whenever the page is served over http(s).
 */
export function useRoute() {
  const [path, setPath] = useState<string>(currentPath);

  useEffect(() => {
    const sync = () => setPath(currentPath());
    window.addEventListener("popstate", sync);
    window.addEventListener("hashchange", sync);
    return () => {
      window.removeEventListener("popstate", sync);
      window.removeEventListener("hashchange", sync);
    };
  }, []);

  const navigate = useCallback((next: string) => {
    if (fileProtocol) {
      window.location.hash = next;
      setPath(next);
      return;
    }
    const url = new URL(window.location.href);
    url.pathname = next;
    window.history.pushState(null, "", url.href);
    setPath(next);
  }, []);

  return { path, navigate };
}
