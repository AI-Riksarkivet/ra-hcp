import{N as p}from"./namespace-permissions-editor-test-harness-BmMaBvII.js";import"./iframe-BLq-IXw7.js";import"./preload-helper-PPVm8Dsz.js";import"./each-BUqwbEfg.js";import"./card-title-ezM6MUMx.js";import"./this-5dDYTdTk.js";import"./badge-DFv9TpwB.js";import"./index-ldovL64k.js";import"./Icon-BM2c6fgH.js";import"./legacy-Ci8bO8La.js";import"./button-DqmmnB3v.js";import"./label-B532bab9.js";import"./save-button-D5BaFS8u.js";import"./loader-circle-BONFkgg1.js";import"./constants-a8_tPpha.js";import"./shield-CBs9F1pr.js";import"./plus-D0LeIIhs.js";import"./trash-2-B_wMm7ZG.js";const{expect:t,userEvent:m,within:r}=__STORYBOOK_MODULE_TEST__,f={title:"Tests/NamespacePermissionsEditor Interactions",component:p,tags:["!autodocs"]},n={play:async({canvasElement:a})=>{const e=r(a);await t(e.getByText("production-data")).toBeInTheDocument(),await t(e.getByText("staging-env")).toBeInTheDocument(),await t(e.getByText("Namespace Access")).toBeInTheDocument()}},s={play:async({canvasElement:a})=>{const e=r(a),c=e.getAllByText("WRITE");await m.click(c[0]);const i=e.getByRole("button",{name:/save/i});await t(i).not.toBeDisabled()}},o={play:async({canvasElement:a})=>{const e=r(a);await t(e.getByText("staging-env")).toBeInTheDocument();const c=a.querySelectorAll('button[class*="hover:text-destructive"]');await t(c.length).toBe(2),await m.click(c[1]);const i=a.querySelectorAll('button[class*="hover:text-destructive"]');await t(i.length).toBe(1),await t(e.getByText("production-data")).toBeInTheDocument()}};n.parameters={...n.parameters,docs:{...n.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText("production-data")).toBeInTheDocument();
    await expect(canvas.getByText("staging-env")).toBeInTheDocument();
    await expect(canvas.getByText("Namespace Access")).toBeInTheDocument();
  }
}`,...n.parameters?.docs?.source},description:{story:"Verify initial state renders two namespaces with permissions.",...n.parameters?.docs?.description}}};s.parameters={...s.parameters,docs:{...s.parameters?.docs,source:{originalSource:`{
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
}`,...s.parameters?.docs?.source},description:{story:"Toggle a permission badge and verify it changes state.",...s.parameters?.docs?.description}}};o.parameters={...o.parameters,docs:{...o.parameters?.docs,source:{originalSource:`{
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
}`,...o.parameters?.docs?.source},description:{story:"Remove a namespace entry.",...o.parameters?.docs?.description}}};const A=["RendersInitialState","TogglePermission","RemoveNamespace"];export{o as RemoveNamespace,n as RendersInitialState,s as TogglePermission,A as __namedExportsOrder,f as default};
