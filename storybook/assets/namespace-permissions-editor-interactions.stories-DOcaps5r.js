import{N as p}from"./namespace-permissions-editor-test-harness-fIoqHW4V.js";import"./iframe-DFtYtFsL.js";import"./preload-helper-PPVm8Dsz.js";import"./each-BlWt3Neu.js";import"./card-title-DCJX056x.js";import"./this-Dypaan2Q.js";import"./badge-DOktaLwq.js";import"./index-KRrpyZZM.js";import"./Icon-CYtk7mac.js";import"./legacy-D7OnDY3G.js";import"./button-BbjatG8g.js";import"./label-mrAA5l7e.js";import"./save-button-_AMgjLGF.js";import"./loader-circle-DukIKDwt.js";import"./constants-a8_tPpha.js";import"./shield-C0akJcpU.js";import"./plus-Bj06M1nx.js";import"./trash-2-C9avNWSC.js";const{expect:t,userEvent:m,within:r}=__STORYBOOK_MODULE_TEST__,f={title:"Tests/NamespacePermissionsEditor Interactions",component:p,tags:["!autodocs"]},n={play:async({canvasElement:a})=>{const e=r(a);await t(e.getByText("production-data")).toBeInTheDocument(),await t(e.getByText("staging-env")).toBeInTheDocument(),await t(e.getByText("Namespace Access")).toBeInTheDocument()}},s={play:async({canvasElement:a})=>{const e=r(a),c=e.getAllByText("WRITE");await m.click(c[0]);const i=e.getByRole("button",{name:/save/i});await t(i).not.toBeDisabled()}},o={play:async({canvasElement:a})=>{const e=r(a);await t(e.getByText("staging-env")).toBeInTheDocument();const c=a.querySelectorAll('button[class*="hover:text-destructive"]');await t(c.length).toBe(2),await m.click(c[1]);const i=a.querySelectorAll('button[class*="hover:text-destructive"]');await t(i.length).toBe(1),await t(e.getByText("production-data")).toBeInTheDocument()}};n.parameters={...n.parameters,docs:{...n.parameters?.docs,source:{originalSource:`{
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
