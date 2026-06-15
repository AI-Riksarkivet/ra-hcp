import{i as e}from"./preload-helper-xPQekRTU.js";import{$ as t,It as n,Nt as r,Ot as i,Rt as a,St as o,hn as s,ht as c,jt as l,rt as u,sn as d,t as f,tt as p,vn as m}from"./client-DASBvjj6.js";import{n as h,t as g}from"./ip-list-editor-CxbrcsJ0.js";function _(e){let s=a(r([`10.0.0.0/8`,`192.168.1.0/24`]));var u=v(),f=l(i(u),2);g(f,{label:`Allowed IPs`,get addresses(){return c(s)},set addresses(e){n(s,e,!0)}});var m=l(f,2),h=i(m);d(m),d(u),o(()=>t(h,`${c(s).length??``} address(es)`)),p(e,u)}var v,y=e((()=>{m(),s(),f(),h(),v=u(`<div class="max-w-md space-y-4 p-4"><h3 class="text-sm font-medium">IP List Editor Test Harness</h3> <!> <div data-testid="ip-count" class="text-xs text-muted-foreground"> </div></div>`),_.__docgen={data:[],name:`ip-list-editor-test-harness.svelte`}})),b,x,S,C,w,T,E,D,O,k;e((()=>{y(),{expect:b,userEvent:x,within:S}=__STORYBOOK_MODULE_TEST__,C={title:`Tests/IpListEditor Interactions`,component:_,tags:[`!autodocs`]},w={play:async({canvasElement:e})=>{let t=S(e);await b(t.getByText(`10.0.0.0/8`)).toBeInTheDocument(),await b(t.getByText(`192.168.1.0/24`)).toBeInTheDocument(),await b(t.getByTestId(`ip-count`)).toHaveTextContent(`2 address(es)`)}},T={play:async({canvasElement:e})=>{let t=S(e),n=t.getByPlaceholderText(`IP address or CIDR (e.g. 10.0.0.0/8)`);await x.type(n,`172.16.0.0/12{Enter}`),await b(t.getByText(`172.16.0.0/12`)).toBeInTheDocument(),await b(t.getByTestId(`ip-count`)).toHaveTextContent(`3 address(es)`)}},E={play:async({canvasElement:e})=>{let t=S(e),n=t.getByPlaceholderText(`IP address or CIDR (e.g. 10.0.0.0/8)`),r=t.getAllByRole(`button`)[0];await x.type(n,`10.10.10.10`),await x.click(r),await b(t.getByText(`10.10.10.10`)).toBeInTheDocument(),await b(t.getByTestId(`ip-count`)).toHaveTextContent(`3 address(es)`)}},D={play:async({canvasElement:e})=>{let t=S(e),n=t.getByPlaceholderText(`IP address or CIDR (e.g. 10.0.0.0/8)`);await x.type(n,`10.0.0.0/8{Enter}`),await b(t.getByTestId(`ip-count`)).toHaveTextContent(`2 address(es)`)}},O={play:async({canvasElement:e})=>{let t=S(e),n=S(t.getByText(`10.0.0.0/8`).closest(`[data-slot='badge']`)).getByRole(`button`);await x.click(n),await b(t.queryByText(`10.0.0.0/8`)).not.toBeInTheDocument(),await b(t.getByTestId(`ip-count`)).toHaveTextContent(`1 address(es)`)}},w.parameters={...w.parameters,docs:{...w.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText("10.0.0.0/8")).toBeInTheDocument();
    await expect(canvas.getByText("192.168.1.0/24")).toBeInTheDocument();
    await expect(canvas.getByTestId("ip-count")).toHaveTextContent("2 address(es)");
  }
}`,...w.parameters?.docs?.source},description:{story:`Verify initial addresses render correctly.`,...w.parameters?.docs?.description}}},T.parameters={...T.parameters,docs:{...T.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const input = canvas.getByPlaceholderText("IP address or CIDR (e.g. 10.0.0.0/8)");
    await userEvent.type(input, "172.16.0.0/12{Enter}");
    await expect(canvas.getByText("172.16.0.0/12")).toBeInTheDocument();
    await expect(canvas.getByTestId("ip-count")).toHaveTextContent("3 address(es)");
  }
}`,...T.parameters?.docs?.source},description:{story:`Add an IP address via Enter key.`,...T.parameters?.docs?.description}}},E.parameters={...E.parameters,docs:{...E.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const input = canvas.getByPlaceholderText("IP address or CIDR (e.g. 10.0.0.0/8)");
    // The add button has a Plus icon, find it by role
    const buttons = canvas.getAllByRole("button");
    // The + button is the one next to the input (not inside badges)
    const addButton = buttons[0];
    await userEvent.type(input, "10.10.10.10");
    await userEvent.click(addButton);
    await expect(canvas.getByText("10.10.10.10")).toBeInTheDocument();
    await expect(canvas.getByTestId("ip-count")).toHaveTextContent("3 address(es)");
  }
}`,...E.parameters?.docs?.source},description:{story:`Add an IP address via the + button.`,...E.parameters?.docs?.description}}},D.parameters={...D.parameters,docs:{...D.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const input = canvas.getByPlaceholderText("IP address or CIDR (e.g. 10.0.0.0/8)");

    // Try adding an existing address
    await userEvent.type(input, "10.0.0.0/8{Enter}");

    // Count should remain 2
    await expect(canvas.getByTestId("ip-count")).toHaveTextContent("2 address(es)");
  }
}`,...D.parameters?.docs?.source},description:{story:`Duplicate IPs should not be added.`,...D.parameters?.docs?.description}}},O.parameters={...O.parameters,docs:{...O.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);

    // Find the badge <span> containing "10.0.0.0/8" and its X button
    const badge = canvas.getByText("10.0.0.0/8").closest("[data-slot='badge']")!;
    const removeButton = within(badge as HTMLElement).getByRole("button");
    await userEvent.click(removeButton);
    await expect(canvas.queryByText("10.0.0.0/8")).not.toBeInTheDocument();
    await expect(canvas.getByTestId("ip-count")).toHaveTextContent("1 address(es)");
  }
}`,...O.parameters?.docs?.source},description:{story:`Remove an IP by clicking the X button on its badge.`,...O.parameters?.docs?.description}}},k=[`RendersInitialAddresses`,`AddIpViaEnter`,`AddIpViaButton`,`PreventsDuplicates`,`RemoveIp`]}))();export{E as AddIpViaButton,T as AddIpViaEnter,D as PreventsDuplicates,O as RemoveIp,w as RendersInitialAddresses,k as __namedExportsOrder,C as default};