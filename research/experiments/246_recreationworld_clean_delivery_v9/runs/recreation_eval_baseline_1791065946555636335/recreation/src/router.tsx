import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { AnchorHTMLAttributes, ReactNode } from "react";

interface RouterValue {
  path: string;
  navigate: (to: string) => void;
}

const RouterContext = createContext<RouterValue>({ path: "/", navigate: () => {} });

export function normalizePath(raw: string): string {
  let p = raw.split("?")[0].split("#")[0];
  if (!p.startsWith("/")) p = "/" + p;
  return p;
}

export function RouterProvider({ children }: { children: ReactNode }) {
  const [path, setPath] = useState<string>(() => normalizePath(window.location.pathname));

  useEffect(() => {
    const onPop = () => setPath(normalizePath(window.location.pathname));
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  const navigate = useCallback((to: string) => {
    const target = normalizePath(to);
    if (target === normalizePath(window.location.pathname)) {
      window.scrollTo({ top: 0 });
      return;
    }
    window.history.pushState({}, "", target);
    setPath(target);
    window.scrollTo({ top: 0 });
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
  const isExternal = /^(https?:|mailto:|tel:)/.test(to);
  return (
    <a
      href={to}
      onClick={(e) => {
        onClick?.(e);
        if (isExternal) return;
        if (e.defaultPrevented) return;
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        e.preventDefault();
        navigate(to);
      }}
      {...rest}
    >
      {children}
    </a>
  );
}
