import{x as S,L as E,a as m,m as I,v as t,t as v,d as h,k as $,u as n}from"./iframe-DFtYtFsL.js";import{S as D}from"./step-progress-BYo6Kaqf.js";import{B as y}from"./button-BbjatG8g.js";import"./preload-helper-PPVm8Dsz.js";import"./each-BlWt3Neu.js";import"./badge-DOktaLwq.js";import"./index-KRrpyZZM.js";import"./Icon-CYtk7mac.js";import"./legacy-D7OnDY3G.js";import"./this-Dypaan2Q.js";import"./loader-circle-DukIKDwt.js";var q=$('<div class="max-w-md space-y-3 p-4"><!> <div class="flex gap-2"><!> <!> <!></div></div>');function _(s){let e=S(E([{label:"Validate configuration",status:"pending"},{label:"Create namespace",status:"pending"},{label:"Apply permissions",status:"pending"}])),a=S(!1);function o(){n(a,!0),t(e)[0].status="running",setTimeout(()=>{t(e)[0].status="done",t(e)[1].status="running"},400),setTimeout(()=>{t(e)[1].status="done",t(e)[2].status="running"},800),setTimeout(()=>{t(e)[2].status="done",n(a,!1)},1200)}function c(){n(a,!0),n(e,[{label:"Validate configuration",status:"pending"},{label:"Create namespace",status:"pending"},{label:"Apply permissions",status:"pending"}],!0),t(e)[0].status="running",setTimeout(()=>{t(e)[0].status="done",t(e)[1].status="running"},400),setTimeout(()=>{t(e)[1].status="failed",t(e)[1].error="Quota exceeded",n(a,!1)},800)}function g(){n(a,!1),n(e,[{label:"Validate configuration",status:"pending"},{label:"Create namespace",status:"pending"},{label:"Apply permissions",status:"pending"}],!0)}var x=q(),f=I(x);D(f,{get steps(){return t(e)}});var A=h(f,2),w=I(A);y(w,{size:"sm",onclick:o,get disabled(){return t(a)},"data-testid":"run-btn",children:(i,b)=>{var l=v("Run");m(i,l)},$$slots:{default:!0}});var T=h(w,2);y(T,{size:"sm",variant:"destructive",onclick:c,get disabled(){return t(a)},"data-testid":"error-btn",children:(i,b)=>{var l=v("Run with Error");m(i,l)},$$slots:{default:!0}});var k=h(T,2);y(k,{size:"sm",variant:"outline",onclick:g,"data-testid":"reset-btn",children:(i,b)=>{var l=v("Reset");m(i,l)},$$slots:{default:!0}}),m(s,x)}_.__docgen={data:[],name:"step-progress-test-harness.svelte"};const{expect:r,within:B}=__STORYBOOK_MODULE_TEST__,M={title:"Tests/StepProgress Interactions",component:_,tags:["!autodocs"]},d={play:async({canvasElement:s})=>{const e=B(s);await r(e.getByText("Validate configuration")).toBeInTheDocument(),await r(e.getByText("Create namespace")).toBeInTheDocument(),await r(e.getByText("Apply permissions")).toBeInTheDocument();const a=s.querySelectorAll('[data-slot="badge"][class*="destructive"]');await r(a.length).toBe(0)}},u={play:async({canvasElement:s})=>{B(s).getByTestId("run-btn").click(),await new Promise(c=>setTimeout(c,1600));const o=s.querySelectorAll('svg[class*="text-green"]');await r(o.length).toBe(3)}},p={play:async({canvasElement:s})=>{const e=B(s);e.getByTestId("error-btn").click(),await new Promise(g=>setTimeout(g,1200)),await r(e.getByText("Quota exceeded")).toBeInTheDocument();const o=s.querySelectorAll('svg[class*="text-green"]');await r(o.length).toBe(1);const c=s.querySelectorAll('svg[class*="text-destructive"]');await r(c.length).toBe(1)}};d.parameters={...d.parameters,docs:{...d.parameters?.docs,source:{originalSource:`{
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
}`,...d.parameters?.docs?.source},description:{story:"Verify initial state renders all steps as pending.",...d.parameters?.docs?.description}}};u.parameters={...u.parameters,docs:{...u.parameters?.docs,source:{originalSource:`{
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
}`,...u.parameters?.docs?.source},description:{story:"Run steps and verify they complete successfully.",...u.parameters?.docs?.description}}};p.parameters={...p.parameters,docs:{...p.parameters?.docs,source:{originalSource:`{
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
}`,...p.parameters?.docs?.source},description:{story:"Run with error and verify the failed step shows error badge.",...p.parameters?.docs?.description}}};const U=["RendersInitialState","CompletesAllSteps","ShowsErrorState"];export{u as CompletesAllSteps,d as RendersInitialState,p as ShowsErrorState,U as __namedExportsOrder,M as default};
