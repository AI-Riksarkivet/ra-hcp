import{i as e}from"./preload-helper-xPQekRTU.js";import{$ as t,It as n,Nt as r,Ot as i,Rt as a,St as o,hn as s,ht as c,jt as l,rt as u,sn as d,t as f,tt as p,vn as m}from"./client-DASBvjj6.js";import{n as h,t as g}from"./tag-input-CRxAzneN.js";function _(e){let s=a(r([`production`,`critical`,`eu-west`]));var u=v(),f=l(i(u),2);g(f,{placeholder:`Add tag...`,get tags(){return c(s)},set tags(e){n(s,e,!0)}});var m=l(f,2),h=i(m);d(m),d(u),o(()=>t(h,`${c(s).length??``} tag(s)`)),p(e,u)}var v,y=e((()=>{m(),s(),f(),h(),v=u(`<div class="max-w-md space-y-4 p-4"><h3 class="text-sm font-medium">Tag Input Test Harness</h3> <!> <div data-testid="tag-count" class="text-xs text-muted-foreground"> </div></div>`),_.__docgen={data:[],name:`tag-input-test-harness.svelte`}})),b,x,S,C,w,T,E,D,O,k;e((()=>{y(),{expect:b,userEvent:x,within:S}=__STORYBOOK_MODULE_TEST__,C={title:`Tests/TagInput Interactions`,component:_,tags:[`!autodocs`]},w={play:async({canvasElement:e})=>{let t=S(e);await b(t.getByText(`production`)).toBeInTheDocument(),await b(t.getByText(`critical`)).toBeInTheDocument(),await b(t.getByText(`eu-west`)).toBeInTheDocument(),await b(t.getByTestId(`tag-count`)).toHaveTextContent(`3 tag(s)`)}},T={play:async({canvasElement:e})=>{let t=S(e),n=t.getByPlaceholderText(`Add tag...`);await x.type(n,`new-tag{Enter}`),await b(t.getByText(`new-tag`)).toBeInTheDocument(),await b(t.getByTestId(`tag-count`)).toHaveTextContent(`4 tag(s)`)}},E={play:async({canvasElement:e})=>{let t=S(e),n=t.getByPlaceholderText(`Add tag...`),r=t.getByRole(`button`,{name:`Add`});await x.type(n,`button-tag`),await x.click(r),await b(t.getByText(`button-tag`)).toBeInTheDocument(),await b(t.getByTestId(`tag-count`)).toHaveTextContent(`4 tag(s)`)}},D={play:async({canvasElement:e})=>{let t=S(e),n=t.getByPlaceholderText(`Add tag...`);await x.type(n,`production{Enter}`),await b(t.getByTestId(`tag-count`)).toHaveTextContent(`3 tag(s)`)}},O={play:async({canvasElement:e})=>{let t=S(e),n=S(t.getByText(`critical`).closest(`[data-slot='badge']`)).getByRole(`button`);await x.click(n),await b(t.queryByText(`critical`)).not.toBeInTheDocument(),await b(t.getByTestId(`tag-count`)).toHaveTextContent(`2 tag(s)`)}},w.parameters={...w.parameters,docs:{...w.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText("production")).toBeInTheDocument();
    await expect(canvas.getByText("critical")).toBeInTheDocument();
    await expect(canvas.getByText("eu-west")).toBeInTheDocument();
    await expect(canvas.getByTestId("tag-count")).toHaveTextContent("3 tag(s)");
  }
}`,...w.parameters?.docs?.source},description:{story:`Verify initial tags render correctly.`,...w.parameters?.docs?.description}}},T.parameters={...T.parameters,docs:{...T.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const input = canvas.getByPlaceholderText("Add tag...");
    await userEvent.type(input, "new-tag{Enter}");
    await expect(canvas.getByText("new-tag")).toBeInTheDocument();
    await expect(canvas.getByTestId("tag-count")).toHaveTextContent("4 tag(s)");
  }
}`,...T.parameters?.docs?.source},description:{story:`Type a new tag and press Enter to add it.`,...T.parameters?.docs?.description}}},E.parameters={...E.parameters,docs:{...E.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const input = canvas.getByPlaceholderText("Add tag...");
    const addButton = canvas.getByRole("button", {
      name: "Add"
    });
    await userEvent.type(input, "button-tag");
    await userEvent.click(addButton);
    await expect(canvas.getByText("button-tag")).toBeInTheDocument();
    await expect(canvas.getByTestId("tag-count")).toHaveTextContent("4 tag(s)");
  }
}`,...E.parameters?.docs?.source},description:{story:`Add a tag via the Add button.`,...E.parameters?.docs?.description}}},D.parameters={...D.parameters,docs:{...D.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const input = canvas.getByPlaceholderText("Add tag...");

    // Try to add an existing tag
    await userEvent.type(input, "production{Enter}");

    // Count should remain 3
    await expect(canvas.getByTestId("tag-count")).toHaveTextContent("3 tag(s)");
  }
}`,...D.parameters?.docs?.source},description:{story:`Duplicate tags should not be added.`,...D.parameters?.docs?.description}}},O.parameters={...O.parameters,docs:{...O.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);

    // The X buttons are inside each badge <span>
    const criticalBadge = canvas.getByText("critical").closest("[data-slot='badge']")!;
    const removeButton = within(criticalBadge as HTMLElement).getByRole("button");
    await userEvent.click(removeButton);
    await expect(canvas.queryByText("critical")).not.toBeInTheDocument();
    await expect(canvas.getByTestId("tag-count")).toHaveTextContent("2 tag(s)");
  }
}`,...O.parameters?.docs?.source},description:{story:`Remove a tag by clicking the X button.`,...O.parameters?.docs?.description}}},k=[`RendersInitialTags`,`AddTagViaEnter`,`AddTagViaButton`,`PreventsDuplicates`,`RemoveTag`]}))();export{E as AddTagViaButton,T as AddTagViaEnter,D as PreventsDuplicates,O as RemoveTag,w as RendersInitialTags,k as __namedExportsOrder,C as default};