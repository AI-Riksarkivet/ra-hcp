import{i as e}from"./preload-helper-xPQekRTU.js";import{It as t,Nt as n,Qt as r,Rt as i,Zt as a,hn as o,ht as s,jt as c,kt as l,rt as u,t as d,tt as f,un as p,vn as m}from"./client-DjbtzEc-.js";import{i as h,n as g,r as _,t as v}from"./create-runtime-stories-CLJZPzla.js";import{n as y,t as b}from"./ip-list-editor-Bzg0CZI9.js";function x(e,o){r(o,!0);let u=i(n([])),d=i(n([`10.0.0.0/8`,`192.168.1.0/24`,`172.16.0.0/12`])),m=i(n([`10.0.0.1`,`192.168.1.100`]));var h=w(),g=l(h);C(g,{name:`Empty`,args:{label:`Allowed IPs`},template:(e,n=p)=>{b(e,{get label(){return n().label},get placeholder(){return n().placeholder},get variant(){return n().variant},get emptyText(){return n().emptyText},get disabled(){return n().disabled},get addresses(){return s(u)},set addresses(e){t(u,e,!0)}})},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<IpListEditor
	bind:addresses={emptyAddresses}
	label={args.label}
	placeholder={args.placeholder}
	variant={args.variant}
	emptyText={args.emptyText}
	disabled={args.disabled}
/>`}}});var _=c(g,2);C(_,{name:`With Addresses`,args:{label:`Allow List`},template:(e,n=p)=>{b(e,{get label(){return n().label},get placeholder(){return n().placeholder},get variant(){return n().variant},get emptyText(){return n().emptyText},get disabled(){return n().disabled},get addresses(){return s(d)},set addresses(e){t(d,e,!0)}})},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<IpListEditor
	bind:addresses={populatedAddresses}
	label={args.label}
	placeholder={args.placeholder}
	variant={args.variant}
	emptyText={args.emptyText}
	disabled={args.disabled}
/>`}}});var v=c(_,2);C(v,{name:`Destructive Variant`,args:{label:`Deny List`,variant:`destructive`,placeholder:`Block IP address...`,emptyText:`No blocked addresses.`},template:(e,n=p)=>{b(e,{get label(){return n().label},get placeholder(){return n().placeholder},get variant(){return n().variant},get emptyText(){return n().emptyText},get disabled(){return n().disabled},get addresses(){return s(m)},set addresses(e){t(m,e,!0)}})},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<IpListEditor
	bind:addresses={destructiveAddresses}
	label={args.label}
	placeholder={args.placeholder}
	variant={args.variant}
	emptyText={args.emptyText}
	disabled={args.disabled}
/>`}}});var y=c(v,2);C(y,{name:`Disabled`,args:{label:`Read-only IPs`,disabled:!0},template:(e,t=p)=>{b(e,{addresses:[`10.0.0.0/8`,`192.168.1.0/24`],get label(){return t().label},get placeholder(){return t().placeholder},get variant(){return t().variant},get emptyText(){return t().emptyText},get disabled(){return t().disabled}})},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<IpListEditor
	addresses={['10.0.0.0/8', '192.168.1.0/24']}
	label={args.label}
	placeholder={args.placeholder}
	variant={args.variant}
	emptyText={args.emptyText}
	disabled={args.disabled}
/>`}}}),f(e,h),a()}var S,C,w,T,E,D,O,k,A;e((()=>{m(),o(),h(),y(),d(),g(),S={title:`UI/IpListEditor`,component:b,args:{label:`Allowed IPs`,placeholder:`IP address or CIDR (e.g. 10.0.0.0/8)`,variant:`secondary`,emptyText:`No addresses configured.`,disabled:!1},argTypes:{variant:{control:`select`,options:[`secondary`,`destructive`]}}},{Story:C}=_(S),w=u(`<!> <!> <!> <!>`,1),x.__docgen={data:[],name:`ip-list-editor.stories.svelte`},T=v(x,S),E=[`Empty`,`WithAddresses`,`DestructiveVariant`,`Disabled`],D={...T.Empty,tags:[`svelte-csf-v5`]},O={...T.WithAddresses,tags:[`svelte-csf-v5`]},k={...T.DestructiveVariant,tags:[`svelte-csf-v5`]},A={...T.Disabled,tags:[`svelte-csf-v5`]}}))();export{k as DestructiveVariant,A as Disabled,D as Empty,O as WithAddresses,E as __namedExportsOrder,S as default};