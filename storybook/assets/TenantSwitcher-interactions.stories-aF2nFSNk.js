import{i as e}from"./preload-helper-xPQekRTU.js";import{Ot as t,hn as n,rt as r,sn as i,t as a,tt as o,vn as s}from"./client-DASBvjj6.js";import{rt as c}from"./iframe-BxaPFNW1.js";import{n as l,t as u}from"./TenantSwitcher-FANqj6z1.js";function d(e){let n=Math.floor(Date.now()/1e3),r=n+3600*4,a=n-3600,s=[{tenant:`dev-ai`,username:`admin`,exp:r,expired:!1,cookieName:`hcp_token__dev-ai__admin`,isActive:!0},{tenant:`prod-ai`,username:`admin`,exp:r,expired:!1,cookieName:`hcp_token__prod-ai__admin`,isActive:!1},{tenant:`staging`,username:`operator`,exp:a,expired:!0,cookieName:`hcp_token__staging__operator`,isActive:!1}];var c=f();u(t(c),{get sessions(){return s},currentTenant:`dev-ai`}),i(c),o(e,c)}var f,p=e((()=>{s(),c(),n(),a(),l(),f=r(`<div class="p-4"><!></div>`),d.__docgen={data:[],name:`TenantSwitcher-test-harness.svelte`}})),m,h,g,_,v,y,b,x;e((()=>{p(),{expect:m,userEvent:h,within:g}=__STORYBOOK_MODULE_TEST__,_={title:`Tests/TenantSwitcher Interactions`,component:d,tags:[`!autodocs`]},v={play:async({canvasElement:e})=>{let t=g(e).getByRole(`button`,{name:/dev-ai/i});await h.click(t);let n=g(e.ownerDocument.body);await m(n.getByText(`Tenant Sessions`)).toBeInTheDocument(),await m(n.getByText(`prod-ai`)).toBeInTheDocument(),await m(n.getByText(`staging`)).toBeInTheDocument()}},y={play:async({canvasElement:e})=>{let t=g(e).getByRole(`button`,{name:/dev-ai/i});await h.click(t,{pointerEventsCheck:0});let n=g(e.ownerDocument.body);await m(n.getByText(`Active`)).toBeInTheDocument(),await m(n.getByText(`Switch`)).toBeInTheDocument(),await m(n.getByText(`Expired`)).toBeInTheDocument()}},b={play:async({canvasElement:e})=>{let t=g(e).getByRole(`button`,{name:/dev-ai/i});await h.click(t,{pointerEventsCheck:0}),await m(g(e.ownerDocument.body).getByText(`Add another tenant`)).toBeInTheDocument()}},v.parameters={...v.parameters,docs:{...v.parameters?.docs,source:{originalSource:`{
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
}`,...v.parameters?.docs?.source},description:{story:`Open the dropdown and verify all sessions are listed.`,...v.parameters?.docs?.description}}},y.parameters={...y.parameters,docs:{...y.parameters?.docs,source:{originalSource:`{
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
}`,...y.parameters?.docs?.source},description:{story:`Verify badge states (Active, Switch, Expired).`,...y.parameters?.docs?.description}}},b.parameters={...b.parameters,docs:{...b.parameters?.docs,source:{originalSource:`{
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
}`,...b.parameters?.docs?.source},description:{story:`Verify "Add another tenant" option is present.`,...b.parameters?.docs?.description}}},x=[`ShowsSessions`,`ShowsBadgeStates`,`ShowsAddTenant`]}))();export{b as ShowsAddTenant,y as ShowsBadgeStates,v as ShowsSessions,x as __namedExportsOrder,_ as default};