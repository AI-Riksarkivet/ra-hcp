/**
 * CSF3 interaction tests for FormDialog.
 *
 * Tests form submission, validation errors, and cancel behavior.
 *
 * Run `make storybook` and open the "Interactions" panel to see results.
 */
import type { Meta, StoryObj } from "@storybook/svelte";
import { expect, userEvent, within } from "storybook/test";
import FormDialogTestHarness from "./form-dialog-test-harness.svelte";

const meta = {
  title: "Tests/FormDialog Interactions",
  component: FormDialogTestHarness,
  tags: ["autodocs"],
} satisfies Meta<FormDialogTestHarness>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Verify the dialog renders with title and description.
 */
export const RendersDialog: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);

    await expect(canvas.getByText("Create Namespace")).toBeInTheDocument();
    await expect(
      canvas.getByText("Create a new namespace."),
    ).toBeInTheDocument();
    await expect(
      canvas.getByPlaceholderText("my-namespace"),
    ).toBeInTheDocument();
    await expect(
      canvas.getByRole("button", { name: "Create" }),
    ).toBeInTheDocument();
    await expect(
      canvas.getByRole("button", { name: "Cancel" }),
    ).toBeInTheDocument();
  },
};

/**
 * Submit with empty name shows validation error.
 */
export const ValidationError: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const submitBtn = canvas.getByRole("button", { name: "Create" });

    await userEvent.click(submitBtn);

    await expect(canvas.getByText("Name is required.")).toBeInTheDocument();
  },
};

/**
 * Submit with duplicate name shows conflict error.
 */
export const ConflictError: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const input = canvas.getByPlaceholderText("my-namespace");
    const submitBtn = canvas.getByRole("button", { name: "Create" });

    await userEvent.type(input, "existing");
    await userEvent.click(submitBtn);

    await expect(
      canvas.getByText("Namespace 'existing' already exists."),
    ).toBeInTheDocument();
  },
};

/**
 * Successful submission shows success message.
 */
export const SuccessfulSubmit: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const input = canvas.getByPlaceholderText("my-namespace");
    const submitBtn = canvas.getByRole("button", { name: "Create" });

    await userEvent.type(input, "new-namespace");
    await userEvent.click(submitBtn);

    await expect(
      canvas.getByTestId("success-msg"),
    ).toHaveTextContent("Created namespace: new-namespace");
  },
};
