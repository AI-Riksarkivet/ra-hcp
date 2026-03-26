import{g as k,r as f,a as _,d as B,v as d,k as S,u as r,w as D,x as v,y as E,m as l,h as R}from"./iframe-DFtYtFsL.js";import{S as I}from"./save-button-_AMgjLGF.js";import"./preload-helper-PPVm8Dsz.js";import"./button-BbjatG8g.js";import"./index-KRrpyZZM.js";import"./this-Dypaan2Q.js";import"./loader-circle-DukIKDwt.js";import"./legacy-D7OnDY3G.js";import"./Icon-CYtk7mac.js";import"./each-BlWt3Neu.js";var C=S('<div class="space-y-3 p-4"><div class="flex gap-2"><button class="rounded border px-3 py-1 text-sm" data-testid="make-dirty">Make dirty</button></div> <!> <p class="text-xs text-muted-foreground" data-testid="save-count"> </p></div>');function b(a){let e=v(!1),t=v(!1),c=v(0);function h(){r(t,!0),D(c),setTimeout(()=>{r(t,!1),r(e,!1)},500)}var p=C(),y=l(p),w=l(y),g=B(y,2);I(g,{get dirty(){return d(e)},get saving(){return d(t)},onclick:h});var x=B(g,2),T=l(x);k(()=>R(T,`Saves: ${d(c)??""}`)),f("click",w,()=>r(e,!0)),_(a,p)}E(["click"]);b.__docgen={data:[],name:"save-button-test-harness.svelte"};const{expect:n,userEvent:m,within:u}=__STORYBOOK_MODULE_TEST__,$={title:"Tests/SaveButton Interactions",component:b,tags:["!autodocs"]},s={play:async({canvasElement:a})=>{const t=u(a).getByRole("button",{name:/save/i});await n(t).toBeDisabled()}},o={play:async({canvasElement:a})=>{const e=u(a),t=e.getByRole("button",{name:/save/i});await n(t).toBeDisabled(),await m.click(e.getByTestId("make-dirty")),await n(t).not.toBeDisabled(),await n(e.getByText("Unsaved changes")).toBeInTheDocument()}},i={play:async({canvasElement:a})=>{const e=u(a);await m.click(e.getByTestId("make-dirty"));const t=e.getByRole("button",{name:/save/i});await m.click(t),await new Promise(c=>setTimeout(c,700)),await n(e.getByTestId("save-count")).toHaveTextContent("Saves: 1"),await n(e.getByRole("button",{name:/save/i})).toBeDisabled()}};s.parameters={...s.parameters,docs:{...s.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const saveBtn = canvas.getByRole("button", {
      name: /save/i
    });
    await expect(saveBtn).toBeDisabled();
  }
}`,...s.parameters?.docs?.source},description:{story:"Save button should be disabled when not dirty.",...s.parameters?.docs?.description}}};o.parameters={...o.parameters,docs:{...o.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);

    // Initially disabled
    const saveBtn = canvas.getByRole("button", {
      name: /save/i
    });
    await expect(saveBtn).toBeDisabled();

    // Make dirty
    await userEvent.click(canvas.getByTestId("make-dirty"));

    // Now enabled with "Unsaved changes" text
    await expect(saveBtn).not.toBeDisabled();
    await expect(canvas.getByText("Unsaved changes")).toBeInTheDocument();
  }
}`,...o.parameters?.docs?.source},description:{story:'Making the form dirty should enable the save button and show "Unsaved changes".',...o.parameters?.docs?.description}}};i.parameters={...i.parameters,docs:{...i.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);

    // Make dirty then save
    await userEvent.click(canvas.getByTestId("make-dirty"));
    const saveBtn = canvas.getByRole("button", {
      name: /save/i
    });
    await userEvent.click(saveBtn);

    // Wait for save to complete (500ms + buffer)
    await new Promise(r => setTimeout(r, 700));

    // Counter should show 1 save
    await expect(canvas.getByTestId("save-count")).toHaveTextContent("Saves: 1");

    // Button should be disabled again (clean state)
    await expect(canvas.getByRole("button", {
      name: /save/i
    })).toBeDisabled();
  }
}`,...i.parameters?.docs?.source},description:{story:"Clicking save should increment the save counter and reset to clean.",...i.parameters?.docs?.description}}};const j=["DisabledWhenClean","EnablesWhenDirty","SaveResetsToClean"];export{s as DisabledWhenClean,o as EnablesWhenDirty,i as SaveResetsToClean,j as __namedExportsOrder,$ as default};
