import type { JSX } from "preact";

import type { Route } from "../routes";

const TABS: { route: Route; label: string }[] = [
  { route: "schedule", label: "Schedule" },
  { route: "map", label: "Map" },
];

/** Snowflake mark next to the wordmark. */
function Logo(): JSX.Element {
  return (
    <a href="#/schedule" class="logo">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
        <path d="M12 2v20M4.2 6.5l15.6 11M4.2 17.5l15.6-11M9.5 3.5 12 6l2.5-2.5M9.5 20.5 12 18l2.5 2.5" />
      </svg>
      <span class="wordmark">searinks</span>
    </a>
  );
}

/** Gear icon for Preferences. */
function Gear(): JSX.Element {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z" />
    </svg>
  );
}

/**
 * Shared header: a band with pill tabs on phones, a top bar with text links on desktop.
 * @param route Current view, highlighted in the nav.
 */
export function Header({ route }: { route: Route }): JSX.Element {
  const current = (tab: Route): "page" | undefined => (tab === route ? "page" : undefined);
  return (
    <>
      <header class="header-phone">
        <div class="header-phone-row">
          <Logo />
          <a href="#/preferences" class="gear" aria-label="Preferences" aria-current={current("preferences")}>
            <Gear />
          </a>
        </div>
        <nav class="pills" aria-label="Views">
          {TABS.map((tab) => (
            <a key={tab.route} href={`#/${tab.route}`} class="pill" aria-current={current(tab.route)}>
              {tab.label}
            </a>
          ))}
        </nav>
      </header>
      <header class="header-desktop">
        <Logo />
        <nav class="links" aria-label="Views">
          {TABS.map((tab) => (
            <a key={tab.route} href={`#/${tab.route}`} class="link" aria-current={current(tab.route)}>
              {tab.label}
            </a>
          ))}
        </nav>
        <a href="#/preferences" class="prefs-button" aria-current={current("preferences")}>
          <Gear />
          Preferences
        </a>
      </header>
    </>
  );
}
