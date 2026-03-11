import{p as Y,f as $,n as P,i as n,d as o,e as z,j as p,t as l,r as d,h as B,k as b,q as C}from"./iframe-Bxes6a3w.js";import{c as A,d as G}from"./create-runtime-stories-NLAG1Xsk.js";import{F as D}from"./form-dialog-CTYkLBlH.js";import{I as L}from"./input-C84zDDIb.js";import{L as h}from"./label-BSPECOsA.js";import{B as N}from"./button-Bwb8csb8.js";import"./preload-helper-PPVm8Dsz.js";import"./legacy-Ce3C9Nuz.js";import"./dialog-description-xRd4NoGL.js";import"./scroll-lock-Dxkd3bHB.js";import"./is-An1zAff2.js";import"./create-id-Ck9YRxHS.js";import"./cn-_yov3II5.js";import"./dialog-description-NuVws75D.js";import"./this-CpOMcO__.js";import"./x-HnGGMeEe.js";import"./Icon-BEE4Z5vH.js";import"./each-DYffTe0e.js";import"./error-banner-BfCiNYNV.js";import"./loader-circle-B9kznHNw.js";import"./input-BqKJjkwU.js";import"./index-DW9qdgWl.js";const{fn:H}=__STORYBOOK_MODULE_TEST__,J={title:"UI/FormDialog",component:D,args:{title:"Create Namespace",description:"Create a new namespace in the tenant.",submitLabel:"Create",loading:!1,error:"",onsubmit:H()},argTypes:{title:{control:"text"},description:{control:"text"},submitLabel:{control:"text"},loading:{control:"boolean"},error:{control:"text"}}},{Story:k}=G();var Q=p('<div class="space-y-3"><div><!> <!></div> <div><!> <!></div></div>'),V=p("<!> <!>",1),X=p("<div><!> <!></div>"),Z=p("<!> <!>",1),ee=p("<div><!> <!></div>"),te=p("<!> <!>",1),re=p("<!> <!> <!>",1);function M(R,U){Y(U,!0);let f=C(!1),O=C(!1),x=C(!1);var W=re(),w=$(W);k(w,{name:"Default",template:(v,t=P)=>{var a=V(),i=$(a);N(i,{onclick:()=>d(f,!0),children:(e,g)=>{var r=l("Open Dialog");o(e,r)},$$slots:{default:!0}});var c=n(i,2);D(c,{get title(){return t().title},get description(){return t().description},get submitLabel(){return t().submitLabel},get loading(){return t().loading},get error(){return t().error},onsubmit:e=>{e.preventDefault(),t().onsubmit?.(e),d(f,!1)},get open(){return B(f)},set open(e){d(f,e,!0)},children:(e,g)=>{var r=Q(),s=b(r),m=b(s);h(m,{children:(E,K)=>{var F=l("Name");o(E,F)},$$slots:{default:!0}});var _=n(m,2);L(_,{placeholder:"my-namespace"});var y=n(s,2),u=b(y);h(u,{children:(E,K)=>{var F=l("Description");o(E,F)},$$slots:{default:!0}});var q=n(u,2);L(q,{placeholder:"Optional description..."}),o(e,r)},$$slots:{default:!0}}),o(v,a)},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<Button onclick={() => (defaultOpen = true)}>Open Dialog</Button>
<FormDialog
	bind:open={defaultOpen}
	title={args.title}
	description={args.description}
	submitLabel={args.submitLabel}
	loading={args.loading}
	error={args.error}
	onsubmit={(e) => {
		e.preventDefault();
		args.onsubmit?.(e);
		defaultOpen = false;
	}}
>
	<div class="space-y-3">
		<div>
			<Label>Name</Label>
			<Input placeholder="my-namespace" />
		</div>
		<div>
			<Label>Description</Label>
			<Input placeholder="Optional description..." />
		</div>
	</div>
</FormDialog>`}}});var S=n(w,2);k(S,{name:"With Error",args:{error:"Namespace 'my-namespace' already exists."},template:(v,t=P)=>{var a=Z(),i=$(a);N(i,{onclick:()=>d(O,!0),children:(e,g)=>{var r=l("Open With Error");o(e,r)},$$slots:{default:!0}});var c=n(i,2);D(c,{get title(){return t().title},get description(){return t().description},get submitLabel(){return t().submitLabel},get loading(){return t().loading},get error(){return t().error},onsubmit:e=>{e.preventDefault(),t().onsubmit?.(e)},get open(){return B(O)},set open(e){d(O,e,!0)},children:(e,g)=>{var r=X(),s=b(r);h(s,{children:(_,y)=>{var u=l("Name");o(_,u)},$$slots:{default:!0}});var m=n(s,2);L(m,{value:"my-namespace"}),o(e,r)},$$slots:{default:!0}}),o(v,a)},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<Button onclick={() => (errorOpen = true)}>Open With Error</Button>
<FormDialog
	bind:open={errorOpen}
	title={args.title}
	description={args.description}
	submitLabel={args.submitLabel}
	loading={args.loading}
	error={args.error}
	onsubmit={(e) => {
		e.preventDefault();
		args.onsubmit?.(e);
	}}
>
	<div>
		<Label>Name</Label>
		<Input value="my-namespace" />
	</div>
</FormDialog>`}}});var j=n(S,2);k(j,{name:"Loading",args:{loading:!0},template:(v,t=P)=>{var a=te(),i=$(a);N(i,{onclick:()=>d(x,!0),children:(e,g)=>{var r=l("Open Loading");o(e,r)},$$slots:{default:!0}});var c=n(i,2);D(c,{get title(){return t().title},get description(){return t().description},get submitLabel(){return t().submitLabel},get loading(){return t().loading},get error(){return t().error},onsubmit:e=>{e.preventDefault(),t().onsubmit?.(e)},get open(){return B(x)},set open(e){d(x,e,!0)},children:(e,g)=>{var r=ee(),s=b(r);h(s,{children:(_,y)=>{var u=l("Name");o(_,u)},$$slots:{default:!0}});var m=n(s,2);L(m,{value:"my-namespace"}),o(e,r)},$$slots:{default:!0}}),o(v,a)},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<Button onclick={() => (loadingOpen = true)}>Open Loading</Button>
<FormDialog
	bind:open={loadingOpen}
	title={args.title}
	description={args.description}
	submitLabel={args.submitLabel}
	loading={args.loading}
	error={args.error}
	onsubmit={(e) => {
		e.preventDefault();
		args.onsubmit?.(e);
	}}
>
	<div>
		<Label>Name</Label>
		<Input value="my-namespace" />
	</div>
</FormDialog>`}}}),o(R,W),z()}M.__docgen={data:[],name:"form-dialog.stories.svelte"};const I=A(M,J),ye=["Default","WithError","Loading"],Ee={...I.Default,tags:["svelte-csf-v5"]},Fe={...I.WithError,tags:["svelte-csf-v5"]},Pe={...I.Loading,tags:["svelte-csf-v5"]};export{Ee as Default,Pe as Loading,Fe as WithError,ye as __namedExportsOrder,J as default};
