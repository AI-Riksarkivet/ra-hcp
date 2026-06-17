import{i as e}from"./preload-helper-xPQekRTU.js";import{$ as t,L as n,Ot as r,Qt as i,St as a,Zt as o,hn as s,jt as c,kt as l,o as u,rt as d,s as f,sn as p,t as m,tt as h,un as g,vn as _}from"./client-DASBvjj6.js";import{rt as v}from"./iframe-DJqng2Wf.js";import{i as y,n as b,r as x,t as S}from"./create-runtime-stories-B6HvUOJ0.js";import{n as C,t as w}from"./storage-progress-bar-aFLJRXRm.js";function T(e,s){i(s,!1),f();var u=M(),d=l(u);O(d,{name:`Low Usage`,args:{percent:30},parameters:{__svelteCsf:{rawCode:`<div class="w-64">
	<StorageProgressBar {...args} />
	<p class="mt-1 text-xs text-muted-foreground">{args.percent}% used</p>
</div>`}}});var m=c(d,2);O(m,{name:`Medium Usage`,args:{percent:65},parameters:{__svelteCsf:{rawCode:`<div class="w-64">
	<StorageProgressBar {...args} />
	<p class="mt-1 text-xs text-muted-foreground">{args.percent}% used</p>
</div>`}}});var g=c(m,2);O(g,{name:`Warning`,args:{percent:80},parameters:{__svelteCsf:{rawCode:`<div class="w-64">
	<StorageProgressBar {...args} />
	<p class="mt-1 text-xs text-muted-foreground">{args.percent}% used</p>
</div>`}}});var _=c(g,2);O(_,{name:`Critical`,args:{percent:95},parameters:{__svelteCsf:{rawCode:`<div class="w-64">
	<StorageProgressBar {...args} />
	<p class="mt-1 text-xs text-muted-foreground">{args.percent}% used</p>
</div>`}}});var v=c(_,2);O(v,{name:`Empty`,args:{percent:0},parameters:{__svelteCsf:{rawCode:`<div class="w-64">
	<StorageProgressBar {...args} />
	<p class="mt-1 text-xs text-muted-foreground">{args.percent}% used</p>
</div>`}}});var y=c(v,2);O(y,{name:`Over Quota`,args:{percent:120},parameters:{__svelteCsf:{rawCode:`<div class="w-64">
	<StorageProgressBar {...args} />
	<p class="mt-1 text-xs text-muted-foreground">{args.percent}% used</p>
</div>`}}});var b=c(y,2);O(b,{name:`All Levels`,template:e=>{var i=j();n(i,4,()=>[0,10,30,50,70,80,90,95,100,120],e=>e,(e,n)=>{var i=A(),o=r(i),s=r(o),l=r(s);p(s);var u=c(s,2),d=r(u,!0);p(u),p(o),w(c(o,2),{get percent(){return n}}),p(i),a(()=>{t(l,`${n??``}%`),t(d,n>100?`Over quota`:n>90?`Critical`:n>70?`Warning`:`OK`)}),h(e,i)}),p(i),h(e,i)},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<div class="space-y-4 w-64">
	{#each [0, 10, 30, 50, 70, 80, 90, 95, 100, 120] as pct (pct)}
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
</div>`}}}),h(e,u),o()}var E,D,O,k,A,j,M,N,P,F,I,L,R,z,B,V;e((()=>{_(),v(),s(),y(),C(),m(),b(),E=(e,n=g)=>{var i=k(),o=r(i);w(o,u(n));var s=c(o,2),l=r(s);p(s),p(i),a(()=>t(l,`${n().percent??``}% used`)),h(e,i)},D={title:`UI/StorageProgressBar`,component:w,render:E,args:{percent:50},argTypes:{percent:{control:{type:`range`,min:0,max:150,step:1}}}},{Story:O}=x(D),k=d(`<div class="w-64"><!> <p class="mt-1 text-xs text-muted-foreground"> </p></div>`),A=d(`<div><div class="flex justify-between text-xs text-muted-foreground mb-1"><span> </span> <span> </span></div> <!></div>`),j=d(`<div class="space-y-4 w-64"></div>`),M=d(`<!> <!> <!> <!> <!> <!> <!>`,1),T.__docgen={data:[],name:`storage-progress-bar.stories.svelte`},N=S(T,D),P=[`LowUsage`,`MediumUsage`,`Warning`,`Critical`,`Empty`,`OverQuota`,`AllLevels`],F={...N.LowUsage,tags:[`svelte-csf-v5`]},I={...N.MediumUsage,tags:[`svelte-csf-v5`]},L={...N.Warning,tags:[`svelte-csf-v5`]},R={...N.Critical,tags:[`svelte-csf-v5`]},z={...N.Empty,tags:[`svelte-csf-v5`]},B={...N.OverQuota,tags:[`svelte-csf-v5`]},V={...N.AllLevels,tags:[`svelte-csf-v5`]}}))();export{V as AllLevels,R as Critical,z as Empty,F as LowUsage,I as MediumUsage,B as OverQuota,L as Warning,P as __namedExportsOrder,D as default};