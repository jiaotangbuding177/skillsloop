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
  return path;
}

export function RouterProvider({ children }: { children: ReactNode }) {
  const [path, setPath] = useState(() =>
    normalize(window.location.pathname),
  );

  useEffect(() => {
    const onPop = () => setPath(normalize(window.location.pathname));
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  const navigate = useCallback((to: string) => {
    if (to.startsWith("http") || to.startsWith("tel:")) {
      window.location.href = to;
      return;
    }
    const target = normalize(to);
    if (target === window.location.pathname) {
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }
    window.history.pushState({}, "", target);
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
