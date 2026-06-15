import{i as e}from"./preload-helper-xPQekRTU.js";import{$ as t,It as n,Ot as r,Rt as i,St as a,ct as o,hn as s,ht as c,jt as l,lt as u,rt as d,sn as f,t as p,tt as m,vn as h,zt as g}from"./client-DASBvjj6.js";import{n as _,t as v}from"./save-button-DA1SaVtT.js";function y(e){let o=i(!1),s=i(!1),d=i(0);function p(){n(s,!0),g(d),setTimeout(()=>{n(s,!1),n(o,!1)},500)}var h=b(),_=r(h),y=r(_);f(_);var x=l(_,2);v(x,{get dirty(){return c(o)},get saving(){return c(s)},onclick:p});var S=l(x,2),C=r(S);f(S),f(h),a(()=>t(C,`Saves: ${c(d)??``}`)),u(`click`,y,()=>n(o,!0)),m(e,h)}var b,x=e((()=>{h(),s(),p(),_(),b=d(`<div class="space-y-3 p-4"><div class="flex gap-2"><button class="rounded border px-3 py-1 text-sm" data-testid="make-dirty">Make dirty</button></div> <!> <p class="text-xs text-muted-foreground" data-testid="save-count"> </p></div>`),o([`click`]),y.__docgen={data:[],name:`save-button-test-harness.svelte`}})),S,C,w,T,E,D,O,k;e((()=>{x(),{expect:S,userEvent:C,within:w}=__STORYBOOK_MODULE_TEST__,T={title:`Tests/SaveButton Interactions`,component:y,tags:[`!autodocs`]},E={play:async({canvasElement:e})=>{await S(w(e).getByRole(`button`,{name:/save/i})).toBeDisabled()}},D={play:async({canvasElement:e})=>{let t=w(e),n=t.getByRole(`button`,{name:/save/i});await S(n).toBeDisabled(),await C.click(t.getByTestId(`make-dirty`)),await S(n).not.toBeDisabled(),await S(t.getByText(`Unsaved changes`)).toBeInTheDocument()}},O={play:async({canvasElement:e})=>{let t=w(e);await C.click(t.getByTestId(`make-dirty`));let n=t.getByRole(`button`,{name:/save/i});await C.click(n),await new Promise(e=>setTimeout(e,700)),await S(t.getByTestId(`save-count`)).toHaveTextContent(`Saves: 1`),await S(t.getByRole(`button`,{name:/save/i})).toBeDisabled()}},E.parameters={...E.parameters,docs:{...E.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const saveBtn = canvas.getByRole("button", {
      name: /save/i
    });
    await expect(saveBtn).toBeDisabled();
  }
}`,...E.parameters?.docs?.source},description:{story:`Save button should be disabled when not dirty.`,...E.parameters?.docs?.description}}},D.parameters={...D.parameters,docs:{...D.parameters?.docs,source:{originalSource:`{
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
}`,...D.parameters?.docs?.source},description:{story:`Making the form dirty should enable the save button and show "Unsaved changes".`,...D.parameters?.docs?.description}}},O.parameters={...O.parameters,docs:{...O.parameters?.docs,source:{originalSource:`{
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
}`,...O.parameters?.docs?.source},description:{story:`Clicking save should increment the save counter and reset to clean.`,...O.parameters?.docs?.description}}},k=[`DisabledWhenClean`,`EnablesWhenDirty`,`SaveResetsToClean`]}))();export{E as DisabledWhenClean,D as EnablesWhenDirty,O as SaveResetsToClean,k as __namedExportsOrder,T as default};