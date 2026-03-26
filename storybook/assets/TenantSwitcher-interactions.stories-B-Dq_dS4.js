import{a as u,m as h,k as w}from"./iframe-DFtYtFsL.js";import"./legacy-D7OnDY3G.js";import{T as v}from"./TenantSwitcher-CTX4fQ86.js";import"./preload-helper-PPVm8Dsz.js";import"./each-BlWt3Neu.js";import"./dropdown-menu-trigger-HXMOkr-0.js";import"./this-Dypaan2Q.js";import"./badge-DOktaLwq.js";import"./index-KRrpyZZM.js";import"./Icon-CYtk7mac.js";import"./button-BbjatG8g.js";import"./plus-Bj06M1nx.js";import"./building-2-Dp6dhOqb.js";var l=w('<div class="p-4"><!></div>');function m(t){const s=Math.floor(Date.now()/1e3),n=s+3600*4,e=s-3600,y=[{tenant:"dev-ai",username:"admin",exp:n,expired:!1,cookieName:"hcp_token__dev-ai__admin",isActive:!0},{tenant:"prod-ai",username:"admin",exp:n,expired:!1,cookieName:"hcp_token__prod-ai__admin",isActive:!1},{tenant:"staging",username:"operator",exp:e,expired:!0,cookieName:"hcp_token__staging__operator",isActive:!1}];var p=l(),g=h(p);v(g,{get sessions(){return y},currentTenant:"dev-ai"}),u(t,p)}m.__docgen={data:[],name:"TenantSwitcher-test-harness.svelte"};const{expect:o,userEvent:d,within:a}=__STORYBOOK_MODULE_TEST__,O={title:"Tests/TenantSwitcher Interactions",component:m,tags:["!autodocs"]},i={play:async({canvasElement:t})=>{const n=a(t).getByRole("button",{name:/dev-ai/i});await d.click(n);const e=a(t.ownerDocument.body);await o(e.getByText("Tenant Sessions")).toBeInTheDocument(),await o(e.getByText("prod-ai")).toBeInTheDocument(),await o(e.getByText("staging")).toBeInTheDocument()}},r={play:async({canvasElement:t})=>{const n=a(t).getByRole("button",{name:/dev-ai/i});await d.click(n,{pointerEventsCheck:0});const e=a(t.ownerDocument.body);await o(e.getByText("Active")).toBeInTheDocument(),await o(e.getByText("Switch")).toBeInTheDocument(),await o(e.getByText("Expired")).toBeInTheDocument()}},c={play:async({canvasElement:t})=>{const n=a(t).getByRole("button",{name:/dev-ai/i});await d.click(n,{pointerEventsCheck:0});const e=a(t.ownerDocument.body);await o(e.getByText("Add another tenant")).toBeInTheDocument()}};i.parameters={...i.parameters,docs:{...i.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);

    // Click the trigger button to open the dropdown
    const trigger = canvas.getByRole("button", {
      name: /dev-ai/i
    });
    await userEvent.click(trigger);

    // Dropdown content is portaled to document.body
    const body = within(canvasElement.ownerDocument.body);

    // Verify sessions are listed
    await expect(body.getByText("Tenant Sessions")).toBeInTheDocument();
    await expect(body.getByText("prod-ai")).toBeInTheDocument();
    await expect(body.getByText("staging")).toBeInTheDocument();
  }
}`,...i.parameters?.docs?.source},description:{story:"Open the dropdown and verify all sessions are listed.",...i.parameters?.docs?.description}}};r.parameters={...r.parameters,docs:{...r.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const trigger = canvas.getByRole("button", {
      name: /dev-ai/i
    });
    await userEvent.click(trigger, {
      pointerEventsCheck: 0
    });
    const body = within(canvasElement.ownerDocument.body);
    await expect(body.getByText("Active")).toBeInTheDocument();
    await expect(body.getByText("Switch")).toBeInTheDocument();
    await expect(body.getByText("Expired")).toBeInTheDocument();
  }
}`,...r.parameters?.docs?.source},description:{story:"Verify badge states (Active, Switch, Expired).",...r.parameters?.docs?.description}}};c.parameters={...c.parameters,docs:{...c.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const trigger = canvas.getByRole("button", {
      name: /dev-ai/i
    });
    await userEvent.click(trigger, {
      pointerEventsCheck: 0
    });
    const body = within(canvasElement.ownerDocument.body);
    await expect(body.getByText("Add another tenant")).toBeInTheDocument();
  }
}`,...c.parameters?.docs?.source},description:{story:'Verify "Add another tenant" option is present.',...c.parameters?.docs?.description}}};const C=["ShowsSessions","ShowsBadgeStates","ShowsAddTenant"];export{c as ShowsAddTenant,r as ShowsBadgeStates,i as ShowsSessions,C as __namedExportsOrder,O as default};
