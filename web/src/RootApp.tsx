import { useCallback, useEffect, useMemo, useState } from "react";
import { App } from "./App";
import { DocsLocale, DocsPage } from "./docs/DocsPage";

type RouteMatch =
  | { kind: "app" }
  | {
      kind: "docs";
      locale: DocsLocale;
      canonicalPath: string;
    };

function parseRoute(pathname: string): RouteMatch {
  if (!pathname.startsWith("/docs")) {
    return { kind: "app" };
  }

  const segments = pathname.split("/").filter(Boolean);
  if (segments.length < 2) {
    return {
      kind: "docs",
      locale: "en",
      canonicalPath: "/docs/en",
    };
  }

  const locale = segments[1];
  if (locale === "en" || locale === "ru") {
    return {
      kind: "docs",
      locale,
      canonicalPath: `/docs/${locale}`,
    };
  }

  return {
    kind: "docs",
    locale: "en",
    canonicalPath: "/docs/en",
  };
}

export function RootApp() {
  const [pathname, setPathname] = useState<string>(() => window.location.pathname);

  const route = useMemo(() => parseRoute(pathname), [pathname]);

  useEffect(() => {
    const onPopState = () => setPathname(window.location.pathname);
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  useEffect(() => {
    if (route.kind !== "docs") {
      return;
    }

    if (window.location.pathname !== route.canonicalPath) {
      window.history.replaceState({}, "", route.canonicalPath);
      setPathname(route.canonicalPath);
    }
  }, [route]);

  const navigate = useCallback((nextPath: string) => {
    const currentPath = `${window.location.pathname}${window.location.search}`;
    if (currentPath === nextPath) {
      return;
    }

    window.history.pushState({}, "", nextPath);
    setPathname(window.location.pathname);
  }, []);

  if (route.kind === "docs") {
    return (
      <DocsPage
        locale={route.locale}
        onNavigateToApp={(mode) => navigate(mode === "use" ? "/?mode=use" : "/")}
        onLocaleChange={(nextLocale) => navigate(`/docs/${nextLocale}`)}
      />
    );
  }

  return <App />;
}
