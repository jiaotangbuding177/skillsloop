import { RouterProvider, useRouter } from "@/lib/router";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import Home from "@/pages/Home";
import ContentPage from "@/pages/ContentPage";
import Contact from "@/pages/Contact";
import Privacy from "@/pages/Privacy";

/** Content slugs that render with the shared audience-page template. */
const CONTENT_SLUGS = new Set([
  "about",
  "academics",
  "life-at-michigan",
  "athletics",
  "research",
  "health-medicine",
  "initiatives",
  "giving",
  "prospective-students",
  "current-students",
  "faculty-staff",
  "parents",
  "alumni",
  "schools-colleges",
]);

function slugFor(path: string) {
  return path.replace(/^\/+|\/+$/g, "");
}

function RouteView() {
  const { path } = useRouter();

  if (path === "/" || path === "") return <Home />;
  if (path === "/contact/") return <Contact />;
  if (path === "/about/privacy/") return <Privacy />;

  const slug = slugFor(path);
  if (CONTENT_SLUGS.has(slug)) return <ContentPage slug={slug} />;

  return <NotFound />;
}

function NotFound() {
  const { path } = useRouter();
  return (
    <div className="panel panel-grey content clear">
      <div className="panel-header">
        <h2>Page Not Found</h2>
      </div>
      <div className="wrap panel-content">
        <div className="panel-description">
          <p>
            The page you requested (<code>{path}</code>) could not be located.
            Please use the navigation above to find what you are looking for.
          </p>
        </div>
      </div>
    </div>
  );
}

function Shell() {
  return (
    <>
      <a className="skip-link" href="#content">
        Skip to main content
      </a>
      <Header />
      <main id="content" role="main">
        <RouteView />
      </main>
      <Footer />
    </>
  );
}

export function App() {
  return (
    <RouterProvider>
      <Shell />
    </RouterProvider>
  );
}
