import type { Preview } from "@storybook/sveltekit";
import "../src/app.css";

const preview: Preview = {
  // Autodocs for all stories globally — no need to set per-file
  tags: ["autodocs"],
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    docs: {
      toc: true,
    },
  },
};

export default preview;
