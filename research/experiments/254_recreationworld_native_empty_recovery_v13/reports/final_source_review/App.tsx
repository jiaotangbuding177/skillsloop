import { useEffect } from "react";
import { RouterProvider, useRouter } from "@/lib/router";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { HomePage } from "@/pages/HomePage";
import {
  AboutPage,
  AcademicsPage,
  LifePage,
  AthleticsPage,
  ResearchPage,
  HealthPage,
  InitiativesPage,
  GivingPage,
  ProspectivePage,
  CurrentStudentsPage,
  FacultyStaffPage,
  ParentsPage,
  AlumniPage,
  SchoolsCollegesPage,
  FactsFiguresPage,
} from "@/pages/ContentPages";
import { ContactPage, SearchPage, PrivacyPage } from "@/pages/MorePages";
import { OfflinePage } from "@/pages/OfflinePage";

const offlinePaths = new Set(["/_404.html", "/404", "/not-found"]);

function routeFor(path: string) {
  if (offlinePaths.has(path)) return <OfflinePage />;
  switch (path) {
    case "/":
      return <HomePage />;
    case "/about":
      return <AboutPage />;
    case "/academics":
      return <AcademicsPage />;
    case "/life-at-michigan":
      return <LifePage />;
    case "/athletics":
      return <AthleticsPage />;
    case "/research":
      return <ResearchPage />;
    case "/health-medicine":
      return <HealthPage />;
    case "/initiatives":
      return <InitiativesPage />;
    case "/giving":
      return <GivingPage />;
    case "/prospective-students":
      return <ProspectivePage />;
    case "/current-students":
      return <CurrentStudentsPage />;
    case "/faculty-staff":
      return <FacultyStaffPage />;
    case "/parents":
      return <ParentsPage />;
    case "/alumni":
      return <AlumniPage />;
    case "/schools-colleges":
      return <SchoolsCollegesPage />;
    case "/facts-figures":
      return <FactsFiguresPage />;
    case "/contact":
      return <ContactPage />;
    case "/search":
      return <SearchPage />;
    case "/about/privacy":
      return <PrivacyPage />;
    default:
      return <HomePage />;
  }
}

const titles: Record<string, string> = {
  "/": "Corravale University",
  "/about": "About › Corravale University",
  "/academics": "Academics › Corravale University",
  "/life-at-michigan": "Life on Campus › Corravale University",
  "/athletics": "Athletics › Corravale University",
  "/research": "Research › Corravale University",
  "/health-medicine": "Health & Medicine › Corravale University",
  "/initiatives": "Initiatives › Corravale University",
  "/giving": "Giving › Corravale University",
  "/prospective-students": "Prospective Students › Corravale University",
  "/current-students": "Current Students › Corravale University",
  "/faculty-staff": "Faculty and Staff › Corravale University",
  "/parents": "Parents › Corravale University",
  "/alumni": "Alumni › Corravale University",
  "/schools-colleges": "Schools & Colleges › Corravale University",
  "/facts-figures": "Facts & Figures › Corravale University",
  "/contact": "Contact › Corravale University",
  "/search": "Corravale University",
  "/about/privacy": "Privacy Notice › Corravale University",
  "/_404.html": "Page Not Available - Offline Mode",
};

function Shell() {
  const { path } = useRouter();
  useEffect(() => {
    document.title = titles[path] ?? "Corravale University";
  }, [path]);

  if (offlinePaths.has(path)) {
    return (
      <main id="content">
        <OfflinePage />
      </main>
    );
  }

  return (
    <div className="flex min-h-screen flex-col">
      <a href="#content" className="sr-only focus:not-sr-only">
        Skip to main content
      </a>
      <Header path={path} />
      <main id="content" className="flex-1">
        {routeFor(path)}
      </main>
      <Footer />
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
