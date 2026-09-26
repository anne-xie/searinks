import { useEffect, useState } from "preact/hooks";

// Hash routes, since GitHub Pages can't fall back to index.html for deep links.
export const ROUTES = ["schedule", "map", "preferences"] as const;
export type Route = (typeof ROUTES)[number];

/**
 * Map a location hash to a view.
 * @param hash `location.hash`, e.g. "#/map".
 */
export function parseRoute(hash: string): Route {
  const name = hash.replace(/^#\/?/, "");
  return (ROUTES as readonly string[]).includes(name) ? (name as Route) : "schedule";
}

/** Current view, following hash changes. */
export function useRoute(): Route {
  const [route, setRoute] = useState(() => parseRoute(location.hash));
  useEffect(() => {
    const onChange = (): void => setRoute(parseRoute(location.hash));
    addEventListener("hashchange", onChange);
    return () => removeEventListener("hashchange", onChange);
  }, []);
  return route;
}
