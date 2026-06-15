import{i as e}from"./preload-helper-xPQekRTU.js";import{Ot as t,hn as n,jt as r,rt as i,sn as a,t as o,tt as s,vn as c}from"./client-DASBvjj6.js";import{n as l,rt as u,t as d}from"./iframe-LZv_KwsN.js";import{n as f,t as p}from"./copyable-input-zeyk7Za2.js";function m(e){l(e,{children:(e,n)=>{var i=h(),o=t(i);p(o,{value:`urn:hcp:namespace:production-data`,label:`Canonical ID`});var c=r(o,2);p(c,{value:`sk_live_abc123secret456def789`,label:`Secret Key`,secret:!0}),p(r(c,2),{value:`https://hcp.example.com:8000`}),a(i),s(e,i)},$$slots:{default:!0}})}var h,g=e((()=>{c(),u(),n(),o(),f(),d(),h=i(`<div class="max-w-md space-y-6 p-4"><!> <!> <!></div>`),m.__docgen={data:[],name:`copyable-input-test-harness.svelte`}})),_,v,y,b,x,S,C,w;e((()=>{g(),{expect:_,userEvent:v,within:y}=__STORYBOOK_MODULE_TEST__,b={title:`Tests/CopyableInput Interactions`,component:m,tags:[`!autodocs`]},x={play:async({canvasElement:e})=>{let t=y(e);await _(t.getByText(`Canonical ID`)).toBeInTheDocument(),await _(t.getByText(`Secret Key`)).toBeInTheDocument(),await _(t.getAllByRole(`textbox`).length).toBeGreaterThanOrEqual(2)}},S={play:async({canvasElement:e})=>{let t=y(e);await _(e.querySelectorAll(`input[type="password"]`).length).toBe(1);let n=y(t.getByText(`Secret Key`).closest(`.space-y-1`)).getAllByRole(`button`)[0];await v.click(n),await _(e.querySelectorAll(`input[type="password"]`).length).toBe(0),await v.click(n),await _(e.querySelectorAll(`input[type="password"]`).length).toBe(1)}},C={play:async({canvasElement:e})=>{let t=y(y(e).getByText(`Canonical ID`).closest(`.space-y-1`)).getAllByRole(`button`)[0];await v.click(t),await _(t).toBeInTheDocument()}},x.parameters={...x.parameters,docs:{...x.parameters?.docs,source:{originalSource:`{
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
}`,...x.parameters?.docs?.source},description:{story:`Verify all three inputs render with correct labels.`,...x.parameters?.docs?.description}}},S.parameters={...S.parameters,docs:{...S.parameters?.docs,source:{originalSource:`{
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
}`,...S.parameters?.docs?.source},description:{story:`Secret input should be masked and togglable.`,...S.parameters?.docs?.description}}},C.parameters={...C.parameters,docs:{...C.parameters?.docs,source:{originalSource:`{
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
}`,...C.parameters?.docs?.source},description:{story:`Clicking copy button shows check icon feedback.`,...C.parameters?.docs?.description}}},w=[`RendersAll`,`SecretToggle`,`CopyFeedback`]}))();export{C as CopyFeedback,x as RendersAll,S as SecretToggle,w as __namedExportsOrder,b as default};