import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type AnchorHTMLAttributes,
  type MouseEvent,
  type ReactNode,
} from "react";

type RouterValue = {
  path: string;
  navigate: (to: string) => void;
};

const RouterContext = createContext<RouterValue>({ path: "/", navigate: () => {} });

/**
 * Map a raw location pathname to an app route. The exported bundle may be
 * opened straight from the filesystem, where the pathname is a real file path
 * such as ".../output/index.html" or ".../output/_404.html".
 */
function normalize(path: string) {
  if (!path) return "/";
  if (path.endsWith("/_404.html")) return "/_404.html";
  if (path.endsWith("/index.html")) return "/";
  if (path.endsWith(".html")) return path.slice(path.lastIndexOf("/"));
  if (path.length > 1 && path.endsWith("/")) return path.slice(0, -1);
  return path;
}

/** Separate an href into pathname + hash so in-page anchors survive routing. */
function splitHref(href: string) {
  const hashAt = href.indexOf("#");
  if (hashAt === -1) return { pathname: href, hash: "" };
  return { pathname: href.slice(0, hashAt), hash: href.slice(hashAt) };
}

export function RouterProvider({ children }: { children: ReactNode }) {
  const [path, setPath] = useState(() => normalize(window.location.pathname));

  useEffect(() => {
    const onPop = () => setPath(normalize(window.location.pathname));
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  const navigate = useCallback((to: string) => {
    const { pathname, hash } = splitHref(to);
    const target = normalize(pathname || window.location.pathname);
    const samePath = target === normalize(window.location.pathname);

    if (samePath) {
      if (hash) document.getElementById(hash.slice(1))?.scrollIntoView({ behavior: "smooth" });
      return;
    }

    try {
      window.history.pushState({}, "", target + hash);
    } catch {
      // e.g. opaque file:// origins where the History API is restricted.
    }
    setPath(target);
    if (hash) {
      window.requestAnimationFrame(() => {
        document.getElementById(hash.slice(1))?.scrollIntoView({ behavior: "smooth" });
      });
    } else {
      window.scrollTo(0, 0);
    }
  }, []);

  const value = useMemo(() => ({ path, navigate }), [path, navigate]);
  return <RouterContext.Provider value={value}>{children}</RouterContext.Provider>;
}

export function useRouter() {
  return useContext(RouterContext);
}

/** hrefs the browser can resolve on its own: mail, phone, and bare anchors. */
function isBrowserHandled(href: string) {
  return (
    href.startsWith("#") ||
    href.startsWith("tel:") ||
    href.startsWith("mailto:") ||
    href.startsWith("javascript:")
  );
}

type LinkProps = AnchorHTMLAttributes<HTMLAnchorElement> & {
  /** Destination path such as "/about/" or "/schools-colleges/". */
  to: string;
};

/**
 * Client-side anchor. Root-relative destinations route through the in-app
 * router; protocol links and bare anchors fall through to the browser.
 */
export function Link({ to, children, onClick, ...rest }: LinkProps) {
  const { navigate } = useRouter();

  if (isBrowserHandled(to)) {
    return (
      <a href={to} {...rest} onClick={onClick}>
        {children}
      </a>
    );
  }

  const internal = to.startsWith("/");
  const href = internal ? to : "#";

  const handleClick = (event: MouseEvent<HTMLAnchorElement>) => {
    onClick?.(event);
    if (!internal) {
      event.preventDefault();
      return;
    }
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0) {
      return;
    }
    event.preventDefault();
    navigate(to);
  };

  return (
    <a href={href} {...rest} onClick={handleClick}>
      {children}
    </a>
  );
}
