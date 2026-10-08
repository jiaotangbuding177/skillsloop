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

function routeFor(path: string) {
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

function Shell() {
  const { path } = useRouter();
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
