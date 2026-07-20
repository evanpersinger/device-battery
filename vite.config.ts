import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import electron from "vite-plugin-electron/simple";
import svgr from "vite-plugin-svgr";

export default defineConfig({
  plugins: [
    react(),
    // Lets `import Icon from "./icons/thing.svg?react"` give back a component.
    // Downloaded icons usually hardcode black, so swap those for currentColor
    // and they inherit whatever the surrounding text color is.
    svgr({
      svgrOptions: {
        // SVGRepo icons hardcode a fill. Add any new one you run into here,
        // otherwise the icon renders in its baked-in color and ignores the theme.
        replaceAttrValues: {
          "#000000": "currentColor",
          "#000": "currentColor",
          "#0F1729": "currentColor",
          "#0f1729": "currentColor",
          black: "currentColor",
        },
      },
    }),
    electron({
      main: { entry: "electron/main.ts" },
      preload: { input: "electron/preload.ts" },
    }),
  ],
});
