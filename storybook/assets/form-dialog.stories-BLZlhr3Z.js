import{p as q,f as $,n as P,d as o,a as n,o as z,k as p,t as l,u as d,v as B,m as f,x as C}from"./iframe-BLq-IXw7.js";import{c as A,d as G}from"./create-runtime-stories-Bj5LuboW.js";import{F as D}from"./form-dialog-cKnrUbYQ.js";import{I as L}from"./input-BLpZLiaj.js";import{L as h}from"./label-B532bab9.js";import{B as N}from"./button-DqmmnB3v.js";import"./preload-helper-PPVm8Dsz.js";import"./legacy-Ci8bO8La.js";import"./dialog-description-DFU8_dGP.js";import"./dialog-description-8sP4BR7d.js";import"./this-5dDYTdTk.js";import"./x-7Jn-ZFAs.js";import"./Icon-BM2c6fgH.js";import"./each-BUqwbEfg.js";import"./error-banner-eHcLZ5rd.js";import"./loader-circle-BONFkgg1.js";import"./input-CSZEXQ_3.js";import"./index-ldovL64k.js";const{fn:H}=__STORYBOOK_MODULE_TEST__,J={title:"UI/FormDialog",component:D,args:{title:"Create Namespace",description:"Create a new namespace in the tenant.",submitLabel:"Create",loading:!1,error:"",onsubmit:H()}},{Story:k}=G();var Q=p('<div class="space-y-3"><div><!> <!></div> <div><!> <!></div></div>'),V=p("<!> <!>",1),X=p("<div><!> <!></div>"),Z=p("<!> <!>",1),ee=p("<div><!> <!></div>"),te=p("<!> <!>",1),re=p("<!> <!> <!>",1);function M(R,U){q(U,!0);let b=C(!1),O=C(!1),x=C(!1);var W=re(),w=$(W);k(w,{name:"Default",template:(v,t=P)=>{var a=V(),i=$(a);N(i,{onclick:()=>d(b,!0),children:(e,g)=>{var r=l("Open Dialog");n(e,r)},$$slots:{default:!0}});var c=o(i,2);D(c,{get title(){return t().title},get description(){return t().description},get submitLabel(){return t().submitLabel},get loading(){return t().loading},get error(){return t().error},onsubmit:e=>{e.preventDefault(),t().onsubmit?.(e),d(b,!1)},get open(){return B(b)},set open(e){d(b,e,!0)},children:(e,g)=>{var r=Q(),s=f(r),u=f(s);h(u,{children:(E,j)=>{var F=l("Name");n(E,F)},$$slots:{default:!0}});var _=o(u,2);L(_,{placeholder:"my-namespace"});var y=o(s,2),m=f(y);h(m,{children:(E,j)=>{var F=l("Description");n(E,F)},$$slots:{default:!0}});var Y=o(m,2);L(Y,{placeholder:"Optional description..."}),n(e,r)},$$slots:{default:!0}}),n(v,a)},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<Button onclick={() => (defaultOpen = true)}>Open Dialog</Button>
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
</FormDialog>`}}});var S=o(w,2);k(S,{name:"With Error",args:{error:"Namespace 'my-namespace' already exists."},template:(v,t=P)=>{var a=Z(),i=$(a);N(i,{onclick:()=>d(O,!0),children:(e,g)=>{var r=l("Open With Error");n(e,r)},$$slots:{default:!0}});var c=o(i,2);D(c,{get title(){return t().title},get description(){return t().description},get submitLabel(){return t().submitLabel},get loading(){return t().loading},get error(){return t().error},onsubmit:e=>{e.preventDefault(),t().onsubmit?.(e)},get open(){return B(O)},set open(e){d(O,e,!0)},children:(e,g)=>{var r=X(),s=f(r);h(s,{children:(_,y)=>{var m=l("Name");n(_,m)},$$slots:{default:!0}});var u=o(s,2);L(u,{value:"my-namespace"}),n(e,r)},$$slots:{default:!0}}),n(v,a)},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<Button onclick={() => (errorOpen = true)}>Open With Error</Button>
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
</FormDialog>`}}});var K=o(S,2);k(K,{name:"Loading",args:{loading:!0},template:(v,t=P)=>{var a=te(),i=$(a);N(i,{onclick:()=>d(x,!0),children:(e,g)=>{var r=l("Open Loading");n(e,r)},$$slots:{default:!0}});var c=o(i,2);D(c,{get title(){return t().title},get description(){return t().description},get submitLabel(){return t().submitLabel},get loading(){return t().loading},get error(){return t().error},onsubmit:e=>{e.preventDefault(),t().onsubmit?.(e)},get open(){return B(x)},set open(e){d(x,e,!0)},children:(e,g)=>{var r=ee(),s=f(r);h(s,{children:(_,y)=>{var m=l("Name");n(_,m)},$$slots:{default:!0}});var u=o(s,2);L(u,{value:"my-namespace"}),n(e,r)},$$slots:{default:!0}}),n(v,a)},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<Button onclick={() => (loadingOpen = true)}>Open Loading</Button>
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
</FormDialog>`}}}),n(R,W),z()}M.__docgen={data:[],name:"form-dialog.stories.svelte"};const I=A(M,J),he=["Default","WithError","Loading"],De={...I.Default,tags:["svelte-csf-v5"]},Oe={...I.WithError,tags:["svelte-csf-v5"]},xe={...I.Loading,tags:["svelte-csf-v5"]};export{De as Default,xe as Loading,Oe as WithError,he as __namedExportsOrder,J as default};
