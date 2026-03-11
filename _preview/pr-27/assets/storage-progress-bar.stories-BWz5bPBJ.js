import{n as B,o as M,g as C,d as v,k as c,m as s,i as e,p as P,f as A,e as O,s as l}from"./iframe-CWf27PRy.js";import{i as j}from"./legacy-DQA76Hu_.js";import{c as K,d as k}from"./create-runtime-stories-Bm_4wmfQ.js";import{S as m}from"./storage-progress-bar-C-JZq-D8.js";import{e as E,i as I}from"./cn-BtxYAf1B.js";import"./preload-helper-CFVQb_FG.js";const R=(g,o=B)=>{var a=q(),t=s(a);m(t,M(o));var i=e(t,2),d=s(i);C(()=>l(d,`${o().percent??""}% used`)),v(g,a)},T={title:"UI/StorageProgressBar",component:m,render:R,args:{percent:50},argTypes:{percent:{control:{type:"range",min:0,max:100,step:1}}}},{Story:r}=k();var q=c('<div class="w-64"><!> <p class="mt-1 text-xs text-muted-foreground"> </p></div>'),z=c('<div><div class="flex justify-between text-xs text-muted-foreground mb-1"><span> </span> <span> </span></div> <!></div>'),D=c('<div class="space-y-4 w-64"></div>'),F=c("<!> <!> <!> <!> <!>",1);function S(g,o){P(o,!1),j();var a=F(),t=A(a);r(t,{name:"Low Usage",args:{percent:30},parameters:{__svelteCsf:{rawCode:`<div class="w-64">
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
</div>`}}}),v(g,a),O()}S.__docgen={data:[],name:"storage-progress-bar.stories.svelte"};const n=K(S,T),Y=["LowUsage","MediumUsage","Warning","Critical","AllLevels"],Z={...n.LowUsage,tags:["svelte-csf-v5"]},ee={...n.MediumUsage,tags:["svelte-csf-v5"]},se={...n.Warning,tags:["svelte-csf-v5"]},ae={...n.Critical,tags:["svelte-csf-v5"]},te={...n.AllLevels,tags:["svelte-csf-v5"]};export{te as AllLevels,ae as Critical,Z as LowUsage,ee as MediumUsage,se as Warning,Y as __namedExportsOrder,T as default};
