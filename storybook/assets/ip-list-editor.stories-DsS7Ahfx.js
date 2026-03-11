import{p as A,r as o,B as i,f as $,n as r,i as p,d as D,e as E,k as C,v as m,h as c}from"./iframe-0B4E8QaP.js";import{c as w,d as L}from"./create-runtime-stories-9d9CFNUZ.js";import{I as a}from"./ip-list-editor-Dx3g8-ha.js";import"./preload-helper-PPVm8Dsz.js";import"./legacy-BIjO5Qzi.js";import"./cn-CukO2arH.js";import"./button-DjEAsAUk.js";import"./index-CR3ZhuFD.js";import"./Icon-D_OA0LUw.js";import"./input--FKDjf7t.js";import"./input-BvX2LBTw.js";import"./badge-DP7wdP4t.js";import"./label-YdVkTYBi.js";import"./create-id-CPYsmAkK.js";import"./plus-YYxNWKok.js";import"./x-Dz3ueVpA.js";const P={title:"UI/IpListEditor",component:a,args:{label:"Allowed IPs",placeholder:"IP address or CIDR (e.g. 10.0.0.0/8)",variant:"secondary",emptyText:"No addresses configured.",disabled:!1},argTypes:{label:{control:"text"},placeholder:{control:"text"},variant:{control:"select",options:["secondary","destructive"]},emptyText:{control:"text"},disabled:{control:"boolean"}}},{Story:l}=L();var V=C("<!> <!> <!> <!>",1);function x(f,T){A(T,!0);let b=o(i([])),u=o(i(["10.0.0.0/8","192.168.1.0/24","172.16.0.0/12"])),v=o(i(["10.0.0.1","192.168.1.100"]));var g=V(),_=$(g);l(_,{name:"Empty",args:{label:"Allowed IPs"},template:(t,e=r)=>{a(t,{get label(){return e().label},get placeholder(){return e().placeholder},get variant(){return e().variant},get emptyText(){return e().emptyText},get disabled(){return e().disabled},get addresses(){return c(b)},set addresses(s){m(b,s,!0)}})},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<IpListEditor
	bind:addresses={emptyAddresses}
	label={args.label}
	placeholder={args.placeholder}
	variant={args.variant}
	emptyText={args.emptyText}
	disabled={args.disabled}
/>`}}});var y=p(_,2);l(y,{name:"With Addresses",args:{label:"Allow List"},template:(t,e=r)=>{a(t,{get label(){return e().label},get placeholder(){return e().placeholder},get variant(){return e().variant},get emptyText(){return e().emptyText},get disabled(){return e().disabled},get addresses(){return c(u)},set addresses(s){m(u,s,!0)}})},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<IpListEditor
	bind:addresses={populatedAddresses}
	label={args.label}
	placeholder={args.placeholder}
	variant={args.variant}
	emptyText={args.emptyText}
	disabled={args.disabled}
/>`}}});var h=p(y,2);l(h,{name:"Destructive Variant",args:{label:"Deny List",variant:"destructive",placeholder:"Block IP address...",emptyText:"No blocked addresses."},template:(t,e=r)=>{a(t,{get label(){return e().label},get placeholder(){return e().placeholder},get variant(){return e().variant},get emptyText(){return e().emptyText},get disabled(){return e().disabled},get addresses(){return c(v)},set addresses(s){m(v,s,!0)}})},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<IpListEditor
	bind:addresses={destructiveAddresses}
	label={args.label}
	placeholder={args.placeholder}
	variant={args.variant}
	emptyText={args.emptyText}
	disabled={args.disabled}
/>`}}});var I=p(h,2);l(I,{name:"Disabled",args:{label:"Read-only IPs",disabled:!0},template:(t,e=r)=>{a(t,{addresses:["10.0.0.0/8","192.168.1.0/24"],get label(){return e().label},get placeholder(){return e().placeholder},get variant(){return e().variant},get emptyText(){return e().emptyText},get disabled(){return e().disabled}})},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<IpListEditor
	addresses={['10.0.0.0/8', '192.168.1.0/24']}
	label={args.label}
	placeholder={args.placeholder}
	variant={args.variant}
	emptyText={args.emptyText}
	disabled={args.disabled}
/>`}}}),D(f,g),E()}x.__docgen={data:[],name:"ip-list-editor.stories.svelte"};const d=w(x,P),K=["Empty","WithAddresses","DestructiveVariant","Disabled"],Q={...d.Empty,tags:["svelte-csf-v5"]},X={...d.WithAddresses,tags:["svelte-csf-v5"]},Y={...d.DestructiveVariant,tags:["svelte-csf-v5"]},Z={...d.Disabled,tags:["svelte-csf-v5"]};export{Y as DestructiveVariant,Z as Disabled,Q as Empty,X as WithAddresses,K as __namedExportsOrder,P as default};
