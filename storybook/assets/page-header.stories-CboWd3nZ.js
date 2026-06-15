import{i as e}from"./preload-helper-xPQekRTU.js";import{$ as t,H as n,Ot as r,Qt as i,St as a,X as o,Zt as s,hn as c,jt as l,kt as u,nt as d,on as f,rt as p,s as m,sn as h,t as g,tt as _,un as v,vn as y}from"./client-DASBvjj6.js";import{rt as b}from"./iframe-CEOTwOQE.js";import{i as x,n as S,r as C,t as w}from"./create-runtime-stories-DVX5FtTr.js";import{P as T,b as E,t as D,wt as O}from"./lucide-svelte-C1WN62Nk.js";import{n as k,t as A}from"./button-C86ki4bN.js";function j(e,i){var s=M(),c=r(s),f=r(c),p=r(f,!0);h(f);var m=l(f,2),g=r(m,!0);h(m),h(c);var v=l(c,2),y=e=>{var t=d();o(u(t),()=>i.actions),_(e,t)};n(v,e=>{i.actions&&e(y)}),h(s),a(()=>{t(p,i.title),t(g,i.description)}),_(e,s)}var M,N=e((()=>{y(),c(),g(),M=p(`<div class="flex items-center justify-between"><div><h2 class="text-2xl font-bold"> </h2> <p class="mt-1 text-sm text-muted-foreground"> </p></div> <!></div>`),j.__docgen={data:[{name:`title`,visibility:`public`,keywords:[{name:`required`,description:``}],kind:`let`,type:{kind:`type`,type:`string`,text:`string`},static:!1,readonly:!1},{name:`description`,visibility:`public`,keywords:[{name:`required`,description:``}],kind:`let`,type:{kind:`type`,type:`string`,text:`string`},static:!1,readonly:!1},{name:`actions`,visibility:`public`,keywords:[],kind:`let`,type:{kind:`function`,text:`Snippet<[]>`},static:!1,readonly:!1}],name:`page-header.svelte`}}));function P(e,t){i(t,!1),m();var n=H(),a=u(n);I(a,{name:`Default`,args:{title:`Namespaces`,description:`Manage tenant namespaces`},parameters:{__svelteCsf:{rawCode:`<PageHeader {...args} />`}}});var o=l(a,2);I(o,{name:`With Single Action`,template:(e,t=v)=>{j(e,{get title(){return t().title},get description(){return t().description},actions:e=>{k(e,{size:`sm`,children:(e,t)=>{var n=L();T(u(n),{class:`h-4 w-4`}),f(),_(e,n)},$$slots:{default:!0}})},$$slots:{actions:!0}})},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<PageHeader title={args.title} description={args.description}>
	{#snippet actions()}
		<Button size="sm">
			<Plus class="h-4 w-4" />
			Create Namespace
		</Button>
	{/snippet}
</PageHeader>`}}});var c=l(o,2);I(c,{name:`With Multiple Actions`,args:{title:`Buckets`,description:`Manage S3-compatible storage buckets`},template:(e,t=v)=>{j(e,{get title(){return t().title},get description(){return t().description},actions:e=>{var t=V(),n=r(t);k(n,{size:`sm`,variant:`outline`,children:(e,t)=>{var n=R();O(u(n),{class:`h-4 w-4`}),f(),_(e,n)},$$slots:{default:!0}});var i=l(n,2);k(i,{size:`sm`,variant:`destructive`,children:(e,t)=>{var n=z();E(u(n),{class:`h-4 w-4`}),f(),_(e,n)},$$slots:{default:!0}}),k(l(i,2),{size:`sm`,children:(e,t)=>{var n=B();T(u(n),{class:`h-4 w-4`}),f(),_(e,n)},$$slots:{default:!0}}),h(t),_(e,t)},$$slots:{actions:!0}})},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<PageHeader title={args.title} description={args.description}>
	{#snippet actions()}
		<div class="flex gap-2">
			<Button size="sm" variant="outline">
				<Download class="h-4 w-4" />
				Export
			</Button>
			<Button size="sm" variant="destructive">
				<Trash2 class="h-4 w-4" />
				Delete Selected
			</Button>
			<Button size="sm">
				<Plus class="h-4 w-4" />
				Create Bucket
			</Button>
		</div>
	{/snippet}
</PageHeader>`}}});var d=l(c,2);I(d,{name:`Long Description`,args:{title:`Settings`,description:`Configure tenant-wide settings including authentication, storage quotas, and network policies.`},parameters:{__svelteCsf:{rawCode:`<PageHeader {...args} />`}}}),I(l(d,2),{name:`Short Title`,args:{title:`Users`,description:`Manage user accounts and group memberships for this tenant.`},parameters:{__svelteCsf:{rawCode:`<PageHeader {...args} />`}}}),_(e,n),s()}var F,I,L,R,z,B,V,H,U,W,G,K,q,J,Y;e((()=>{y(),b(),c(),x(),N(),g(),A(),D(),S(),F={title:`UI/PageHeader`,component:j,args:{title:`Namespaces`,description:`Manage tenant namespaces`}},{Story:I}=C(F),L=p(`<!> Create Namespace`,1),R=p(`<!> Export`,1),z=p(`<!> Delete Selected`,1),B=p(`<!> Create Bucket`,1),V=p(`<div class="flex gap-2"><!> <!> <!></div>`),H=p(`<!> <!> <!> <!> <!>`,1),P.__docgen={data:[],name:`page-header.stories.svelte`},U=w(P,F),W=[`Default`,`WithSingleAction`,`WithMultipleActions`,`LongDescription`,`ShortTitle`],G={...U.Default,tags:[`svelte-csf-v5`]},K={...U.WithSingleAction,tags:[`svelte-csf-v5`]},q={...U.WithMultipleActions,tags:[`svelte-csf-v5`]},J={...U.LongDescription,tags:[`svelte-csf-v5`]},Y={...U.ShortTitle,tags:[`svelte-csf-v5`]}}))();export{G as Default,J as LongDescription,Y as ShortTitle,q as WithMultipleActions,K as WithSingleAction,W as __namedExportsOrder,F as default};