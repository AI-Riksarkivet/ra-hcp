import{i as e}from"./preload-helper-xPQekRTU.js";import{$ as t,H as n,It as r,Ot as i,Rt as a,St as o,hn as s,ht as c,jt as l,on as u,rt as d,sn as f,st as p,t as m,tt as h,vn as g}from"./client-DASBvjj6.js";import{n as _,t as v}from"./button-CsKmZasc.js";import{n as y,t as b}from"./input-CBTYUk1q.js";import{n as x,t as S}from"./label-CrdgXbxH.js";import{n as C,t as w}from"./form-dialog-NMI6p7UY.js";function T(e){let s=a(!0),d=a(``),m=a(!1),g=a(``);function v(e){if(e.preventDefault(),!c(g).trim()){r(d,`Name is required.`);return}if(c(g)===`existing`){r(d,`Namespace 'existing' already exists.`);return}r(d,``),r(m,!0)}function b(){r(s,!0),r(d,``),r(m,!1),r(g,``)}var S=O(),C=i(S),T=e=>{_(e,{onclick:b,"data-testid":`reopen-btn`,children:(e,t)=>{u(),h(e,p(`Open Dialog`))},$$slots:{default:!0}})};n(C,e=>{c(s)||e(T)});var k=l(C,2),A=e=>{var n=E(),r=i(n);f(n),o(()=>t(r,`Created namespace: ${c(g)??``}`)),h(e,n)};n(k,e=>{c(m)&&e(A)}),w(l(k,2),{title:`Create Namespace`,description:`Create a new namespace.`,loading:!1,get error(){return c(d)},onsubmit:v,get open(){return c(s)},set open(e){r(s,e,!0)},children:(e,t)=>{var n=D(),a=i(n),o=i(a);x(o,{for:`ns-name`,children:(e,t)=>{u(),h(e,p(`Name`))},$$slots:{default:!0}}),y(l(o,2),{id:`ns-name`,placeholder:`my-namespace`,get value(){return c(g)},set value(e){r(g,e,!0)}}),f(a),f(n),h(e,n)},$$slots:{default:!0}}),f(S),h(e,S)}var E,D,O,k=e((()=>{g(),s(),m(),C(),b(),S(),v(),E=d(`<div data-testid="success-msg" class="text-sm text-emerald-600"> </div>`),D=d(`<div class="space-y-3"><div><!> <!></div></div>`),O=d(`<div class="space-y-4 p-4"><!> <!> <!></div>`),T.__docgen={data:[],name:`form-dialog-test-harness.svelte`}}));function A(){return N(document.body)}var j,M,N,P,F,I,L,R,z;e((()=>{k(),{expect:j,userEvent:M,within:N}=__STORYBOOK_MODULE_TEST__,P={title:`Tests/FormDialog Interactions`,component:T,tags:[`!autodocs`]},F={play:async()=>{let e=A();await j(await e.findByText(`Create Namespace`)).toBeInTheDocument(),await j(await e.findByText(`Create a new namespace.`)).toBeInTheDocument(),await j(await e.findByPlaceholderText(`my-namespace`)).toBeInTheDocument(),await j(await e.findByRole(`button`,{name:`Create`})).toBeInTheDocument(),await j(await e.findByRole(`button`,{name:`Cancel`})).toBeInTheDocument()}},I={play:async()=>{let e=A(),t=await e.findByRole(`button`,{name:`Create`});await M.click(t),await j(await e.findByText(`Name is required.`)).toBeInTheDocument()}},L={play:async()=>{let e=A(),t=await e.findByPlaceholderText(`my-namespace`),n=await e.findByRole(`button`,{name:`Create`});await M.type(t,`existing`),await M.click(n),await j(await e.findByText(`Namespace 'existing' already exists.`)).toBeInTheDocument()}},R={play:async({canvasElement:e})=>{let t=A(),n=N(e),r=await t.findByPlaceholderText(`my-namespace`),i=await t.findByRole(`button`,{name:`Create`});await M.type(r,`new-namespace`),await M.click(i),await j(await n.findByTestId(`success-msg`)).toHaveTextContent(`Created namespace: new-namespace`)}},F.parameters={...F.parameters,docs:{...F.parameters?.docs,source:{originalSource:`{
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
}`,...F.parameters?.docs?.source},description:{story:`Verify the dialog renders with title and description.`,...F.parameters?.docs?.description}}},I.parameters={...I.parameters,docs:{...I.parameters?.docs,source:{originalSource:`{
  play: async () => {
    const page = getPage();
    const submitBtn = await page.findByRole("button", {
      name: "Create"
    });
    await userEvent.click(submitBtn);
    await expect(await page.findByText("Name is required.")).toBeInTheDocument();
  }
}`,...I.parameters?.docs?.source},description:{story:`Submit with empty name shows validation error.`,...I.parameters?.docs?.description}}},L.parameters={...L.parameters,docs:{...L.parameters?.docs,source:{originalSource:`{
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
}`,...L.parameters?.docs?.source},description:{story:`Submit with duplicate name shows conflict error.`,...L.parameters?.docs?.description}}},R.parameters={...R.parameters,docs:{...R.parameters?.docs,source:{originalSource:`{
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
}`,...R.parameters?.docs?.source},description:{story:`Successful submission shows success message.`,...R.parameters?.docs?.description}}},z=[`RendersDialog`,`ValidationError`,`ConflictError`,`SuccessfulSubmit`]}))();export{L as ConflictError,F as RendersDialog,R as SuccessfulSubmit,I as ValidationError,z as __namedExportsOrder,P as default};