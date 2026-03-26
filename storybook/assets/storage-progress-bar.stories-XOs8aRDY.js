import{n as W,s as E,g as $,a as i,k as g,m as t,d as e,p as M,f as A,o as Q,h as l}from"./iframe-DFtYtFsL.js";import{i as j}from"./legacy-D7OnDY3G.js";import{c as q,d as K}from"./create-runtime-stories-CO2bfBCH.js";import{S as m}from"./storage-progress-bar-lhQ0c6CC.js";import{e as k,i as I}from"./each-BlWt3Neu.js";import"./preload-helper-PPVm8Dsz.js";const R=(c,d=W)=>{var r=z(),n=t(r);m(n,E(d));var p=e(n,2),v=t(p);$(()=>l(v,`${d().percent??""}% used`)),i(c,r)},T={title:"UI/StorageProgressBar",component:m,render:R,args:{percent:50},argTypes:{percent:{control:{type:"range",min:0,max:150,step:1}}}},{Story:s}=K();var z=g('<div class="w-64"><!> <p class="mt-1 text-xs text-muted-foreground"> </p></div>'),D=g('<div><div class="flex justify-between text-xs text-muted-foreground mb-1"><span> </span> <span> </span></div> <!></div>'),F=g('<div class="space-y-4 w-64"></div>'),G=g("<!> <!> <!> <!> <!> <!> <!>",1);function y(c,d){M(d,!1),j();var r=G(),n=A(r);s(n,{name:"Low Usage",args:{percent:30},parameters:{__svelteCsf:{rawCode:`<div class="w-64">
	<StorageProgressBar {...args} />
	<p class="mt-1 text-xs text-muted-foreground">{args.percent}% used</p>
</div>`}}});var p=e(n,2);s(p,{name:"Medium Usage",args:{percent:65},parameters:{__svelteCsf:{rawCode:`<div class="w-64">
	<StorageProgressBar {...args} />
	<p class="mt-1 text-xs text-muted-foreground">{args.percent}% used</p>
</div>`}}});var v=e(p,2);s(v,{name:"Warning",args:{percent:80},parameters:{__svelteCsf:{rawCode:`<div class="w-64">
	<StorageProgressBar {...args} />
	<p class="mt-1 text-xs text-muted-foreground">{args.percent}% used</p>
</div>`}}});var _=e(v,2);s(_,{name:"Critical",args:{percent:95},parameters:{__svelteCsf:{rawCode:`<div class="w-64">
	<StorageProgressBar {...args} />
	<p class="mt-1 text-xs text-muted-foreground">{args.percent}% used</p>
</div>`}}});var u=e(_,2);s(u,{name:"Empty",args:{percent:0},parameters:{__svelteCsf:{rawCode:`<div class="w-64">
	<StorageProgressBar {...args} />
	<p class="mt-1 text-xs text-muted-foreground">{args.percent}% used</p>
</div>`}}});var f=e(u,2);s(f,{name:"Over Quota",args:{percent:120},parameters:{__svelteCsf:{rawCode:`<div class="w-64">
	<StorageProgressBar {...args} />
	<p class="mt-1 text-xs text-muted-foreground">{args.percent}% used</p>
</div>`}}});var U=e(f,2);s(U,{name:"All Levels",template:L=>{var x=F();k(x,4,()=>[0,10,30,50,70,80,90,95,100,120],I,(O,o)=>{var w=D(),C=t(w),S=t(C),b=t(S),h=e(S,2),B=t(h),P=e(C,2);m(P,{get percent(){return o}}),$(()=>{l(b,`${o??""}%`),l(B,o>100?"Over quota":o>90?"Critical":o>70?"Warning":"OK")}),i(O,w)}),i(L,x)},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<div class="space-y-4 w-64">
	{#each [0, 10, 30, 50, 70, 80, 90, 95, 100, 120] as pct}
		<div>
			<div class="flex justify-between text-xs text-muted-foreground mb-1">
				<span>{pct}%</span>
				<span
					>{pct > 100
						? 'Over quota'
						: pct > 90
							? 'Critical'
							: pct > 70
								? 'Warning'
								: 'OK'}</span
				>
			</div>
			<StorageProgressBar percent={pct} />
		</div>
	{/each}
</div>`}}}),i(c,r),Q()}y.__docgen={data:[],name:"storage-progress-bar.stories.svelte"};const a=q(y,T),ee=["LowUsage","MediumUsage","Warning","Critical","Empty","OverQuota","AllLevels"],se={...a.LowUsage,tags:["svelte-csf-v5"]},ae={...a.MediumUsage,tags:["svelte-csf-v5"]},te={...a.Warning,tags:["svelte-csf-v5"]},re={...a.Critical,tags:["svelte-csf-v5"]},ne={...a.Empty,tags:["svelte-csf-v5"]},oe={...a.OverQuota,tags:["svelte-csf-v5"]},de={...a.AllLevels,tags:["svelte-csf-v5"]};export{de as AllLevels,re as Critical,ne as Empty,se as LowUsage,ae as MediumUsage,oe as OverQuota,te as Warning,ee as __namedExportsOrder,T as default};
