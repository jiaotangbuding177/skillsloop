export const siteName = "Corravale University";

export type NavItem = { label: string; to: string };

export const mainMenu: NavItem[] = [
  { label: "Home", to: "/" },
  { label: "About", to: "/about/" },
  { label: "Academics", to: "/academics/" },
  { label: "Life at Corravale", to: "/life-at-michigan/" },
  { label: "Athletics", to: "/athletics/" },
  { label: "Research", to: "/research/" },
  { label: "Health & Medicine", to: "/health-medicine/" },
  { label: "Initiatives", to: "/initiatives/" },
  { label: "Giving", to: "/giving/" },
];

export const audiences: NavItem[] = [
  { label: "Prospective Students", to: "/prospective-students/" },
  { label: "Current Students", to: "/current-students/" },
  { label: "Faculty & Staff", to: "/faculty-staff/" },
  { label: "Parents", to: "/parents/" },
  { label: "Alumni", to: "/alumni/" },
];

export const quickLinks: [label: string, to: string][] = [
  ["Academic Calendar", "/_404.html"],
  ["Courses", "/_404.html"],
  ["Directory", "/_404.html"],
  ["Email", "/_404.html"],
  ["Health Email", "/_404.html"],
  ["Library Catalog", "/_404.html"],
  ["Maps & Directions", "/_404.html"],
  ["Schools & Colleges", "/schools-colleges/"],
  ["Corravale Access", "/_404.html"],
];

export const footerCampuses = [
  { label: "Fairhaven", to: "/" },
  { label: "Westgate", to: "/_404.html" },
  { label: "Alden", to: "/_404.html" },
];

export const socialFeeds = [
  { label: "Streamly", icon: "streamly" },
  { label: "Z", icon: "z" },
  { label: "Skylark", icon: "skylark" },
  { label: "Vidcast", icon: "vidcast" },
  { label: "Photogram", icon: "photogram" },
  { label: "Loopit", icon: "loopit" },
  { label: "Careerly", icon: "careerly" },
];

export type LinkGroup = { heading: string; links: { label: string; to: string; note?: string }[] };
