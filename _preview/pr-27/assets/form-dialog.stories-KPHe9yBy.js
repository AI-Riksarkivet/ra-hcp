import{p as q,f as $,n as P,i as o,d as n,e as z,k as p,t as l,v as d,h as B,m as b,w as C}from"./iframe-CWf27PRy.js";import{c as A,d as G}from"./create-runtime-stories-Bm_4wmfQ.js";import{F as D}from"./form-dialog-Cpq0lDQZ.js";import{I as L}from"./input-CPTY0rWV.js";import{L as h}from"./label-BzU35nbr.js";import{B as N}from"./button-5150YEiy.js";import"./preload-helper-CFVQb_FG.js";import"./legacy-DQA76Hu_.js";import"./dialog-description-BEjoonQf.js";import"./scroll-lock-CcAA4XD8.js";import"./is-Hnx3UWIX.js";import"./create-id-B_1JCdG3.js";import"./cn-BtxYAf1B.js";import"./dialog-description-Bo6IKNVW.js";import"./Icon-DITVVYAT.js";import"./x-yNAkBOuJ.js";import"./error-banner-5ixFm5aG.js";import"./loader-circle-BfbR9apL.js";import"./input-zTd21VHu.js";import"./index-CPQfhKb5.js";const{fn:H}=__STORYBOOK_MODULE_TEST__,J={title:"UI/FormDialog",component:D,args:{title:"Create Namespace",description:"Create a new namespace in the tenant.",submitLabel:"Create",loading:!1,error:"",onsubmit:H()},argTypes:{title:{control:"text"},description:{control:"text"},submitLabel:{control:"text"},loading:{control:"boolean"},error:{control:"text"}}},{Story:k}=G();var Q=p('<div class="space-y-3"><div><!> <!></div> <div><!> <!></div></div>'),V=p("<!> <!>",1),X=p("<div><!> <!></div>"),Z=p("<!> <!>",1),ee=p("<div><!> <!></div>"),te=p("<!> <!>",1),re=p("<!> <!> <!>",1);function M(R,U){q(U,!0);let f=C(!1),O=C(!1),x=C(!1);var W=re(),w=$(W);k(w,{name:"Default",template:(v,t=P)=>{var a=V(),i=$(a);N(i,{onclick:()=>d(f,!0),children:(e,g)=>{var r=l("Open Dialog");n(e,r)},$$slots:{default:!0}});var c=o(i,2);D(c,{get title(){return t().title},get description(){return t().description},get submitLabel(){return t().submitLabel},get loading(){return t().loading},get error(){return t().error},onsubmit:e=>{e.preventDefault(),t().onsubmit?.(e),d(f,!1)},get open(){return B(f)},set open(e){d(f,e,!0)},children:(e,g)=>{var r=Q(),s=b(r),u=b(s);h(u,{children:(E,j)=>{var F=l("Name");n(E,F)},$$slots:{default:!0}});var _=o(u,2);L(_,{placeholder:"my-namespace"});var y=o(s,2),m=b(y);h(m,{children:(E,j)=>{var F=l("Description");n(E,F)},$$slots:{default:!0}});var Y=o(m,2);L(Y,{placeholder:"Optional description..."}),n(e,r)},$$slots:{default:!0}}),n(v,a)},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<Button onclick={() => (defaultOpen = true)}>Open Dialog</Button>
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
</FormDialog>`}}});var S=o(w,2);k(S,{name:"With Error",args:{error:"Namespace 'my-namespace' already exists."},template:(v,t=P)=>{var a=Z(),i=$(a);N(i,{onclick:()=>d(O,!0),children:(e,g)=>{var r=l("Open With Error");n(e,r)},$$slots:{default:!0}});var c=o(i,2);D(c,{get title(){return t().title},get description(){return t().description},get submitLabel(){return t().submitLabel},get loading(){return t().loading},get error(){return t().error},onsubmit:e=>{e.preventDefault(),t().onsubmit?.(e)},get open(){return B(O)},set open(e){d(O,e,!0)},children:(e,g)=>{var r=X(),s=b(r);h(s,{children:(_,y)=>{var m=l("Name");n(_,m)},$$slots:{default:!0}});var u=o(s,2);L(u,{value:"my-namespace"}),n(e,r)},$$slots:{default:!0}}),n(v,a)},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<Button onclick={() => (errorOpen = true)}>Open With Error</Button>
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
</FormDialog>`}}});var K=o(S,2);k(K,{name:"Loading",args:{loading:!0},template:(v,t=P)=>{var a=te(),i=$(a);N(i,{onclick:()=>d(x,!0),children:(e,g)=>{var r=l("Open Loading");n(e,r)},$$slots:{default:!0}});var c=o(i,2);D(c,{get title(){return t().title},get description(){return t().description},get submitLabel(){return t().submitLabel},get loading(){return t().loading},get error(){return t().error},onsubmit:e=>{e.preventDefault(),t().onsubmit?.(e)},get open(){return B(x)},set open(e){d(x,e,!0)},children:(e,g)=>{var r=ee(),s=b(r);h(s,{children:(_,y)=>{var m=l("Name");n(_,m)},$$slots:{default:!0}});var u=o(s,2);L(u,{value:"my-namespace"}),n(e,r)},$$slots:{default:!0}}),n(v,a)},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<Button onclick={() => (loadingOpen = true)}>Open Loading</Button>
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
</FormDialog>`}}}),n(R,W),z()}M.__docgen={data:[],name:"form-dialog.stories.svelte"};const I=A(M,J),Oe=["Default","WithError","Loading"],xe={...I.Default,tags:["svelte-csf-v5"]},ye={...I.WithError,tags:["svelte-csf-v5"]},Ee={...I.Loading,tags:["svelte-csf-v5"]};export{xe as Default,Ee as Loading,ye as WithError,Oe as __namedExportsOrder,J as default};
