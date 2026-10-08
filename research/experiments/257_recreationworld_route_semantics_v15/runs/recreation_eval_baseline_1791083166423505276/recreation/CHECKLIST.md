# Observed public interactions checklist

All entries below were observed on http://localhost:33615 with ordinary
navigation, clicks, and accessibility snapshots.

## Header / chrome (varies per route)
- Skip link text differs per route (e.g. "Skip to main content", "Skip global navigation",
  "Skip primary navigation", "Jump past site navigation", "Skip to primary content",
  "Skip main navigation", "Skip to main navigation", "Jump to main navigation",
  "Jump past main navigation", "Bypass global navigation").
- Report link text differs per route; destination always /_404.html.
- Header search landmark labeled per route ("Search for:", "Search site:", "Search here:",
  "Find pages:"); submit button accessible name "Search" usually, "Lookup" on /giving/ and /contact/.
- Quick Links panel title varies ("Quick Links", "Handy Links", "Quick Access"); panel is a nav
  landmark with a per-route list; "Schools & Colleges" entry -> /schools-colleges/, others -> /_404.html.
- Audiences nav landmark labeled "Audiences" (or "Visitors" on /academics/): For: + 5 audience links.
- Main menu landmark "Main Menu" (or "Site Menu" on life/giving/prospective/parents/contact);
  9 items; Home is icon w/ "Home" text. Items route to real paths.

## Behaviors
- Header search submit navigates to /search/?keywords=<q>; the /search/ page itself has a
  Keywords field + Search button and no visible results.
- Every observed "unavailable" destination (external sites, backend tools) navigates to /_404.html,
  which renders the offline notice page (title "Page Not Available - Offline Mode").
- /_404.html renders with a bare gray page (no header/footer chrome).
- /about/privacy/ has anchor /about/privacy/#choices.
- Footer: "Our Campuses" nav (Fairhaven -> /, Westgate/Alden -> /_404.html), © line,
  Privacy Notice -> /about/privacy/, tel link, Contact us -> /contact/,
  Careers -> /_404.html, Social Feeds -> /_404.html each,
  Regulatory badges -> /_404.html.

## Routes discovered
/ , /about/ , /academics/ , /life-at-michigan/ , /athletics/ , /research/ ,
/health-medicine/ , /initiatives/ , /giving/ , /prospective-students/ ,
/current-students/ , /faculty-staff/ , /parents/ , /alumni/ , /schools-colleges/ ,
/facts-figures/ , /contact/ , /search/ , /about/privacy/ , /_404.html
