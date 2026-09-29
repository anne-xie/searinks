import type { Discipline } from "@/schedule";

export type Preferences = {
  /** Rink keys to show; empty shows every rink. */
  rinks: string[];
  sports: Discipline[];
  dropIn: boolean;
};

// Hardcoded until preferences are stored in the browser (#15).
export const DEFAULT_PREFERENCES: Preferences = {
  rinks: [],
  sports: ["figure", "public"],
  dropIn: true,
};
