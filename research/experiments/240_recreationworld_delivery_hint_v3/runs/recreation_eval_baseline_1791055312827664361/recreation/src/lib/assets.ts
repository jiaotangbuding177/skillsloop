/**
 * Resolves the logical "/media/<file>" paths used across the content data to
 * bundled asset URLs. Vite processes each import at build time so the whole
 * bundle (including imagery) can ship as one self-contained document.
 */

const modules = import.meta.glob<string>(
  "../assets/media/**/*.{jpg,jpeg,png,svg}",
  { eager: true, query: "?url", import: "default" },
);

const byName = new Map<string, string>();
for (const [key, url] of Object.entries(modules)) {
  const name = key.split("/").pop()!;
  byName.set(name, url);
}

export function media(path: string | undefined | null): string {
  if (!path) return "";
  if (/^(https?:|data:)/.test(path)) return path;
  const name = path.split("/").pop()!;
  return byName.get(name) ?? path;
}

export const LOGO = media("/media/umich-logo.png");
