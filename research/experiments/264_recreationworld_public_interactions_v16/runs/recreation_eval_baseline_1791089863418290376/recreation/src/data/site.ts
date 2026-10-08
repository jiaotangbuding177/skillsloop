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

export type QuickLink = [label: string, to: string];

/**
 * Per-route chrome. The offline reference varies the search label, the
 * misconduct-report label, the quick-links panel title and the main menu
 * navigation landmark name from page to page; these are reproduced here.
 */
export type RouteChrome = {
  skip: string;
  report: string;
  searchLabel: string;
  /** Visible label on the header search submit control; defaults to "Search". */
  searchButton?: string;
  quickTitle: string;
  quick: QuickLink[];
  menuLabel: string;
  audienceLabel: string;
};

const quickBase: Record<string, QuickLink> = {
  calendar: ["Academic Calendar", "/_404.html"],
  courses: ["Courses", "/_404.html"],
  semester: ["Semester Calendar", "/_404.html"],
  directory: ["Directory", "/_404.html"],
  email: ["Email", "/_404.html"],
  library: ["Library Catalog", "/_404.html"],
  maps: ["Maps & Directions", "/_404.html"],
  schools: ["Schools & Colleges", "/schools-colleges/"],
};

function quick(
  calendar: QuickLink,
  portal: QuickLink | null,
  email2: QuickLink | null,
  access: QuickLink,
  extras: QuickLink[] = []
): QuickLink[] {
  return [
    calendar,
    ...(portal ? [portal] : []),
    quickBase.directory,
    quickBase.email,
    ...(email2 ? [email2] : []),
    quickBase.library,
    quickBase.maps,
    quickBase.schools,
    ...extras,
    access,
  ];
}

const HOME_CHROME: RouteChrome = {
  skip: "Skip to main content",
  report: "Report Sexual Misconduct, Discrimination, and Bias Concerns",
  searchLabel: "Search for:",
  quickTitle: "Quick Links",
  quick: [
    quickBase.calendar,
    quickBase.courses,
    quickBase.directory,
    quickBase.email,
    ["Health Email", "/_404.html"],
    quickBase.library,
    quickBase.maps,
    quickBase.schools,
    ["Corravale Access", "/_404.html"],
  ],
  menuLabel: "Main Menu",
  audienceLabel: "Audiences",
};

export const routeChrome: Record<string, RouteChrome> = {
  "/": HOME_CHROME,
  "/schools-colleges": {
    skip: "Skip primary navigation",
    report: "Report Misconduct, Discrimination, Bias and Harassment",
    searchLabel: "Search for:",
    quickTitle: "Quick Links",
    quick: quick(quickBase.calendar, ["Portal", "/_404.html"], ["Email — CHS", "/_404.html"], ["Student Access", "/_404.html"]),
    menuLabel: "Main Menu",
    audienceLabel: "Audiences",
  },
  "/about": {
    skip: "Skip global navigation",
    report: "Report Sexual Misconduct, Discrimination, and Harassment",
    searchLabel: "Search for:",
    quickTitle: "Quick Links",
    quick: quick(quickBase.calendar, ["Studio", "/_404.html"], ["Email — CHS", "/_404.html"], ["Wingspan Access", "/_404.html"]),
    menuLabel: "Main Menu",
    audienceLabel: "Audiences",
  },
  "/academics": {
    skip: "Jump past site navigation",
    report: "Report Misconduct, Bias, Discrimination and Harassment",
    searchLabel: "Search for:",
    quickTitle: "Quick Links",
    quick: quick(quickBase.calendar, ["Portal", "/_404.html"], ["Email — CHS", "/_404.html"], ["Corravale Access", "/_404.html"]),
    menuLabel: "Main Menu",
    audienceLabel: "Visitors",
  },
  "/life-at-michigan": {
    skip: "Skip primary navigation",
    report: "Report Misconduct, Discrimination, and Bias Incidents",
    searchLabel: "Search site:",
    quickTitle: "Handy Links",
    quick: quick(quickBase.semester, ["Coursly", "/_404.html"], ["Email — CUMC", "/_404.html"], ["Sentinel Access", "/_404.html"]),
    menuLabel: "Site Menu",
    audienceLabel: "Audiences",
  },
  "/athletics": {
    skip: "Jump to main navigation",
    report: "Report Misconduct, Bias, Discrimination and Harassment",
    searchLabel: "Find pages:",
    quickTitle: "Handy Links",
    quick: quick(["Academic Schedule", "/_404.html"], ["Portal", "/_404.html"], ["Email — CHS", "/_404.html"], ["Corravale Access", "/_404.html"]),
    menuLabel: "Main Menu",
    audienceLabel: "Audiences",
  },
  "/research": {
    skip: "Skip global navigation",
    report: "Report Misconduct, Discrimination and Harassment Concerns",
    searchLabel: "Search for:",
    quickTitle: "Quick Links",
    quick: quick(quickBase.calendar, ["Portal", "/_404.html"], ["Email — CMED", "/_404.html"], ["Corravale Access", "/_404.html"]),
    menuLabel: "Main Menu",
    audienceLabel: "Audiences",
  },
  "/health-medicine": {
    skip: "Jump past main navigation",
    report: "Report Misconduct, Discrimination and Bias Incidents",
    searchLabel: "Search here:",
    quickTitle: "Handy Links",
    quick: quick(quickBase.calendar, ["Nexus", "/_404.html"], ["Email — CHS", "/_404.html"], ["Corravale Access", "/_404.html"]),
    menuLabel: "Main Menu",
    audienceLabel: "Audiences",
  },
  "/initiatives": {
    skip: "Skip global navigation",
    report: "Report Sexual Misconduct, Discrimination and Harassment",
    searchLabel: "Search for:",
    quickTitle: "Quick Links",
    quick: quick(quickBase.calendar, ["Learn", "/_404.html"], ["Email — Med", "/_404.html"], ["Corravale Access", "/_404.html"]),
    menuLabel: "Main Menu",
    audienceLabel: "Audiences",
  },
  "/giving": {
    skip: "Skip primary navigation",
    report: "Report Misconduct, Bias, Discrimination and Harassment",
    searchLabel: "Search here:",
    searchButton: "Lookup",
    quickTitle: "Handy Links",
    quick: quick(quickBase.semester, ["Portal", "/_404.html"], ["Email — CUHS", "/_404.html"], ["Corravale Access", "/_404.html"], [["People Hub", "/_404.html"]]),
    menuLabel: "Site Menu",
    audienceLabel: "Audiences",
  },
  "/prospective-students": {
    skip: "Skip to main navigation",
    report: "Report Misconduct, Discrimination, and Harassment Concerns",
    searchLabel: "Search here:",
    quickTitle: "Quick Access",
    quick: quick(quickBase.calendar, null, ["Email — CHS", "/_404.html"], ["Corravale Access", "/_404.html"], [quickBase.courses]),
    menuLabel: "Site Menu",
    audienceLabel: "Audiences",
  },
  "/current-students": {
    skip: "Skip primary navigation",
    report: "Report Misconduct, Discrimination, Bias and Harassment",
    searchLabel: "Search site:",
    quickTitle: "Quick Access",
    quick: quick(quickBase.calendar, ["Nimbus", "/_404.html"], ["Email — CVHS", "/_404.html"], ["Corravale Access", "/_404.html"]),
    menuLabel: "Main Menu",
    audienceLabel: "Audiences",
  },
  "/faculty-staff": {
    skip: "Skip to primary content",
    report: "Report Misconduct, Bias, Discrimination and Harassment",
    searchLabel: "Find pages:",
    quickTitle: "Quick Links",
    quick: quick(quickBase.calendar, ["Portal", "/_404.html"], ["Email — CHS", "/_404.html"], ["Corravale Access", "/_404.html"]),
    menuLabel: "Main Menu",
    audienceLabel: "Audiences",
  },
  "/parents": {
    skip: "Skip main navigation",
    report: "Report Misconduct, Discrimination, and Harassment Concerns",
    searchLabel: "Search here:",
    quickTitle: "Handy Links",
    quick: quick(["Academic Schedule", "/_404.html"], ["Nexus", "/_404.html"], ["Email — CHS", "/_404.html"], ["Ridgeback Access", "/_404.html"]),
    menuLabel: "Site Menu",
    audienceLabel: "Audiences",
  },
  "/alumni": {
    skip: "Skip global navigation",
    report: "Report Sexual Misconduct, Discrimination and Harassment",
    searchLabel: "Search for:",
    quickTitle: "Quick Links",
    quick: quick(quickBase.calendar, ["MyVale", "/_404.html"], ["Email — CVMC", "/_404.html"], ["Voyager Access", "/_404.html"]),
    menuLabel: "Main Menu",
    audienceLabel: "Audiences",
  },
  "/fact-figures-alias": HOME_CHROME,
  "/facts-figures": {
    skip: "Skip global navigation",
    report: "Report Sexual Misconduct, Discrimination and Harassment",
    searchLabel: "Search for:",
    quickTitle: "Quick Links",
    quick: quick(quickBase.calendar, ["Portal", "/_404.html"], ["Email — CHS", "/_404.html"], ["Corravale Access", "/_404.html"]),
    menuLabel: "Main Menu",
    audienceLabel: "Audiences",
  },
  "/contact": {
    skip: "Skip to primary content",
    report: "Report Misconduct, Bias Incidents and Harassment Here",
    searchLabel: "Find pages:",
    searchButton: "Lookup",
    quickTitle: "Handy Links",
    quick: quick(quickBase.semester, ["Beacon", "/_404.html"], ["Email — CMed", "/_404.html"], ["Ridgeback Access", "/_404.html"]),
    menuLabel: "Site Menu",
    audienceLabel: "Audiences",
  },
  "/search": {
    skip: "Bypass global navigation",
    report: "Report Misconduct, Bias, Discrimination, and Harassment",
    searchLabel: "Search for:",
    quickTitle: "Quick Links",
    quick: HOME_CHROME.quick,
    menuLabel: "Main Menu",
    audienceLabel: "Audiences",
  },
  "/about/privacy": {
    skip: "Skip global navigation",
    report: "Report Sexual Misconduct, Discrimination and Harassment",
    searchLabel: "Search for:",
    quickTitle: "Quick Links",
    quick: quick(quickBase.calendar, ["Portal", "/_404.html"], ["Email — Med", "/_404.html"], ["Corravale Access", "/_404.html"]),
    menuLabel: "Main Menu",
    audienceLabel: "Audiences",
  },
  "/about/privacy-statement": {
    skip: "Skip global navigation",
    report: "Report Sexual Misconduct, Discrimination or Harassment",
    searchLabel: "Search for:",
    quickTitle: "Quick Links",
    quick: quick(quickBase.calendar, ["Learn", "/_404.html"], ["Email — CHS", "/_404.html"], ["Corravale Access", "/_404.html"]),
    menuLabel: "Main Menu",
    audienceLabel: "Audiences",
  },
};

export function chromeFor(path: string): RouteChrome {
  // Callers pass a trailing-slash route ("/about/"); the table is keyed
  // without it, so normalize before looking up.
  const key = path.length > 1 && path.endsWith("/") ? path.slice(0, -1) : path;
  return routeChrome[key] ?? HOME_CHROME;
}

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
