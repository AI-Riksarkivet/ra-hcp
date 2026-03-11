import{w as x,C as w,g as h,d as E,v as I,h as u,k as _,i as m,m as l,s as b}from"./iframe-CWf27PRy.js";import{T as D}from"./tag-input-CmtvKeLQ.js";import"./preload-helper-CFVQb_FG.js";import"./cn-BtxYAf1B.js";import"./button-5150YEiy.js";import"./index-CPQfhKb5.js";import"./Icon-DITVVYAT.js";import"./legacy-DQA76Hu_.js";import"./input-CPTY0rWV.js";import"./input-zTd21VHu.js";import"./badge--90Mman0.js";import"./x-yNAkBOuJ.js";var A=_('<div class="max-w-md space-y-4 p-4"><h3 class="text-sm font-medium">Tag Input Test Harness</h3> <!> <div data-testid="tag-count" class="text-xs text-muted-foreground"> </div></div>');function v(e){let t=x(w(["production","critical","eu-west"]));var n=A(),s=m(l(n),2);D(s,{placeholder:"Add tag...",get tags(){return u(t)},set tags(B){I(t,B,!0)}});var y=m(s,2),T=l(y);h(()=>b(T,`${u(t).length??""} tag(s)`)),E(e,n)}v.__docgen={data:[],name:"tag-input-test-harness.svelte"};const{expect:a,userEvent:p,within:o}=__STORYBOOK_MODULE_TEST__,X={title:"Tests/TagInput Interactions",component:v,tags:["!autodocs"]},c={play:async({canvasElement:e})=>{const t=o(e);await a(t.getByText("production")).toBeInTheDocument(),await a(t.getByText("critical")).toBeInTheDocument(),await a(t.getByText("eu-west")).toBeInTheDocument(),await a(t.getByTestId("tag-count")).toHaveTextContent("3 tag(s)")}},r={play:async({canvasElement:e})=>{const t=o(e),n=t.getByPlaceholderText("Add tag...");await p.type(n,"new-tag{Enter}"),await a(t.getByText("new-tag")).toBeInTheDocument(),await a(t.getByTestId("tag-count")).toHaveTextContent("4 tag(s)")}},i={play:async({canvasElement:e})=>{const t=o(e),n=t.getByPlaceholderText("Add tag..."),s=t.getByRole("button",{name:"Add"});await p.type(n,"button-tag"),await p.click(s),await a(t.getByText("button-tag")).toBeInTheDocument(),await a(t.getByTestId("tag-count")).toHaveTextContent("4 tag(s)")}},d={play:async({canvasElement:e})=>{const t=o(e),n=t.getByPlaceholderText("Add tag...");await p.type(n,"production{Enter}"),await a(t.getByTestId("tag-count")).toHaveTextContent("3 tag(s)")}},g={play:async({canvasElement:e})=>{const t=o(e),n=t.getByText("critical").closest("[data-slot='badge']"),s=o(n).getByRole("button");await p.click(s),await a(t.queryByText("critical")).not.toBeInTheDocument(),await a(t.getByTestId("tag-count")).toHaveTextContent("2 tag(s)")}};c.parameters={...c.parameters,docs:{...c.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText("production")).toBeInTheDocument();
    await expect(canvas.getByText("critical")).toBeInTheDocument();
    await expect(canvas.getByText("eu-west")).toBeInTheDocument();
    await expect(canvas.getByTestId("tag-count")).toHaveTextContent("3 tag(s)");
  }
}`,...c.parameters?.docs?.source},description:{story:"Verify initial tags render correctly.",...c.parameters?.docs?.description}}};r.parameters={...r.parameters,docs:{...r.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const input = canvas.getByPlaceholderText("Add tag...");
    await userEvent.type(input, "new-tag{Enter}");
    await expect(canvas.getByText("new-tag")).toBeInTheDocument();
    await expect(canvas.getByTestId("tag-count")).toHaveTextContent("4 tag(s)");
  }
}`,...r.parameters?.docs?.source},description:{story:"Type a new tag and press Enter to add it.",...r.parameters?.docs?.description}}};i.parameters={...i.parameters,docs:{...i.parameters?.docs,source:{originalSource:`{
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
}`,...i.parameters?.docs?.source},description:{story:"Add a tag via the Add button.",...i.parameters?.docs?.description}}};d.parameters={...d.parameters,docs:{...d.parameters?.docs,source:{originalSource:`{
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
}`,...d.parameters?.docs?.source},description:{story:"Duplicate tags should not be added.",...d.parameters?.docs?.description}}};g.parameters={...g.parameters,docs:{...g.parameters?.docs,source:{originalSource:`{
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
}`,...g.parameters?.docs?.source},description:{story:"Remove a tag by clicking the X button.",...g.parameters?.docs?.description}}};const K=["RendersInitialTags","AddTagViaEnter","AddTagViaButton","PreventsDuplicates","RemoveTag"];export{i as AddTagViaButton,r as AddTagViaEnter,d as PreventsDuplicates,g as RemoveTag,c as RendersInitialTags,K as __namedExportsOrder,X as default};
