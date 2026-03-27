import{B as H,g as T,a as s,k as i,d as a,m as _,c as L,f as r,Q as N,h as A,p as q,n as M,o as E}from"./iframe-CTm_ffW8.js";import{i as U}from"./legacy-CDXkwGSf.js";import{c as j,d as I}from"./create-runtime-stories-JUC_Opkr.js";import{B as P}from"./button-Dnzsi9-9.js";import{P as W}from"./plus-ChedtXt0.js";import{D as O}from"./download-DFzCuyeN.js";import{T as Q}from"./trash-2-DFQKG_t2.js";import"./preload-helper-PPVm8Dsz.js";import"./index-CrxHSMXN.js";import"./this-DscMLWEM.js";import"./Icon-CbVG816t.js";import"./each-Dcph8Tww.js";var R=i('<div class="flex items-center justify-between"><div><h2 class="text-2xl font-bold"> </h2> <p class="mt-1 text-sm text-muted-foreground"> </p></div> <!></div>');function x(S,n){var o=R(),l=_(o),c=_(l),h=_(c),$=a(c,2),k=_($),C=a(l,2);{var d=e=>{var w=L(),p=r(w);N(p,()=>n.actions),s(e,w)};H(C,e=>{n.actions&&e(d)})}T(()=>{A(h,n.title),A(k,n.description)}),s(S,o)}x.__docgen={data:[{name:"title",visibility:"public",keywords:[{name:"required",description:""}],kind:"let",type:{kind:"type",type:"string",text:"string"},static:!1,readonly:!1},{name:"description",visibility:"public",keywords:[{name:"required",description:""}],kind:"let",type:{kind:"type",type:"string",text:"string"},static:!1,readonly:!1},{name:"actions",visibility:"public",keywords:[],kind:"let",type:{kind:"function",text:"Snippet<[]>"},static:!1,readonly:!1}],name:"page-header.svelte"};const F={title:"UI/PageHeader",component:x,args:{title:"Namespaces",description:"Manage tenant namespaces"}},{Story:u}=I();var G=i("<!> Create Namespace",1),J=i("<!> Export",1),K=i("<!> Delete Selected",1),V=i("<!> Create Bucket",1),X=i('<div class="flex gap-2"><!> <!> <!></div>'),Y=i("<!> <!> <!> <!> <!>",1);function z(S,n){q(n,!1),U();var o=Y(),l=r(o);u(l,{name:"Default",args:{title:"Namespaces",description:"Manage tenant namespaces"},parameters:{__svelteCsf:{rawCode:"<PageHeader {...args} />"}}});var c=a(l,2);u(c,{name:"With Single Action",template:(d,e=M)=>{x(d,{get title(){return e().title},get description(){return e().description},actions:p=>{P(p,{size:"sm",children:(y,D)=>{var m=G(),B=r(m);W(B,{class:"h-4 w-4"}),s(y,m)},$$slots:{default:!0}})}})},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<PageHeader title={args.title} description={args.description}>
	{#snippet actions()}
		<Button size="sm">
			<Plus class="h-4 w-4" />
			Create Namespace
		</Button>
	{/snippet}
</PageHeader>`}}});var h=a(c,2);u(h,{name:"With Multiple Actions",args:{title:"Buckets",description:"Manage S3-compatible storage buckets"},template:(d,e=M)=>{x(d,{get title(){return e().title},get description(){return e().description},actions:p=>{var y=X(),D=_(y);P(D,{size:"sm",variant:"outline",children:(v,b)=>{var t=J(),g=r(t);O(g,{class:"h-4 w-4"}),s(v,t)},$$slots:{default:!0}});var m=a(D,2);P(m,{size:"sm",variant:"destructive",children:(v,b)=>{var t=K(),g=r(t);Q(g,{class:"h-4 w-4"}),s(v,t)},$$slots:{default:!0}});var B=a(m,2);P(B,{size:"sm",children:(v,b)=>{var t=V(),g=r(t);W(g,{class:"h-4 w-4"}),s(v,t)},$$slots:{default:!0}}),s(p,y)}})},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<PageHeader title={args.title} description={args.description}>
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
</PageHeader>`}}});var $=a(h,2);u($,{name:"Long Description",args:{title:"Settings",description:"Configure tenant-wide settings including authentication, storage quotas, and network policies."},parameters:{__svelteCsf:{rawCode:"<PageHeader {...args} />"}}});var k=a($,2);u(k,{name:"Short Title",args:{title:"Users",description:"Manage user accounts and group memberships for this tenant."},parameters:{__svelteCsf:{rawCode:"<PageHeader {...args} />"}}}),s(S,o),E()}z.__docgen={data:[],name:"page-header.stories.svelte"};const f=j(z,F),pe=["Default","WithSingleAction","WithMultipleActions","LongDescription","ShortTitle"],me={...f.Default,tags:["svelte-csf-v5"]},ve={...f.WithSingleAction,tags:["svelte-csf-v5"]},ge={...f.WithMultipleActions,tags:["svelte-csf-v5"]},ue={...f.LongDescription,tags:["svelte-csf-v5"]},_e={...f.ShortTitle,tags:["svelte-csf-v5"]};export{me as Default,ue as LongDescription,_e as ShortTitle,ge as WithMultipleActions,ve as WithSingleAction,pe as __namedExportsOrder,F as default};
