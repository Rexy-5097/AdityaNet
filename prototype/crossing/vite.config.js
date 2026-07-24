import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// `.glsl?raw` imports use Vite's built-in raw suffix — no plugin. reportCompressedSize
// gives the bundle figure. dedupe keeps a single React instance (R3F is strict about it).
export default defineConfig({
  plugins: [react()],
  resolve: { dedupe: ["react", "react-dom"] },
  build: { reportCompressedSize: true },
});
