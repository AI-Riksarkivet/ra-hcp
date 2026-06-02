/**
 * CSF3 interaction tests for the bucket object-browser search derivation.
 *
 * Guards the fix for the "search returns no results for objects beyond the
 * first 1,000" bug: a search term must drive a server-side flat prefix query
 * (navigated prefix + term), not a client-side filter of the loaded page.
 */
import type { Meta, StoryObj } from "@storybook/svelte";
import { expect, userEvent, within } from "storybook/test";
import TestHarness from "./object-search-test-harness.svelte";

const meta = {
  title: "Tests/ObjectSearch",
  // deno-lint-ignore no-explicit-any -- Storybook Meta types incompatible with Svelte 5 Component
  component: TestHarness as any,
  tags: ["!autodocs"],
} satisfies Meta<typeof TestHarness>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * No search term: list the navigated prefix in the current (folder) view.
 */
export const EmptySearchKeepsFolderView: Story = {
  args: { navigatedPrefix: "", initialFlat: false },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByTestId("query-prefix")).toBeEmptyDOMElement();
    await expect(canvas.getByTestId("query-flat")).toHaveTextContent("false");
  },
};

/**
 * Searching at the bucket root must query the backend by prefix in flat mode,
 * so a batch far down the alphabet (e.g. after tens of thousands of numeric
 * keys) is found instead of silently missing.
 */
export const SearchAtRootMatchesPrefixFlat: Story = {
  args: { navigatedPrefix: "", initialFlat: false },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await userEvent.type(canvas.getByTestId("search"), "A0075850");
    await expect(canvas.getByTestId("query-prefix")).toHaveTextContent(
      "A0075850",
    );
    await expect(canvas.getByTestId("query-flat")).toHaveTextContent("true");
  },
};

/**
 * Searching inside a folder prepends the navigated prefix to the term.
 */
export const SearchWithinFolderPrependsPrefix: Story = {
  args: { navigatedPrefix: "A0075850/", initialFlat: false },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await userEvent.type(canvas.getByTestId("search"), "A0075850_002");
    await expect(canvas.getByTestId("query-prefix")).toHaveTextContent(
      "A0075850/A0075850_002",
    );
    await expect(canvas.getByTestId("query-flat")).toHaveTextContent("true");
  },
};

/**
 * Whitespace-only input is not treated as a search (no prefix narrowing).
 */
export const WhitespaceIsNotASearch: Story = {
  args: { navigatedPrefix: "", initialFlat: false },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await userEvent.type(canvas.getByTestId("search"), "   ");
    await expect(canvas.getByTestId("query-prefix")).toBeEmptyDOMElement();
    await expect(canvas.getByTestId("query-flat")).toHaveTextContent("false");
  },
};
