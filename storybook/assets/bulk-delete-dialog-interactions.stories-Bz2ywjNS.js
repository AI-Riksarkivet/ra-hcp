import{f as D,g as T,r as k,a as _,d as w,u as a,v as d,k as C,w as E,x as m,y as I,h as O,m as S}from"./iframe-CTm_ffW8.js";import{B as F}from"./bulk-delete-dialog-D0Lbs8y8.js";import"./preload-helper-PPVm8Dsz.js";import"./alert-dialog-description-5hDRawPw.js";import"./dialog-description-CoEWcitx.js";import"./button-Dnzsi9-9.js";import"./index-CrxHSMXN.js";import"./this-DscMLWEM.js";import"./checkbox-DiHJ9xaq.js";import"./legacy-CDXkwGSf.js";import"./input-BSg8yut6.js";import"./check-CZ3wGmvo.js";import"./Icon-CbVG816t.js";import"./each-Dcph8Tww.js";var H=C('<button class="rounded bg-destructive px-4 py-2 text-sm text-white">Open Bulk Delete Dialog</button> <div data-testid="confirm-count" class="mt-2 text-xs text-muted-foreground"> </div> <!>',1);function x(t){let e=m(!0),n=m(!1),o=m(!1),l=m(0);function p(){E(l),a(o,!0),setTimeout(()=>{a(o,!1),a(e,!1)},500)}var h=H(),b=D(h),g=w(b,2),v=S(g),B=w(g,2);F(B,{count:5,itemType:"namespace",get loading(){return d(o)},showForceOption:!0,onconfirm:p,get open(){return d(e)},set open(y){a(e,y,!0)},get force(){return d(n)},set force(y){a(n,y,!0)}}),T(()=>O(v,`Confirmed: ${d(l)??""}`)),k("click",b,()=>a(e,!0)),_(t,h)}I(["click"]);x.__docgen={data:[],name:"bulk-delete-dialog-test-harness.svelte"};const{expect:c,userEvent:f,within:u}=__STORYBOOK_MODULE_TEST__,J={title:"Tests/BulkDeleteDialog Interactions",component:x,tags:["!autodocs"]},r={play:async({canvasElement:t})=>{const e=u(t.ownerDocument.body),n=e.getAllByText("Delete 5 namespaces");await c(n.length).toBeGreaterThanOrEqual(1),await c(e.getByText("Cancel")).toBeInTheDocument()}},s={play:async({canvasElement:t})=>{const e=u(t.ownerDocument.body),n=u(t),o=e.getByRole("button",{name:"Delete 5 namespaces"});await f.click(o),await new Promise(p=>setTimeout(p,600));const l=n.getByTestId("confirm-count");await c(l).toHaveTextContent("Confirmed: 1")}},i={play:async({canvasElement:t})=>{const e=u(t.ownerDocument.body);await c(e.getByText(/Force delete/)).toBeInTheDocument();const o=t.ownerDocument.querySelector('button[role="checkbox"]');await c(o).toBeInTheDocument(),await f.click(o),await c(o).toHaveAttribute("data-state","checked")}};r.parameters={...r.parameters,docs:{...r.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    // Dialog content is portaled to document.body, outside canvasElement
    const body = within(canvasElement.ownerDocument.body);

    // Title and confirm button both contain "Delete 5 namespaces"
    const matches = body.getAllByText("Delete 5 namespaces");
    await expect(matches.length).toBeGreaterThanOrEqual(1);
    await expect(body.getByText("Cancel")).toBeInTheDocument();
  }
}`,...r.parameters?.docs?.source},description:{story:"Verify the dialog renders with correct plural content.",...r.parameters?.docs?.description}}};s.parameters={...s.parameters,docs:{...s.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const body = within(canvasElement.ownerDocument.body);
    const canvas = within(canvasElement);
    const deleteBtn = body.getByRole("button", {
      name: "Delete 5 namespaces"
    });
    await userEvent.click(deleteBtn);
    await new Promise(r => setTimeout(r, 600));
    const counter = canvas.getByTestId("confirm-count");
    await expect(counter).toHaveTextContent("Confirmed: 1");
  }
}`,...s.parameters?.docs?.source},description:{story:"Click confirm and verify count increments.",...s.parameters?.docs?.description}}};i.parameters={...i.parameters,docs:{...i.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const body = within(canvasElement.ownerDocument.body);
    await expect(body.getByText(/Force delete/)).toBeInTheDocument();
    const doc = canvasElement.ownerDocument;
    const checkbox = doc.querySelector('button[role="checkbox"]') as HTMLElement;
    await expect(checkbox).toBeInTheDocument();
    await userEvent.click(checkbox);
    await expect(checkbox).toHaveAttribute("data-state", "checked");
  }
}`,...i.parameters?.docs?.source},description:{story:"Toggle force delete checkbox.",...i.parameters?.docs?.description}}};const N=["RendersContent","ConfirmBulkDelete","ForceDeleteCheckbox"];export{s as ConfirmBulkDelete,i as ForceDeleteCheckbox,r as RendersContent,N as __namedExportsOrder,J as default};
