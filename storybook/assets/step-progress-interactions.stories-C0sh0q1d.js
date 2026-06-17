import{i as e}from"./preload-helper-xPQekRTU.js";import{It as t,Nt as n,Ot as r,Rt as i,hn as a,ht as o,jt as s,on as c,rt as l,sn as u,st as d,t as f,tt as p,vn as m}from"./client-DASBvjj6.js";import{n as h,t as g}from"./button-DImO-Pmy.js";import{n as _,t as v}from"./step-progress-xlFk5lVI.js";function y(e){let a=i(n([{label:`Validate configuration`,status:`pending`},{label:`Create namespace`,status:`pending`},{label:`Apply permissions`,status:`pending`}])),l=i(!1);function f(){t(l,!0),o(a)[0].status=`running`,setTimeout(()=>{o(a)[0].status=`done`,o(a)[1].status=`running`},400),setTimeout(()=>{o(a)[1].status=`done`,o(a)[2].status=`running`},800),setTimeout(()=>{o(a)[2].status=`done`,t(l,!1)},1200)}function m(){t(l,!0),t(a,[{label:`Validate configuration`,status:`pending`},{label:`Create namespace`,status:`pending`},{label:`Apply permissions`,status:`pending`}],!0),o(a)[0].status=`running`,setTimeout(()=>{o(a)[0].status=`done`,o(a)[1].status=`running`},400),setTimeout(()=>{o(a)[1].status=`failed`,o(a)[1].error=`Quota exceeded`,t(l,!1)},800)}function g(){t(l,!1),t(a,[{label:`Validate configuration`,status:`pending`},{label:`Create namespace`,status:`pending`},{label:`Apply permissions`,status:`pending`}],!0)}var _=b(),y=r(_);v(y,{get steps(){return o(a)}});var x=s(y,2),S=r(x);h(S,{size:`sm`,onclick:f,get disabled(){return o(l)},"data-testid":`run-btn`,children:(e,t)=>{c(),p(e,d(`Run`))},$$slots:{default:!0}});var C=s(S,2);h(C,{size:`sm`,variant:`destructive`,onclick:m,get disabled(){return o(l)},"data-testid":`error-btn`,children:(e,t)=>{c(),p(e,d(`Run with Error`))},$$slots:{default:!0}}),h(s(C,2),{size:`sm`,variant:`outline`,onclick:g,"data-testid":`reset-btn`,children:(e,t)=>{c(),p(e,d(`Reset`))},$$slots:{default:!0}}),u(x),u(_),p(e,_)}var b,x=e((()=>{m(),a(),f(),_(),g(),b=l(`<div class="max-w-md space-y-3 p-4"><!> <div class="flex gap-2"><!> <!> <!></div></div>`),y.__docgen={data:[],name:`step-progress-test-harness.svelte`}})),S,C,w,T,E,D,O;e((()=>{x(),{expect:S,within:C}=__STORYBOOK_MODULE_TEST__,w={title:`Tests/StepProgress Interactions`,component:y,tags:[`!autodocs`]},T={play:async({canvasElement:e})=>{let t=C(e);await S(t.getByText(`Validate configuration`)).toBeInTheDocument(),await S(t.getByText(`Create namespace`)).toBeInTheDocument(),await S(t.getByText(`Apply permissions`)).toBeInTheDocument(),await S(e.querySelectorAll(`[data-slot="badge"][class*="destructive"]`).length).toBe(0)}},E={play:async({canvasElement:e})=>{C(e).getByTestId(`run-btn`).click(),await new Promise(e=>setTimeout(e,1600)),await S(e.querySelectorAll(`svg[class*="text-green"]`).length).toBe(3)}},D={play:async({canvasElement:e})=>{let t=C(e);t.getByTestId(`error-btn`).click(),await new Promise(e=>setTimeout(e,1200)),await S(t.getByText(`Quota exceeded`)).toBeInTheDocument(),await S(e.querySelectorAll(`svg[class*="text-green"]`).length).toBe(1),await S(e.querySelectorAll(`svg[class*="text-destructive"]`).length).toBe(1)}},T.parameters={...T.parameters,docs:{...T.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText("Validate configuration")).toBeInTheDocument();
    await expect(canvas.getByText("Create namespace")).toBeInTheDocument();
    await expect(canvas.getByText("Apply permissions")).toBeInTheDocument();

    // All pending — no error badges visible
    const errorBadges = canvasElement.querySelectorAll('[data-slot="badge"][class*="destructive"]');
    await expect(errorBadges.length).toBe(0);
  }
}`,...T.parameters?.docs?.source},description:{story:`Verify initial state renders all steps as pending.`,...T.parameters?.docs?.description}}},E.parameters={...E.parameters,docs:{...E.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const runBtn = canvas.getByTestId("run-btn");
    runBtn.click();

    // Wait for all steps to finish (1200ms + buffer)
    await new Promise(r => setTimeout(r, 1600));

    // All steps should show checkmarks (done state)
    const checkIcons = canvasElement.querySelectorAll('svg[class*="text-green"]');
    await expect(checkIcons.length).toBe(3);
  }
}`,...E.parameters?.docs?.source},description:{story:`Run steps and verify they complete successfully.`,...E.parameters?.docs?.description}}},D.parameters={...D.parameters,docs:{...D.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const errorBtn = canvas.getByTestId("error-btn");
    errorBtn.click();

    // Wait for error to occur (800ms + buffer)
    await new Promise(r => setTimeout(r, 1200));

    // Should show "Quota exceeded" error badge
    await expect(canvas.getByText("Quota exceeded")).toBeInTheDocument();

    // First step should be done (green), second failed (red)
    const checkIcons = canvasElement.querySelectorAll('svg[class*="text-green"]');
    await expect(checkIcons.length).toBe(1);
    const errorIcons = canvasElement.querySelectorAll('svg[class*="text-destructive"]');
    await expect(errorIcons.length).toBe(1);
  }
}`,...D.parameters?.docs?.source},description:{story:`Run with error and verify the failed step shows error badge.`,...D.parameters?.docs?.description}}},O=[`RendersInitialState`,`CompletesAllSteps`,`ShowsErrorState`]}))();export{E as CompletesAllSteps,T as RendersInitialState,D as ShowsErrorState,O as __namedExportsOrder,w as default};