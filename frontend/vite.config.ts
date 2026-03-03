import tailwindcss from "@tailwindcss/vite";
import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [tailwindcss(), sveltekit()],
  ssr: {
    noExternal: ["svelte-sonner", "mode-watcher", "svelte-toolbelt"],
  },
  server: {
    host: "0.0.0.0",
    port: 5174,
    strictPort: true,
    allowedHosts: true,
    hmr: {
      // code-server proxy uses port 443 over wss
      clientPort: 443,
      protocol: "wss",
    },
  },
});
