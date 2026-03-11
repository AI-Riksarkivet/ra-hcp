import{o as S,d,t as P,r as n,h as i,k as f,i as b,j as _,q as B,g as H,s as U}from"./iframe-DMiptjJG.js";import{F as j}from"./form-dialog-Da-Ihxbl.js";import{I as K}from"./input-D2YdAfeF.js";import{L as M}from"./label-BCQGPmbF.js";import{B as Y}from"./button-DDYK5eOR.js";import"./preload-helper-CbY8PC0A.js";import"./dialog-description-C5xgpCfq.js";import"./scroll-lock-cV0BiRee.js";import"./is-ByncQuYD.js";import"./create-id-CWF4jc6H.js";import"./cn-_yov3II5.js";import"./dialog-description-90Yy-i_D.js";import"./this-DAsf5IBR.js";import"./x-CmHGk0MO.js";import"./legacy-Bd9v3_Zu.js";import"./Icon-Df3np04X.js";import"./each-DXFiKjeP.js";import"./error-banner-U7KgkDkc.js";import"./loader-circle-C-Js3TOj.js";import"./input-BgDHMTDQ.js";import"./index-DW9qdgWl.js";var z=_('<div data-testid="success-msg" class="text-sm text-emerald-600"> </div>'),A=_('<div class="space-y-3"><div><!> <!></div></div>'),G=_('<div class="space-y-4 p-4"><!> <!> <!></div>');function $(e){let a=B(!0),s=B(""),h=!1,c=B(!1),r=B("");function N(t){if(t.preventDefault(),!i(r).trim()){n(s,"Name is required.");return}if(i(r)==="existing"){n(s,"Namespace 'existing' already exists.");return}n(s,""),n(c,!0)}function k(){n(a,!0),n(s,""),n(c,!1),n(r,"")}var C=G(),D=f(C);{var O=t=>{Y(t,{onclick:k,"data-testid":"reopen-btn",children:(m,p)=>{var x=P("Open Dialog");d(m,x)},$$slots:{default:!0}})};S(D,t=>{i(a)||t(O)})}var I=b(D,2);{var q=t=>{var m=z(),p=f(m);H(()=>U(p,`Created namespace: ${i(r)??""}`)),d(t,m)};S(I,t=>{i(c)&&t(q)})}var F=b(I,2);j(F,{title:"Create Namespace",description:"Create a new namespace.",loading:h,get error(){return i(s)},onsubmit:N,get open(){return i(a)},set open(t){n(a,t,!0)},children:(t,m)=>{var p=A(),x=f(p),E=f(x);M(E,{for:"ns-name",children:(T,J)=>{var L=P("Name");d(T,L)},$$slots:{default:!0}});var V=b(E,2);K(V,{id:"ns-name",placeholder:"my-namespace",get value(){return i(r)},set value(T){n(r,T,!0)}}),d(t,p)},$$slots:{default:!0}}),d(e,C)}$.__docgen={data:[],name:"form-dialog-test-harness.svelte"};const{expect:o,userEvent:g,within:R}=__STORYBOOK_MODULE_TEST__,fe={title:"Tests/FormDialog Interactions",component:$,tags:["!autodocs"]};function v(){return R(document.body)}const l={play:async()=>{const e=v();await o(await e.findByText("Create Namespace")).toBeInTheDocument(),await o(await e.findByText("Create a new namespace.")).toBeInTheDocument(),await o(await e.findByPlaceholderText("my-namespace")).toBeInTheDocument(),await o(await e.findByRole("button",{name:"Create"})).toBeInTheDocument(),await o(await e.findByRole("button",{name:"Cancel"})).toBeInTheDocument()}},u={play:async()=>{const e=v(),a=await e.findByRole("button",{name:"Create"});await g.click(a),await o(await e.findByText("Name is required.")).toBeInTheDocument()}},w={play:async()=>{const e=v(),a=await e.findByPlaceholderText("my-namespace"),s=await e.findByRole("button",{name:"Create"});await g.type(a,"existing"),await g.click(s),await o(await e.findByText("Namespace 'existing' already exists.")).toBeInTheDocument()}},y={play:async({canvasElement:e})=>{const a=v(),s=R(e),h=await a.findByPlaceholderText("my-namespace"),c=await a.findByRole("button",{name:"Create"});await g.type(h,"new-namespace"),await g.click(c),await o(await s.findByTestId("success-msg")).toHaveTextContent("Created namespace: new-namespace")}};l.parameters={...l.parameters,docs:{...l.parameters?.docs,source:{originalSource:`{
  play: async () => {
    const page = getPage();

    // Use findBy* to wait for the portaled dialog content
    await expect(await page.findByText("Create Namespace")).toBeInTheDocument();
    await expect(await page.findByText("Create a new namespace.")).toBeInTheDocument();
    await expect(await page.findByPlaceholderText("my-namespace")).toBeInTheDocument();
    await expect(await page.findByRole("button", {
      name: "Create"
    })).toBeInTheDocument();
    await expect(await page.findByRole("button", {
      name: "Cancel"
    })).toBeInTheDocument();
  }
}`,...l.parameters?.docs?.source},description:{story:"Verify the dialog renders with title and description.",...l.parameters?.docs?.description}}};u.parameters={...u.parameters,docs:{...u.parameters?.docs,source:{originalSource:`{
  play: async () => {
    const page = getPage();
    const submitBtn = await page.findByRole("button", {
      name: "Create"
    });
    await userEvent.click(submitBtn);
    await expect(await page.findByText("Name is required.")).toBeInTheDocument();
  }
}`,...u.parameters?.docs?.source},description:{story:"Submit with empty name shows validation error.",...u.parameters?.docs?.description}}};w.parameters={...w.parameters,docs:{...w.parameters?.docs,source:{originalSource:`{
  play: async () => {
    const page = getPage();
    const input = await page.findByPlaceholderText("my-namespace");
    const submitBtn = await page.findByRole("button", {
      name: "Create"
    });
    await userEvent.type(input, "existing");
    await userEvent.click(submitBtn);
    await expect(await page.findByText("Namespace 'existing' already exists.")).toBeInTheDocument();
  }
}`,...w.parameters?.docs?.source},description:{story:"Submit with duplicate name shows conflict error.",...w.parameters?.docs?.description}}};y.parameters={...y.parameters,docs:{...y.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const page = getPage();
    const canvas = within(canvasElement);
    const input = await page.findByPlaceholderText("my-namespace");
    const submitBtn = await page.findByRole("button", {
      name: "Create"
    });
    await userEvent.type(input, "new-namespace");
    await userEvent.click(submitBtn);

    // Success message renders in the harness (inside canvasElement), not the dialog
    await expect(await canvas.findByTestId("success-msg")).toHaveTextContent("Created namespace: new-namespace");
  }
}`,...y.parameters?.docs?.source},description:{story:"Successful submission shows success message.",...y.parameters?.docs?.description}}};const Be=["RendersDialog","ValidationError","ConflictError","SuccessfulSubmit"];export{w as ConflictError,l as RendersDialog,y as SuccessfulSubmit,u as ValidationError,Be as __namedExportsOrder,fe as default};
