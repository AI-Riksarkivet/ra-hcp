import{q as B,A as I,g as h,d as w,r as E,h as m,j as b,i as v,k as y,s as P}from"./iframe-Co2Sxuwq.js";import{I as D}from"./ip-list-editor-B63Id9Zk.js";import"./preload-helper-DLusk7T2.js";import"./each-BrD972-b.js";import"./button-BORfKT9t.js";import"./cn-_yov3II5.js";import"./index-DW9qdgWl.js";import"./this-DJ9Dm61Y.js";import"./input-Ctteer6V.js";import"./input-qmIb0F2P.js";import"./badge-DW-VITkT.js";import"./Icon-C8ul-QQv.js";import"./legacy-BC_fe1ri.js";import"./label-BUxM4hCf.js";import"./create-id-D5q5wpPz.js";import"./plus-RDtvHZAS.js";import"./x-Cs9tWfnT.js";var _=b('<div class="max-w-md space-y-4 p-4"><h3 class="text-sm font-medium">IP List Editor Test Harness</h3> <!> <div data-testid="ip-count" class="text-xs text-muted-foreground"> </div></div>');function g(e){let t=B(I(["10.0.0.0/8","192.168.1.0/24"]));var a=_(),o=v(y(a),2);D(o,{label:"Allowed IPs",get addresses(){return m(t)},set addresses(x){E(t,x,!0)}});var l=v(o,2),T=y(l);h(()=>P(T,`${m(t).length??""} address(es)`)),w(e,a)}g.__docgen={data:[],name:"ip-list-editor-test-harness.svelte"};const{expect:s,userEvent:u,within:n}=__STORYBOOK_MODULE_TEST__,Y={title:"Tests/IpListEditor Interactions",component:g,tags:["!autodocs"]},r={play:async({canvasElement:e})=>{const t=n(e);await s(t.getByText("10.0.0.0/8")).toBeInTheDocument(),await s(t.getByText("192.168.1.0/24")).toBeInTheDocument(),await s(t.getByTestId("ip-count")).toHaveTextContent("2 address(es)")}},c={play:async({canvasElement:e})=>{const t=n(e),a=t.getByPlaceholderText("IP address or CIDR (e.g. 10.0.0.0/8)");await u.type(a,"172.16.0.0/12{Enter}"),await s(t.getByText("172.16.0.0/12")).toBeInTheDocument(),await s(t.getByTestId("ip-count")).toHaveTextContent("3 address(es)")}},i={play:async({canvasElement:e})=>{const t=n(e),a=t.getByPlaceholderText("IP address or CIDR (e.g. 10.0.0.0/8)"),l=t.getAllByRole("button")[0];await u.type(a,"10.10.10.10"),await u.click(l),await s(t.getByText("10.10.10.10")).toBeInTheDocument(),await s(t.getByTestId("ip-count")).toHaveTextContent("3 address(es)")}},d={play:async({canvasElement:e})=>{const t=n(e),a=t.getByPlaceholderText("IP address or CIDR (e.g. 10.0.0.0/8)");await u.type(a,"10.0.0.0/8{Enter}"),await s(t.getByTestId("ip-count")).toHaveTextContent("2 address(es)")}},p={play:async({canvasElement:e})=>{const t=n(e),a=t.getByText("10.0.0.0/8").closest("[data-slot='badge']"),o=n(a).getByRole("button");await u.click(o),await s(t.queryByText("10.0.0.0/8")).not.toBeInTheDocument(),await s(t.getByTestId("ip-count")).toHaveTextContent("1 address(es)")}};r.parameters={...r.parameters,docs:{...r.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText("10.0.0.0/8")).toBeInTheDocument();
    await expect(canvas.getByText("192.168.1.0/24")).toBeInTheDocument();
    await expect(canvas.getByTestId("ip-count")).toHaveTextContent("2 address(es)");
  }
}`,...r.parameters?.docs?.source},description:{story:"Verify initial addresses render correctly.",...r.parameters?.docs?.description}}};c.parameters={...c.parameters,docs:{...c.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const input = canvas.getByPlaceholderText("IP address or CIDR (e.g. 10.0.0.0/8)");
    await userEvent.type(input, "172.16.0.0/12{Enter}");
    await expect(canvas.getByText("172.16.0.0/12")).toBeInTheDocument();
    await expect(canvas.getByTestId("ip-count")).toHaveTextContent("3 address(es)");
  }
}`,...c.parameters?.docs?.source},description:{story:"Add an IP address via Enter key.",...c.parameters?.docs?.description}}};i.parameters={...i.parameters,docs:{...i.parameters?.docs,source:{originalSource:`{
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
}`,...i.parameters?.docs?.source},description:{story:"Add an IP address via the + button.",...i.parameters?.docs?.description}}};d.parameters={...d.parameters,docs:{...d.parameters?.docs,source:{originalSource:`{
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
}`,...d.parameters?.docs?.source},description:{story:"Duplicate IPs should not be added.",...d.parameters?.docs?.description}}};p.parameters={...p.parameters,docs:{...p.parameters?.docs,source:{originalSource:`{
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
}`,...p.parameters?.docs?.source},description:{story:"Remove an IP by clicking the X button on its badge.",...p.parameters?.docs?.description}}};const $=["RendersInitialAddresses","AddIpViaEnter","AddIpViaButton","PreventsDuplicates","RemoveIp"];export{i as AddIpViaButton,c as AddIpViaEnter,d as PreventsDuplicates,p as RemoveIp,r as RendersInitialAddresses,$ as __namedExportsOrder,Y as default};
