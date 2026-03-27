import{f as v,g as B,r as k,a as _,d as w,u as a,v as m,k as C,w as I,x as l,y as E,h as O,m as R}from"./iframe-CTm_ffW8.js";import{D as S}from"./delete-confirm-dialog-BUh8W_U5.js";import"./preload-helper-PPVm8Dsz.js";import"./alert-dialog-description-5hDRawPw.js";import"./dialog-description-CoEWcitx.js";import"./button-Dnzsi9-9.js";import"./index-CrxHSMXN.js";import"./this-DscMLWEM.js";import"./checkbox-DiHJ9xaq.js";import"./legacy-CDXkwGSf.js";import"./input-BSg8yut6.js";import"./check-CZ3wGmvo.js";import"./Icon-CbVG816t.js";import"./each-Dcph8Tww.js";var F=C('<button class="rounded bg-destructive px-4 py-2 text-sm text-white">Open Delete Dialog</button> <div data-testid="confirm-count" class="mt-2 text-xs text-muted-foreground"> </div> <!>',1);function x(t){let e=l(!0),c=l(!1),o=l(!1),d=l(0);function p(){I(d),a(o,!0),setTimeout(()=>{a(o,!1),a(e,!1)},500)}var b=F(),h=v(b),g=w(h,2),D=R(g),T=w(g,2);S(T,{name:"production-data",itemType:"namespace",get loading(){return m(o)},showForceOption:!0,onconfirm:p,get open(){return m(e)},set open(y){a(e,y,!0)},get force(){return m(c)},set force(y){a(c,y,!0)}}),B(()=>O(D,`Confirmed: ${m(d)??""}`)),k("click",h,()=>a(e,!0)),_(t,b)}E(["click"]);x.__docgen={data:[],name:"delete-confirm-dialog-test-harness.svelte"};const{expect:n,userEvent:f,within:u}=__STORYBOOK_MODULE_TEST__,G={title:"Tests/DeleteConfirmDialog Interactions",component:x,tags:["!autodocs"]},r={play:async({canvasElement:t})=>{const e=u(t.ownerDocument.body);await n(e.getByText("Delete namespace")).toBeInTheDocument(),await n(e.getByText(/production-data/)).toBeInTheDocument(),await n(e.getByText("Cancel")).toBeInTheDocument(),await n(e.getByRole("button",{name:"Delete"})).toBeInTheDocument()}},s={play:async({canvasElement:t})=>{const e=u(t.ownerDocument.body),c=u(t),o=e.getByRole("button",{name:"Delete"});await f.click(o),await new Promise(p=>setTimeout(p,600));const d=c.getByTestId("confirm-count");await n(d).toHaveTextContent("Confirmed: 1")}},i={play:async({canvasElement:t})=>{const e=u(t.ownerDocument.body);await n(e.getByText(/Force delete/)).toBeInTheDocument();const o=t.ownerDocument.querySelector('button[role="checkbox"]');await n(o).toBeInTheDocument(),await f.click(o),await n(o).toHaveAttribute("data-state","checked")}};r.parameters={...r.parameters,docs:{...r.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    // Dialog content is portaled to document.body, outside canvasElement
    const body = within(canvasElement.ownerDocument.body);
    await expect(body.getByText("Delete namespace")).toBeInTheDocument();
    await expect(body.getByText(/production-data/)).toBeInTheDocument();
    await expect(body.getByText("Cancel")).toBeInTheDocument();
    await expect(body.getByRole("button", {
      name: "Delete"
    })).toBeInTheDocument();
  }
}`,...r.parameters?.docs?.source},description:{story:"Verify the dialog renders with correct content.",...r.parameters?.docs?.description}}};s.parameters={...s.parameters,docs:{...s.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const body = within(canvasElement.ownerDocument.body);
    const canvas = within(canvasElement);
    const deleteBtn = body.getByRole("button", {
      name: "Delete"
    });
    await userEvent.click(deleteBtn);

    // Wait for loading to complete and dialog to close
    await new Promise(r => setTimeout(r, 600));
    const counter = canvas.getByTestId("confirm-count");
    await expect(counter).toHaveTextContent("Confirmed: 1");
  }
}`,...s.parameters?.docs?.source},description:{story:"Click Delete and verify confirm count increments.",...s.parameters?.docs?.description}}};i.parameters={...i.parameters,docs:{...i.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const body = within(canvasElement.ownerDocument.body);
    await expect(body.getByText(/Force delete/)).toBeInTheDocument();

    // Find and click the checkbox (portaled to document body)
    const doc = canvasElement.ownerDocument;
    const checkbox = doc.querySelector('button[role="checkbox"]') as HTMLElement;
    await expect(checkbox).toBeInTheDocument();
    await userEvent.click(checkbox);

    // Checkbox should now be checked
    await expect(checkbox).toHaveAttribute("data-state", "checked");
  }
}`,...i.parameters?.docs?.source},description:{story:"Verify force delete checkbox is present and toggleable.",...i.parameters?.docs?.description}}};const J=["RendersContent","ConfirmDelete","ForceDeleteCheckbox"];export{s as ConfirmDelete,i as ForceDeleteCheckbox,r as RendersContent,J as __namedExportsOrder,G as default};
