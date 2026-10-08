# Public Behavior Checklist — Corravale University rebuild

Reference: http://localhost:38381 (offline). Candidate: http://localhost:4173 (single-file build).

## Route inventory (discovered by following internal links from `/`)
| Route | Renders? | Candidate route |
|---|---|---|
| `/` | yes | HomePage |
| `/about/` | yes | AboutPage |
| `/academics/` | yes | AcademicsPage |
| `/life-at-michigan/` | yes | LifePage |
| `/athletics/` | yes | AthleticsPage |
| `/research/` | yes | ResearchPage |
| `/health-medicine/` | yes | HealthPage |
| `/initiatives/` | yes | InitiativesPage |
| `/giving/` | yes | GivingPage |
| `/prospective-students/` | yes | ProspectivePage |
| `/current-students/` | yes | CurrentStudentsPage |
| `/faculty-staff/` | yes | FacultyStaffPage |
| `/parents/` | yes | ParentsPage |
| `/alumni/` | yes | AlumniPage |
| `/schools-colleges/` | yes | SchoolsCollegesPage |
| `/facts-figures/` | yes | FactsFiguresPage |
| `/contact/` | yes | ContactPage |
| `/search/` | yes | SearchPage |
| `/about/privacy/` | yes | PrivacyPage |
| `/about/privacy-statement/` | yes | PrivacyStatementPage |
| `/_404.html` | offline notice | OfflinePage |

## Interaction checks (reference action → observed → candidate parity)
- [x] Header "Quick Links": reference button toggles a dropdown of links (Academic Calendar, Studio/Portal/Learn, Directory, Email, Email — CHS, Library Catalog, Maps & Directions, Schools & Colleges, Corravale Access). Per-route label varies. Candidate: toggles panel, same labels, `Schools & Colleges → /schools-colleges/`.
- [x] Header search (Enter + button): reference URL becomes `/search/?keywords=<q>` and the page shows the same search form (no result list rendered offline). Candidate: `navigate('/search/?keywords=' + q)`, no-op result set — parity.
- [x] Search page form submit: reference navigates to `/search/?keywords=<q>` (address bar updates, body unchanged, input not re-prefilled). Candidate now submits via router (was `preventDefault` no-op — fixed).
- [x] `/about/privacy/` link "privacy overview" → `/about/privacy-statement/` (reference confirmed). Candidate: real route + page (was missing → home — fixed).
- [x] `/about/privacy/` "Specific Notices" links → `/about/privacy-statement/#coppa` and `#eu`. Candidate: navigate + scroll to `#coppa`/`#eu` disclosure ids.
- [x] Privacy statement "Special Notices" disclosures: reference click expands inline COPPA / EU text. Candidate: Disclosure component with aria-expanded.
- [x] Footer: Privacy Notice → `/about/privacy/`; Contact us → `/contact/`; Phone → `tel:+1-734-764-1817`; campuses Fairhaven `/`, Westgate/Alden `/_404.html`; social feeds + Careers + regulatory badges → `/_404.html`.
- [x] Main nav (desktop) links route to their pages; mobile menu toggle expands the same links.
- [x] Direct route load / reload / back: router reads `window.location.pathname`, popstate handled.
