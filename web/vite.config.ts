import preact from "@preact/preset-vite";
import { defineConfig } from "vite";

// Served from https://anne-xie.github.io/searinks/ once built. `../site` holds the
// export's `data/` folder, so dev serves it and the build copies it into `dist/`.
export default defineConfig(({ command }) => ({
  base: command === "build" ? "/searinks/" : "/",
  publicDir: "../site",
  plugins: [preact()],
}));
