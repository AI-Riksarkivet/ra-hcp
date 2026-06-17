import{i as e}from"./preload-helper-xPQekRTU.js";import{It as t,Ot as n,Qt as r,Rt as i,Zt as a,hn as o,ht as s,jt as c,kt as l,on as u,rt as d,sn as f,st as p,t as m,tt as h,un as g,vn as _}from"./client-DASBvjj6.js";import{i as v,n as y,r as b,t as x}from"./create-runtime-stories-BLv_IUYu.js";import{n as S,t as C}from"./button-tl3gcfrW.js";import{n as w,t as T}from"./input-BJmUI_ZR.js";import{n as E,t as D}from"./label-B0wJyLzm.js";import{n as O,t as k}from"./form-dialog-h-Zojc3X.js";function A(e,o){r(o,!0);let d=i(!1),m=i(!1),_=i(!1);var v=L(),y=l(v);N(y,{name:`Default`,template:(e,r=g)=>{var i=F(),a=l(i);S(a,{onclick:()=>t(d,!0),children:(e,t)=>{u(),h(e,p(`Open Dialog`))},$$slots:{default:!0}}),k(c(a,2),{get title(){return r().title},get description(){return r().description},get submitLabel(){return r().submitLabel},get loading(){return r().loading},get error(){return r().error},onsubmit:e=>{e.preventDefault(),r().onsubmit?.(e),t(d,!1)},get open(){return s(d)},set open(e){t(d,e,!0)},children:(e,t)=>{var r=P(),i=n(r),a=n(i);E(a,{children:(e,t)=>{u(),h(e,p(`Name`))},$$slots:{default:!0}}),w(c(a,2),{placeholder:`my-namespace`}),f(i);var o=c(i,2),s=n(o);E(s,{children:(e,t)=>{u(),h(e,p(`Description`))},$$slots:{default:!0}}),w(c(s,2),{placeholder:`Optional description...`}),f(o),f(r),h(e,r)},$$slots:{default:!0}}),h(e,i)},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<Button onclick={() => (defaultOpen = true)}>Open Dialog</Button>
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
</FormDialog>`}}});var b=c(y,2);N(b,{name:`With Error`,args:{error:`Namespace 'my-namespace' already exists.`},template:(e,r=g)=>{var i=F(),a=l(i);S(a,{onclick:()=>t(m,!0),children:(e,t)=>{u(),h(e,p(`Open With Error`))},$$slots:{default:!0}}),k(c(a,2),{get title(){return r().title},get description(){return r().description},get submitLabel(){return r().submitLabel},get loading(){return r().loading},get error(){return r().error},onsubmit:e=>{e.preventDefault(),r().onsubmit?.(e)},get open(){return s(m)},set open(e){t(m,e,!0)},children:(e,t)=>{var r=I(),i=n(r);E(i,{children:(e,t)=>{u(),h(e,p(`Name`))},$$slots:{default:!0}}),w(c(i,2),{value:`my-namespace`}),f(r),h(e,r)},$$slots:{default:!0}}),h(e,i)},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<Button onclick={() => (errorOpen = true)}>Open With Error</Button>
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
</FormDialog>`}}});var x=c(b,2);N(x,{name:`Loading`,args:{loading:!0},template:(e,r=g)=>{var i=F(),a=l(i);S(a,{onclick:()=>t(_,!0),children:(e,t)=>{u(),h(e,p(`Open Loading`))},$$slots:{default:!0}}),k(c(a,2),{get title(){return r().title},get description(){return r().description},get submitLabel(){return r().submitLabel},get loading(){return r().loading},get error(){return r().error},onsubmit:e=>{e.preventDefault(),r().onsubmit?.(e)},get open(){return s(_)},set open(e){t(_,e,!0)},children:(e,t)=>{var r=I(),i=n(r);E(i,{children:(e,t)=>{u(),h(e,p(`Name`))},$$slots:{default:!0}}),w(c(i,2),{value:`my-namespace`}),f(r),h(e,r)},$$slots:{default:!0}}),h(e,i)},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<Button onclick={() => (loadingOpen = true)}>Open Loading</Button>
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
</FormDialog>`}}}),h(e,v),a()}var j,M,N,P,F,I,L,R,z,B,V,H;e((()=>{_(),o(),v(),O(),m(),T(),D(),C(),y(),{fn:j}=__STORYBOOK_MODULE_TEST__,M={title:`UI/FormDialog`,component:k,args:{title:`Create Namespace`,description:`Create a new namespace in the tenant.`,submitLabel:`Create`,loading:!1,error:``,onsubmit:j()}},{Story:N}=b(M),P=d(`<div class="space-y-3"><div><!> <!></div> <div><!> <!></div></div>`),F=d(`<!> <!>`,1),I=d(`<div><!> <!></div>`),L=d(`<!> <!> <!>`,1),A.__docgen={data:[],name:`form-dialog.stories.svelte`},R=x(A,M),z=[`Default`,`WithError`,`Loading`],B={...R.Default,tags:[`svelte-csf-v5`]},V={...R.WithError,tags:[`svelte-csf-v5`]},H={...R.Loading,tags:[`svelte-csf-v5`]}}))();export{B as Default,H as Loading,V as WithError,z as __namedExportsOrder,M as default};