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

type RouterValue = {
  path: string;
  navigate: (to: string) => void;
};

const RouterContext = createContext<RouterValue>({ path: "/", navigate: () => {} });

function normalize(path: string) {
  if (!path) return "/";
  if (path.length > 1 && path.endsWith("/")) return path.slice(0, -1);
  return path;
}

export function RouterProvider({ children }: { children: ReactNode }) {
  const [path, setPath] = useState(() => normalize(window.location.pathname));

  useEffect(() => {
    const onPop = () => setPath(normalize(window.location.pathname));
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  const navigate = useCallback((to: string) => {
    const target = normalize(to);
    if (target === normalize(window.location.pathname)) return;
    window.history.pushState({}, "", target);
    setPath(target);
    window.scrollTo(0, 0);
  }, []);

  const value = useMemo(() => ({ path, navigate }), [path, navigate]);
  return <RouterContext.Provider value={value}>{children}</RouterContext.Provider>;
}

export function useRouter() {
  return useContext(RouterContext);
}

type LinkProps = AnchorHTMLAttributes<HTMLAnchorElement> & { to: string };

export function Link({ to, children, onClick, ...rest }: LinkProps) {
  const { navigate } = useRouter();
  const isInternal = to.startsWith("/") && !to.startsWith("/_404");
  const isPlain = to.startsWith("#") || to.startsWith("tel:") || to.startsWith("javascript:");

  if (isPlain) {
    return (
      <a href={to} {...rest} onClick={onClick}>
        {children}
      </a>
    );
  }
  return (
    <a
      href={isInternal ? to : "#"}
      {...rest}
      onClick={(event) => {
        onClick?.(event);
        if (!isInternal) {
          event.preventDefault();
          return;
        }
        if (event.metaKey || event.ctrlKey || event.shiftKey) return;
        event.preventDefault();
        navigate(to);
      }}
    >
      {children}
    </a>
  );
}
