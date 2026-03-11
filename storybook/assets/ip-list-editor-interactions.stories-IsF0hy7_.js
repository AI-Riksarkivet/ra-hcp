import{r as x,B as I,g as h,d as w,v as E,h as m,k as b,i as v,m as y,s as P}from"./iframe-0B4E8QaP.js";import{I as D}from"./ip-list-editor-Dx3g8-ha.js";import"./preload-helper-PPVm8Dsz.js";import"./cn-CukO2arH.js";import"./button-DjEAsAUk.js";import"./index-CR3ZhuFD.js";import"./Icon-D_OA0LUw.js";import"./legacy-BIjO5Qzi.js";import"./input--FKDjf7t.js";import"./input-BvX2LBTw.js";import"./badge-DP7wdP4t.js";import"./label-YdVkTYBi.js";import"./create-id-CPYsmAkK.js";import"./plus-YYxNWKok.js";import"./x-Dz3ueVpA.js";var _=b('<div class="max-w-md space-y-4 p-4"><h3 class="text-sm font-medium">IP List Editor Test Harness</h3> <!> <div data-testid="ip-count" class="text-xs text-muted-foreground"> </div></div>');function g(e){let t=x(I(["10.0.0.0/8","192.168.1.0/24"]));var a=_(),o=v(y(a),2);D(o,{label:"Allowed IPs",get addresses(){return m(t)},set addresses(B){E(t,B,!0)}});var l=v(o,2),T=y(l);h(()=>P(T,`${m(t).length??""} address(es)`)),w(e,a)}g.__docgen={data:[],name:"ip-list-editor-test-harness.svelte"};const{expect:s,userEvent:u,within:n}=__STORYBOOK_MODULE_TEST__,U={title:"Tests/IpListEditor Interactions",component:g,tags:["!autodocs"]},r={play:async({canvasElement:e})=>{const t=n(e);await s(t.getByText("10.0.0.0/8")).toBeInTheDocument(),await s(t.getByText("192.168.1.0/24")).toBeInTheDocument(),await s(t.getByTestId("ip-count")).toHaveTextContent("2 address(es)")}},c={play:async({canvasElement:e})=>{const t=n(e),a=t.getByPlaceholderText("IP address or CIDR (e.g. 10.0.0.0/8)");await u.type(a,"172.16.0.0/12{Enter}"),await s(t.getByText("172.16.0.0/12")).toBeInTheDocument(),await s(t.getByTestId("ip-count")).toHaveTextContent("3 address(es)")}},i={play:async({canvasElement:e})=>{const t=n(e),a=t.getByPlaceholderText("IP address or CIDR (e.g. 10.0.0.0/8)"),l=t.getAllByRole("button")[0];await u.type(a,"10.10.10.10"),await u.click(l),await s(t.getByText("10.10.10.10")).toBeInTheDocument(),await s(t.getByTestId("ip-count")).toHaveTextContent("3 address(es)")}},d={play:async({canvasElement:e})=>{const t=n(e),a=t.getByPlaceholderText("IP address or CIDR (e.g. 10.0.0.0/8)");await u.type(a,"10.0.0.0/8{Enter}"),await s(t.getByTestId("ip-count")).toHaveTextContent("2 address(es)")}},p={play:async({canvasElement:e})=>{const t=n(e),a=t.getByText("10.0.0.0/8").closest("[data-slot='badge']"),o=n(a).getByRole("button");await u.click(o),await s(t.queryByText("10.0.0.0/8")).not.toBeInTheDocument(),await s(t.getByTestId("ip-count")).toHaveTextContent("1 address(es)")}};r.parameters={...r.parameters,docs:{...r.parameters?.docs,source:{originalSource:`{
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
}`,...p.parameters?.docs?.source},description:{story:"Remove an IP by clicking the X button on its badge.",...p.parameters?.docs?.description}}};const Y=["RendersInitialAddresses","AddIpViaEnter","AddIpViaButton","PreventsDuplicates","RemoveIp"];export{i as AddIpViaButton,c as AddIpViaEnter,d as PreventsDuplicates,p as RemoveIp,r as RendersInitialAddresses,Y as __namedExportsOrder,U as default};
