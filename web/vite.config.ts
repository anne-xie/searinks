import preact from "@preact/preset-vite";
import { defineConfig } from "vite";

// Served from https://anne-xie.github.io/searinks/ once built. `../site` holds the
// export's `data/` folder, so dev serves it and the build copies it into `dist/`.
// "mpa" turns off the dev server's index.html fallback, so a missing day file is a 404
// there too, as on GitHub Pages; routing is by hash, so nothing needs the fallback.
export default defineConfig(({ command }) => ({
  appType: "mpa",
  base: command === "build" ? "/searinks/" : "/",
  // `@/x` is `src/x`; keep in step with `paths` in tsconfig.json.
  resolve: { alias: { "@": "/src" } },
  publicDir: "../site",
  plugins: [preact()],
}));
