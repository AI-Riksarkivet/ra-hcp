import{n as B,l as M,g as C,d as v,j as c,k as s,i as e,p as P,f as A,e as j,s as l}from"./iframe-yNdMEOQF.js";import{i as O}from"./legacy-D7Ho_9H1.js";import{c as K,d as k}from"./create-runtime-stories-Cm4ppnof.js";import{S as m}from"./storage-progress-bar-DAfAUNgu.js";import{e as E,i as I}from"./each-vZ03cvl4.js";import"./preload-helper-XGDCq6z_.js";import"./cn-_yov3II5.js";const R=(g,o=B)=>{var a=q(),t=s(a);m(t,M(o));var i=e(t,2),d=s(i);C(()=>l(d,`${o().percent??""}% used`)),v(g,a)},T={title:"UI/StorageProgressBar",component:m,render:R,args:{percent:50},argTypes:{percent:{control:{type:"range",min:0,max:100,step:1}}}},{Story:r}=k();var q=c('<div class="w-64"><!> <p class="mt-1 text-xs text-muted-foreground"> </p></div>'),z=c('<div><div class="flex justify-between text-xs text-muted-foreground mb-1"><span> </span> <span> </span></div> <!></div>'),D=c('<div class="space-y-4 w-64"></div>'),F=c("<!> <!> <!> <!> <!>",1);function S(g,o){P(o,!1),O();var a=F(),t=A(a);r(t,{name:"Low Usage",args:{percent:30},parameters:{__svelteCsf:{rawCode:`<div class="w-64">
	<StorageProgressBar {...args} />
	<p class="mt-1 text-xs text-muted-foreground">{args.percent}% used</p>
</div>`}}});var i=e(t,2);r(i,{name:"Medium Usage",args:{percent:65},parameters:{__svelteCsf:{rawCode:`<div class="w-64">
	<StorageProgressBar {...args} />
	<p class="mt-1 text-xs text-muted-foreground">{args.percent}% used</p>
</div>`}}});var d=e(i,2);r(d,{name:"Warning",args:{percent:80},parameters:{__svelteCsf:{rawCode:`<div class="w-64">
	<StorageProgressBar {...args} />
	<p class="mt-1 text-xs text-muted-foreground">{args.percent}% used</p>
</div>`}}});var _=e(d,2);r(_,{name:"Critical",args:{percent:95},parameters:{__svelteCsf:{rawCode:`<div class="w-64">
	<StorageProgressBar {...args} />
	<p class="mt-1 text-xs text-muted-foreground">{args.percent}% used</p>
</div>`}}});var U=e(_,2);r(U,{name:"All Levels",template:$=>{var f=D();E(f,4,()=>[10,30,50,70,80,90,95,100],I,(L,p)=>{var u=z(),x=s(u),w=s(x),b=s(w),h=e(w,2),y=s(h),W=e(x,2);m(W,{get percent(){return p}}),C(()=>{l(b,`${p??""}%`),l(y,p>90?"Critical":p>70?"Warning":"OK")}),v(L,u)}),v($,f)},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<div class="space-y-4 w-64">
	{#each [10, 30, 50, 70, 80, 90, 95, 100] as pct}
		<div>
			<div class="flex justify-between text-xs text-muted-foreground mb-1">
				<span>{pct}%</span>
				<span>{pct > 90 ? 'Critical' : pct > 70 ? 'Warning' : 'OK'}</span>
			</div>
			<StorageProgressBar percent={pct} />
		</div>
	{/each}
</div>`}}}),v(g,a),j()}S.__docgen={data:[],name:"storage-progress-bar.stories.svelte"};const n=K(S,T),Z=["LowUsage","MediumUsage","Warning","Critical","AllLevels"],ee={...n.LowUsage,tags:["svelte-csf-v5"]},se={...n.MediumUsage,tags:["svelte-csf-v5"]},ae={...n.Warning,tags:["svelte-csf-v5"]},te={...n.Critical,tags:["svelte-csf-v5"]},re={...n.AllLevels,tags:["svelte-csf-v5"]};export{re as AllLevels,te as Critical,ee as LowUsage,se as MediumUsage,ae as Warning,Z as __namedExportsOrder,T as default};
