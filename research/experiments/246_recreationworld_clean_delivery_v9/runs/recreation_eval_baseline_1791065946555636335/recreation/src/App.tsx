import { useEffect } from "react";
import { RouterProvider, useRouter } from "@/router";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { HomePage } from "@/pages/HomePage";
import { SectionPage } from "@/pages/SectionPage";
import { FactsFiguresPage } from "@/pages/FactsFiguresPage";
import { ContactPage, NotFoundPage, PrivacyPage, SchoolsCollegesPage } from "@/pages/SimplePages";
import { sectionByPath } from "@/data/pages";

/** Per-route header copy, mirroring the varied labels used across the site. */
const headerCopy: Record<string, { report: string; skip: string }> = {
  "/": { report: "Report Sexual Misconduct, Discrimination, and Bias Concerns", skip: "Skip to main content" },
  "/about/": { report: "Report Sexual Misconduct, Discrimination, and Harassment", skip: "Skip global navigation" },
  "/academics/": { report: "Report Misconduct, Bias, Discrimination and Harassment", skip: "Jump past site navigation" },
  "/life-at-michigan/": { report: "Report Misconduct, Discrimination, and Bias Incidents", skip: "Skip primary navigation" },
  "/athletics/": { report: "Report Misconduct, Bias, Discrimination and Harassment", skip: "Jump to main navigation" },
  "/research/": { report: "Report Misconduct, Discrimination and Harassment Concerns", skip: "Skip global navigation" },
  "/health-medicine/": { report: "Report Misconduct, Discrimination and Bias Incidents", skip: "Jump past main navigation" },
  "/initiatives/": { report: "Report Sexual Misconduct, Discrimination and Harassment", skip: "Skip global navigation" },
  "/giving/": { report: "Report Misconduct, Bias, Discrimination and Harassment", skip: "Skip primary navigation" },
  "/facts-figures/": { report: "Report Sexual Misconduct, Discrimination and Harassment", skip: "Skip global navigation" },
  "/contact/": { report: "Report Misconduct, Bias Incidents and Harassment Here", skip: "Skip to primary content" },
  "/about/privacy/": { report: "Report Sexual Misconduct, Discrimination and Harassment", skip: "Skip global navigation" },
  "/schools-colleges/": { report: "Report Misconduct, Discrimination, Bias and Harassment", skip: "Skip primary navigation" },
  "/prospective-students/": { report: "Report Misconduct, Discrimination, and Harassment Concerns", skip: "Skip to main navigation" },
  "/current-students/": { report: "Report Misconduct, Discrimination, Bias and Harassment", skip: "Skip primary navigation" },
  "/faculty-staff/": { report: "Report Misconduct, Bias, Discrimination and Harassment", skip: "Skip to primary content" },
  "/parents/": { report: "Report Misconduct, Discrimination, and Harassment Concerns", skip: "Skip main navigation" },
  "/alumni/": { report: "Report Sexual Misconduct, Discrimination and Harassment", skip: "Skip global navigation" },
  "/_404.html": { report: "Report Sexual Misconduct, Discrimination, and Bias Concerns", skip: "Skip to main content" },
};

const DEFAULTS = {
  report: "Report Sexual Misconduct, Discrimination, and Bias Concerns",
  skip: "Skip to main content",
};

const pageTitles: Record<string, string> = {
  "/": "Corravale University",
  "/about/": "About › Corravale University",
  "/academics/": "Academics › Corravale University",
  "/life-at-michigan/": "Life on Campus › Corravale University",
  "/athletics/": "Athletics › Corravale University",
  "/research/": "Research › Corravale University",
  "/health-medicine/": "Health & Medicine › Corravale University",
  "/initiatives/": "Initiatives › Corravale University",
  "/giving/": "Giving › Corravale University",
  "/facts-figures/": "Facts & Figures › Corravale University",
  "/contact/": "Contact › Corravale University",
  "/about/privacy/": "Privacy Notice › Corravale University",
  "/schools-colleges/": "Schools & Colleges › Corravale University",
  "/prospective-students/": "Prospective Students › Corravale University",
  "/current-students/": "Current Students › Corravale University",
  "/faculty-staff/": "Faculty and Staff › Corravale University",
  "/parents/": "Parents › Corravale University",
  "/alumni/": "Alumni › Corravale University",
};

function Routes() {
  const { path } = useRouter();
  const section = sectionByPath[path];

  if (path === "/") return <HomePage />;
  if (section) return <SectionPage config={section} />;
  if (path === "/facts-figures/") return <FactsFiguresPage />;
  if (path === "/schools-colleges/") return <SchoolsCollegesPage />;
  if (path === "/contact/") return <ContactPage />;
  if (path === "/about/privacy/") return <PrivacyPage />;
  return <NotFoundPage />;
}

function Shell() {
  const { path } = useRouter();
  const copy = headerCopy[path] ?? DEFAULTS;
  const isHome = path === "/";

  useEffect(() => {
    document.title = pageTitles[path] ?? "Page Not Available - Offline Mode";
  }, [path]);

  return (
    <div className="min-h-screen bg-white">
      <a
        href="#content"
        className="absolute left-[-9999px] top-0 z-50 bg-white px-[10px] py-[6px] text-[14px] focus:left-0"
      >
        {copy.skip}
      </a>
      <div className={isHome ? "relative" : ""}>
        <Header reportLabel={copy.report} overlay={isHome} />
        <main id="content" role="main">
          <Routes />
        </main>
        <Footer />
      </div>
    </div>
  );
}

export function App() {
  return (
    <RouterProvider>
      <Shell />
    </RouterProvider>
  );
}
