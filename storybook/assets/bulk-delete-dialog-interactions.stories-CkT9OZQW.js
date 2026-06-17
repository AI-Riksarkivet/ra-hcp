import{i as e}from"./preload-helper-xPQekRTU.js";import{$ as t,It as n,Ot as r,Rt as i,St as a,ct as o,hn as s,ht as c,jt as l,kt as u,lt as d,rt as f,sn as p,t as m,tt as h,vn as g,zt as _}from"./client-DASBvjj6.js";import{n as v,t as y}from"./bulk-delete-dialog-B4lgkIgC.js";function b(e){let o=i(!0),s=i(!1),f=i(!1),m=i(0);function g(){_(m),n(f,!0),setTimeout(()=>{n(f,!1),n(o,!1)},500)}var v=x(),b=u(v),S=l(b,2),C=r(S);p(S),y(l(S,2),{count:5,itemType:`namespace`,get loading(){return c(f)},showForceOption:!0,onconfirm:g,get open(){return c(o)},set open(e){n(o,e,!0)},get force(){return c(s)},set force(e){n(s,e,!0)}}),a(()=>t(C,`Confirmed: ${c(m)??``}`)),d(`click`,b,()=>n(o,!0)),h(e,v)}var x,S=e((()=>{g(),s(),m(),v(),x=f(`<button class="rounded bg-destructive px-4 py-2 text-sm text-white">Open Bulk Delete Dialog</button> <div data-testid="confirm-count" class="mt-2 text-xs text-muted-foreground"> </div> <!>`,1),o([`click`]),b.__docgen={data:[],name:`bulk-delete-dialog-test-harness.svelte`}})),C,w,T,E,D,O,k,A;e((()=>{S(),{expect:C,userEvent:w,within:T}=__STORYBOOK_MODULE_TEST__,E={title:`Tests/BulkDeleteDialog Interactions`,component:b,tags:[`!autodocs`]},D={play:async({canvasElement:e})=>{let t=T(e.ownerDocument.body);await C(t.getAllByText(`Delete 5 namespaces`).length).toBeGreaterThanOrEqual(1),await C(t.getByText(`Cancel`)).toBeInTheDocument()}},O={play:async({canvasElement:e})=>{let t=T(e.ownerDocument.body),n=T(e),r=t.getByRole(`button`,{name:`Delete 5 namespaces`});await w.click(r),await new Promise(e=>setTimeout(e,600)),await C(n.getByTestId(`confirm-count`)).toHaveTextContent(`Confirmed: 1`)}},k={play:async({canvasElement:e})=>{await C(T(e.ownerDocument.body).getByText(/Force delete/)).toBeInTheDocument();let t=e.ownerDocument.querySelector(`button[role="checkbox"]`);await C(t).toBeInTheDocument(),await w.click(t),await C(t).toHaveAttribute(`data-state`,`checked`)}},D.parameters={...D.parameters,docs:{...D.parameters?.docs,source:{originalSource:`{
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
}`,...D.parameters?.docs?.source},description:{story:`Verify the dialog renders with correct plural content.`,...D.parameters?.docs?.description}}},O.parameters={...O.parameters,docs:{...O.parameters?.docs,source:{originalSource:`{
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
}`,...O.parameters?.docs?.source},description:{story:`Click confirm and verify count increments.`,...O.parameters?.docs?.description}}},k.parameters={...k.parameters,docs:{...k.parameters?.docs,source:{originalSource:`{
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
}`,...k.parameters?.docs?.source},description:{story:`Toggle force delete checkbox.`,...k.parameters?.docs?.description}}},A=[`RendersContent`,`ConfirmBulkDelete`,`ForceDeleteCheckbox`]}))();export{O as ConfirmBulkDelete,k as ForceDeleteCheckbox,D as RendersContent,A as __namedExportsOrder,E as default};