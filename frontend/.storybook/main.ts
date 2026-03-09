import type { StorybookConfig } from "@storybook/sveltekit";

const config: StorybookConfig = {
  stories: ["../src/**/*.stories.@(js|ts|svelte)"],
  addons: ["@storybook/addon-svelte-csf"],
  framework: {
    name: "@storybook/sveltekit",
    options: {
      docgen: false,
    },
  },
};

export default config;
