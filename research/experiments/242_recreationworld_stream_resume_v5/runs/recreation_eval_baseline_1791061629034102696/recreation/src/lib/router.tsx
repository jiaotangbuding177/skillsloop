import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type AnchorHTMLAttributes,
  type ReactNode,
} from "react";

/**
 * Minimal client-side router driven by the History API so that real URL
 * paths (for example /about/) are used instead of hash fragments.
 */

type RouterValue = {
  path: string;
  navigate: (to: string) => void;
};

const RouterContext = createContext<RouterValue>({
  path: "/",
  navigate: () => {},
});

function normalize(path: string) {
  if (!path) return "/";
  // When the bundle is opened directly as a file (file://.../index.html) or
  // served from a sub-path, strip any trailing document name so routing still
  // starts at the site root and path-based navigation keeps working.
  if (/\.html?$/i.test(path)) return "/";
  return path;
}

function readPath() {
  const hash = window.location.hash.replace(/^#/, "");
  if (hash && hash.startsWith("/")) return normalize(hash);
  return normalize(window.location.pathname);
}

export function RouterProvider({ children }: { children: ReactNode }) {
  const [path, setPath] = useState(readPath);

  useEffect(() => {
    const onPop = () => setPath(readPath());
    window.addEventListener("popstate", onPop);
    window.addEventListener("hashchange", onPop);
    return () => {
      window.removeEventListener("popstate", onPop);
      window.removeEventListener("hashchange", onPop);
    };
  }, []);

  const navigate = useCallback((to: string) => {
    if (to.startsWith("http") || to.startsWith("tel:")) {
      window.location.href = to;
      return;
    }
    const target = normalize(to);
    if (target === normalize(window.location.pathname)) {
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }
    try {
      window.history.pushState({}, "", target);
    } catch {
      // Some sandboxed/file contexts disallow pushState; fall back to hash so
      // navigation still reaches the right view.
      window.location.hash = target;
    }
    setPath(target);
    window.scrollTo({ top: 0, behavior: "auto" });
  }, []);

  const value = useMemo(() => ({ path, navigate }), [path, navigate]);

  return (
    <RouterContext.Provider value={value}>{children}</RouterContext.Provider>
  );
}

export function useRouter() {
  return useContext(RouterContext);
}

type LinkProps = AnchorHTMLAttributes<HTMLAnchorElement> & { to: string };

export function Link({ to, children, onClick, ...rest }: LinkProps) {
  const { navigate } = useRouter();
  return (
    <a
      href={to}
      onClick={(event) => {
        onClick?.(event);
        if (
          event.defaultPrevented ||
          event.metaKey ||
          event.ctrlKey ||
          event.shiftKey ||
          event.altKey
        ) {
          return;
        }
        event.preventDefault();
        navigate(to);
      }}
      {...rest}
    >
      {children}
    </a>
  );
}
