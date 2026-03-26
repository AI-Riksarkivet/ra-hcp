import{p as A,x as i,L as o,f as $,n as r,d as p,a as D,o as E,k as C,u as m,v as c}from"./iframe-DFtYtFsL.js";import{c as L,d as w}from"./create-runtime-stories-CO2bfBCH.js";import{I as a}from"./ip-list-editor-BKYQpqeM.js";import"./preload-helper-PPVm8Dsz.js";import"./legacy-D7OnDY3G.js";import"./each-BlWt3Neu.js";import"./button-BbjatG8g.js";import"./index-KRrpyZZM.js";import"./this-Dypaan2Q.js";import"./input-Btbn_eAX.js";import"./input-BYhCp0Wp.js";import"./badge-DOktaLwq.js";import"./Icon-CYtk7mac.js";import"./label-mrAA5l7e.js";import"./plus-Bj06M1nx.js";import"./x-DNYSgm9v.js";const P={title:"UI/IpListEditor",component:a,args:{label:"Allowed IPs",placeholder:"IP address or CIDR (e.g. 10.0.0.0/8)",variant:"secondary",emptyText:"No addresses configured.",disabled:!1},argTypes:{variant:{control:"select",options:["secondary","destructive"]}}},{Story:d}=w();var V=C("<!> <!> <!> <!>",1);function x(f,T){A(T,!0);let b=i(o([])),u=i(o(["10.0.0.0/8","192.168.1.0/24","172.16.0.0/12"])),v=i(o(["10.0.0.1","192.168.1.100"]));var g=V(),_=$(g);d(_,{name:"Empty",args:{label:"Allowed IPs"},template:(t,e=r)=>{a(t,{get label(){return e().label},get placeholder(){return e().placeholder},get variant(){return e().variant},get emptyText(){return e().emptyText},get disabled(){return e().disabled},get addresses(){return c(b)},set addresses(s){m(b,s,!0)}})},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<IpListEditor
	bind:addresses={emptyAddresses}
	label={args.label}
	placeholder={args.placeholder}
	variant={args.variant}
	emptyText={args.emptyText}
	disabled={args.disabled}
/>`}}});var y=p(_,2);d(y,{name:"With Addresses",args:{label:"Allow List"},template:(t,e=r)=>{a(t,{get label(){return e().label},get placeholder(){return e().placeholder},get variant(){return e().variant},get emptyText(){return e().emptyText},get disabled(){return e().disabled},get addresses(){return c(u)},set addresses(s){m(u,s,!0)}})},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<IpListEditor
	bind:addresses={populatedAddresses}
	label={args.label}
	placeholder={args.placeholder}
	variant={args.variant}
	emptyText={args.emptyText}
	disabled={args.disabled}
/>`}}});var h=p(y,2);d(h,{name:"Destructive Variant",args:{label:"Deny List",variant:"destructive",placeholder:"Block IP address...",emptyText:"No blocked addresses."},template:(t,e=r)=>{a(t,{get label(){return e().label},get placeholder(){return e().placeholder},get variant(){return e().variant},get emptyText(){return e().emptyText},get disabled(){return e().disabled},get addresses(){return c(v)},set addresses(s){m(v,s,!0)}})},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<IpListEditor
	bind:addresses={destructiveAddresses}
	label={args.label}
	placeholder={args.placeholder}
	variant={args.variant}
	emptyText={args.emptyText}
	disabled={args.disabled}
/>`}}});var I=p(h,2);d(I,{name:"Disabled",args:{label:"Read-only IPs",disabled:!0},template:(t,e=r)=>{a(t,{addresses:["10.0.0.0/8","192.168.1.0/24"],get label(){return e().label},get placeholder(){return e().placeholder},get variant(){return e().variant},get emptyText(){return e().emptyText},get disabled(){return e().disabled}})},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<IpListEditor
	addresses={['10.0.0.0/8', '192.168.1.0/24']}
	label={args.label}
	placeholder={args.placeholder}
	variant={args.variant}
	emptyText={args.emptyText}
	disabled={args.disabled}
/>`}}}),D(f,g),E()}x.__docgen={data:[],name:"ip-list-editor.stories.svelte"};const l=L(x,P),K=["Empty","WithAddresses","DestructiveVariant","Disabled"],Q={...l.Empty,tags:["svelte-csf-v5"]},X={...l.WithAddresses,tags:["svelte-csf-v5"]},Y={...l.DestructiveVariant,tags:["svelte-csf-v5"]},Z={...l.Disabled,tags:["svelte-csf-v5"]};export{Y as DestructiveVariant,Z as Disabled,Q as Empty,X as WithAddresses,K as __namedExportsOrder,P as default};
