import { describe, expect, it } from "vitest";

const SOURCES = import.meta.glob(["/src/**/*.{ts,tsx}", "/tests/**/*.ts"], {
  query: "?raw",
  import: "default",
  eager: true,
}) as Record<string, string>;

/**
 * Module specifiers in a source file that start with "./" or "../".
 * @param source File contents.
 */
function relativeImports(source: string): string[] {
  return [...source.matchAll(/(?:from|import)\s*\(?\s*["'](\.{1,2}\/[^"']+)["']/g)].map((m) => m[1]);
}

describe("imports", () => {
  it.each([
    ['import { a } from "./a";', ["./a"]],
    ["import b from '../b';", ["../b"]],
    ['import "./styles.css";', ["./styles.css"]],
    ['const c = await import("./c");', ["./c"]],
    ['import { d } from "@/d";', []],
  ])("finds relative specifiers in %s", (source, expected) => {
    // WHEN/THEN: only ./ and ../ specifiers count
    expect(relativeImports(source)).toEqual(expected);
  });

  it("uses the @/ alias everywhere", () => {
    // GIVEN: every source and test file
    const offenders = Object.entries(SOURCES).flatMap(([path, source]) =>
      relativeImports(source).map((spec) => `${path}: ${spec}`),
    );

    // THEN: none imports by relative path
    expect(Object.keys(SOURCES).length).toBeGreaterThan(10);
    expect(offenders).toEqual([]);
  });
});
