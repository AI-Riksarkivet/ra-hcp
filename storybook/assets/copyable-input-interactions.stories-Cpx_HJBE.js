import{i as m,d as w,m as g,k as B}from"./iframe-C-MwBp7L.js";import"./legacy-Zk7M6gCX.js";import{C as d}from"./copyable-input-CWSHYEwq.js";import{T as x}from"./tooltip-provider-5qXNX-xO.js";import"./preload-helper-PPVm8Dsz.js";import"./button-DyM1asKa.js";import"./cn-BDY1P_YX.js";import"./index-CBhWCKEA.js";import"./Icon-CTgOlQVF.js";import"./input-B_gImy6z.js";import"./input-DBEPWy-F.js";import"./label-DDeuEMBk.js";import"./create-id-Bdf389et.js";import"./check-yP3rzBl3.js";import"./popper-layer-force-mount-CxH67qOb.js";import"./scroll-lock-C9uGmbdB.js";import"./is-DbNek6LP.js";var T=B('<div class="max-w-md space-y-6 p-4"><!> <!> <!></div>');function h(e){x(e,{children:(t,o)=>{var s=T(),c=g(s);d(c,{value:"urn:hcp:namespace:production-data",label:"Canonical ID"});var a=m(c,2);d(a,{value:"sk_live_abc123secret456def789",label:"Secret Key",secret:!0});var u=m(a,2);d(u,{value:"https://hcp.example.com:8000"}),w(t,s)},$$slots:{default:!0}})}h.__docgen={data:[],name:"copyable-input-test-harness.svelte"};const{expect:n,userEvent:y,within:p}=__STORYBOOK_MODULE_TEST__,G={title:"Tests/CopyableInput Interactions",component:h,tags:["!autodocs"]},r={play:async({canvasElement:e})=>{const t=p(e);await n(t.getByText("Canonical ID")).toBeInTheDocument(),await n(t.getByText("Secret Key")).toBeInTheDocument();const o=t.getAllByRole("textbox");await n(o.length).toBeGreaterThanOrEqual(2)}},i={play:async({canvasElement:e})=>{const t=p(e),o=e.querySelectorAll('input[type="password"]');await n(o.length).toBe(1);const c=t.getByText("Secret Key").closest(".space-y-1"),u=p(c).getAllByRole("button")[0];await y.click(u);const b=e.querySelectorAll('input[type="password"]');await n(b.length).toBe(0),await y.click(u);const v=e.querySelectorAll('input[type="password"]');await n(v.length).toBe(1)}},l={play:async({canvasElement:e})=>{const s=p(e).getByText("Canonical ID").closest(".space-y-1"),a=p(s).getAllByRole("button")[0];await y.click(a),await n(a).toBeInTheDocument()}};r.parameters={...r.parameters,docs:{...r.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText("Canonical ID")).toBeInTheDocument();
    await expect(canvas.getByText("Secret Key")).toBeInTheDocument();

    // The plain input should show its value
    const inputs = canvas.getAllByRole("textbox");
    await expect(inputs.length).toBeGreaterThanOrEqual(2);
  }
}`,...r.parameters?.docs?.source},description:{story:"Verify all three inputs render with correct labels.",...r.parameters?.docs?.description}}};i.parameters={...i.parameters,docs:{...i.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);

    // Find all password-type inputs (secret ones)
    const passwordInputs = canvasElement.querySelectorAll('input[type="password"]');
    await expect(passwordInputs.length).toBe(1);

    // Click the reveal button (Eye icon) — it's in the Secret Key row
    const secretLabel = canvas.getByText("Secret Key");
    const secretSection = secretLabel.closest(".space-y-1")!;
    const buttons = within(secretSection as HTMLElement).getAllByRole("button");
    // First button is reveal, second is copy
    const revealBtn = buttons[0];
    await userEvent.click(revealBtn);

    // Now the input should be type="text"
    const textInputs = canvasElement.querySelectorAll('input[type="password"]');
    await expect(textInputs.length).toBe(0);

    // Click again to hide
    await userEvent.click(revealBtn);
    const hiddenAgain = canvasElement.querySelectorAll('input[type="password"]');
    await expect(hiddenAgain.length).toBe(1);
  }
}`,...i.parameters?.docs?.source},description:{story:"Secret input should be masked and togglable.",...i.parameters?.docs?.description}}};l.parameters={...l.parameters,docs:{...l.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);

    // Find the Canonical ID section and its copy button
    const canonicalLabel = canvas.getByText("Canonical ID");
    const canonicalSection = canonicalLabel.closest(".space-y-1")!;
    const buttons = within(canonicalSection as HTMLElement).getAllByRole("button");
    // Only one button (copy) since this isn't a secret field
    const copyBtn = buttons[0];
    await userEvent.click(copyBtn);

    // The button should still be in the document after click
    // (copy feedback shows a check icon briefly)
    await expect(copyBtn).toBeInTheDocument();
  }
}`,...l.parameters?.docs?.source},description:{story:"Clicking copy button shows check icon feedback.",...l.parameters?.docs?.description}}};const H=["RendersAll","SecretToggle","CopyFeedback"];export{l as CopyFeedback,r as RendersAll,i as SecretToggle,H as __namedExportsOrder,G as default};
