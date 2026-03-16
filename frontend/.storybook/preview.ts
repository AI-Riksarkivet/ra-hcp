import type { Preview } from "@storybook/sveltekit";
import { withThemeByClassName } from "@storybook/addon-themes";
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
    a11y: {
      // Fail on accessibility violations by default — use 'todo' per-story to defer fixes
      test: "error",
    },
  },
  decorators: [
    withThemeByClassName({
      themes: {
        light: "",
        dark: "dark",
      },
      defaultTheme: "light",
    }),
  ],
};

export default preview;
