import{i as e}from"./preload-helper-xPQekRTU.js";import{n as t,t as n}from"./namespace-permissions-editor-test-harness-BCvj8FXe.js";var r,i,a,o,s,c,l,u;e((()=>{t(),{expect:r,userEvent:i,within:a}=__STORYBOOK_MODULE_TEST__,o={title:`Tests/NamespacePermissionsEditor Interactions`,component:n,tags:[`!autodocs`]},s={play:async({canvasElement:e})=>{let t=a(e);await r(t.getByText(`production-data`)).toBeInTheDocument(),await r(t.getByText(`staging-env`)).toBeInTheDocument(),await r(t.getByText(`Namespace Access`)).toBeInTheDocument()}},c={play:async({canvasElement:e})=>{let t=a(e),n=t.getAllByText(`WRITE`);await i.click(n[0]),await r(t.getByRole(`button`,{name:/save/i})).not.toBeDisabled()}},l={play:async({canvasElement:e})=>{let t=a(e);await r(t.getByText(`staging-env`)).toBeInTheDocument();let n=e.querySelectorAll(`button[class*="hover:text-destructive"]`);await r(n.length).toBe(2),await i.click(n[1]),await r(e.querySelectorAll(`button[class*="hover:text-destructive"]`).length).toBe(1),await r(t.getByText(`production-data`)).toBeInTheDocument()}},s.parameters={...s.parameters,docs:{...s.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText("production-data")).toBeInTheDocument();
    await expect(canvas.getByText("staging-env")).toBeInTheDocument();
    await expect(canvas.getByText("Namespace Access")).toBeInTheDocument();
  }
}`,...s.parameters?.docs?.source},description:{story:`Verify initial state renders two namespaces with permissions.`,...s.parameters?.docs?.description}}},c.parameters={...c.parameters,docs:{...c.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);

    // Find all WRITE badges — staging-env has it enabled, production-data does not
    const writeBadges = canvas.getAllByText("WRITE");
    // Click WRITE on production-data (first namespace) to enable it
    await userEvent.click(writeBadges[0]);

    // The save button should now be enabled (dirty)
    const saveBtn = canvas.getByRole("button", {
      name: /save/i
    });
    await expect(saveBtn).not.toBeDisabled();
  }
}`,...c.parameters?.docs?.source},description:{story:`Toggle a permission badge and verify it changes state.`,...c.parameters?.docs?.description}}},l.parameters={...l.parameters,docs:{...l.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);

    // Verify staging-env exists as a namespace card label
    await expect(canvas.getByText("staging-env")).toBeInTheDocument();

    // Find the delete buttons (Trash2 icons) — there should be 2
    const deleteButtons = canvasElement.querySelectorAll('button[class*="hover:text-destructive"]');
    await expect(deleteButtons.length).toBe(2);

    // Click the second delete button (staging-env)
    await userEvent.click(deleteButtons[1] as HTMLElement);

    // After removal, staging-env moves from the card list to the <option> dropdown.
    // Verify the namespace card is removed by checking only 1 delete button remains.
    const remaining = canvasElement.querySelectorAll('button[class*="hover:text-destructive"]');
    await expect(remaining.length).toBe(1);

    // The remaining card should be production-data
    await expect(canvas.getByText("production-data")).toBeInTheDocument();
  }
}`,...l.parameters?.docs?.source},description:{story:`Remove a namespace entry.`,...l.parameters?.docs?.description}}},u=[`RendersInitialState`,`TogglePermission`,`RemoveNamespace`]}))();export{l as RemoveNamespace,s as RendersInitialState,c as TogglePermission,u as __namedExportsOrder,o as default};