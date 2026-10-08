export interface NavItem {
  k: "a" | "d";
  href?: string;
  label: string;
  children?: string[];
}

export interface NavBlock {
  title: string;
  extraTitles?: string[];
  items: NavItem[];
  paras?: string[];
}

export interface ContentPageData {
  route: string;
  title: string;
  description: string;
  blocks: NavBlock[];
  secondaryBlocks?: NavBlock[];
  featureImg: string;
  caption: string;
  captionLink?: { href: string; label: string } | null;
  sharingImg: string;
  sharingCaption: string;
}

import pagesData from "../data/pages.json";
import homeData from "../data/home.json";
import galleryData from "../data/gallery.json";

export const pages = pagesData as unknown as Record<string, ContentPageData>;

export const home = homeData as unknown as {
  features: { title: string; body: string; link: string; href: string; bg: string; cloned: string }[];
  infographics: { cls: string; href: string; hidden: string; span: string }[];
  news: [string, string][];
  videos: { title: string; img: string; alt: string }[];
};

export const gallery = galleryData as unknown as { alt: string; img: string; time: string }[];

export const QUICK_LINKS = [
  "Academic Calendar",
  "Courses",
  "Directory",
  "Email",
  "Health Email",
  "Library Catalog",
  "Maps & Directions",
  "Schools & Colleges",
  "Corravale Access",
];

export const AUDIENCES = [
  { label: "Prospective Students", href: "/prospective-students/" },
  { label: "Current Students", href: "/current-students/" },
  { label: "Faculty & Staff", href: "/faculty-staff/" },
  { label: "Parents", href: "/parents/" },
  { label: "Alumni", href: "/alumni/" },
];

export const MAIN_NAV = [
  { label: "Home", href: "/", icon: "home" },
  { label: "About", href: "/about/" },
  { label: "Academics", href: "/academics/" },
  { label: "Life at Corravale", href: "/life-at-michigan/" },
  { label: "Athletics", href: "/athletics/" },
  { label: "Research", href: "/research/" },
  { label: "Health & Medicine", href: "/health-medicine/" },
  { label: "Initiatives", href: "/initiatives/" },
  { label: "Giving", href: "/giving/" },
];

export const MEDIA_URL = (p: string) => (p.startsWith("media/") ? p : p.replace(/^\/media\//, "media/"));

export function resolveMedia(src: string): string {
  if (!src) return "";
  if (src.startsWith("/_images/")) return "media/" + src.replace("/_images/", "");
  if (src.startsWith("/includes/panels/gallery/images/")) return "media/panels/" + src.replace("/includes/panels/gallery/images/", "");
  if (src.startsWith("/media/images/sidebar-images/")) {
    const b = src.replace("/media/images/sidebar-images/", "");
    return "media/ui-" + b;
  }
  if (src.startsWith("/skins/um2013/media/images/")) return "media/" + src.replace("/skins/um2013/media/images/", "");
  return src.replace(/^\//, "");
}

export const CONTACT_EMAIL = "corravale@corravale.edu";
