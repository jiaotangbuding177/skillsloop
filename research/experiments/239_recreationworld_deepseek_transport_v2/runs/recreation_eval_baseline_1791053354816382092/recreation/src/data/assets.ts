// Bundles every downloaded media file and exposes a lookup keyed by the
// original reference path (e.g. "/_images/abc.jpg").
const modules = import.meta.glob("../assets/media/**/*.{jpg,jpeg,png,svg}", {
  eager: true,
  query: "?url",
  import: "default",
}) as Record<string, string>;

const byPath: Record<string, string> = {};
for (const [key, url] of Object.entries(modules)) {
  // ../assets/media/_images/x.jpg -> /_images/x.jpg
  const rel = key.replace("../assets/media", "");
  byPath[rel] = url;
  byPath[rel.replace(/^\/media\//, "/")] = url;
}

/** Resolve a reference media path to a bundled URL. */
export function asset(path: string | undefined | null): string {
  if (!path) return "";
  const clean = path.split("?")[0];
  if (byPath[clean]) return byPath[clean];
  // fall back: strip a leading /assets/media or /media duplication
  const alt = clean.replace(/^\/media\//, "/");
  if (byPath[alt]) return byPath[alt];
  return clean;
}
