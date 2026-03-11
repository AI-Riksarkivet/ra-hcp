import{p as I,q as o,A as i,f as $,n as a,i as p,d as D,e as E,j as C,r as m,h as c}from"./iframe-zLStlQv7.js";import{c as w,d as L}from"./create-runtime-stories-Dn8qDVdA.js";import{I as r}from"./ip-list-editor-g8maO-OQ.js";import"./preload-helper-PPVm8Dsz.js";import"./legacy-DIRdaJBZ.js";import"./each-X6WZQib-.js";import"./button-uH4Qgsaz.js";import"./cn-_yov3II5.js";import"./index-DW9qdgWl.js";import"./this-q4fHJjNK.js";import"./input-BwLoZrRU.js";import"./input-BoxI7ix9.js";import"./badge-DrKQjqOU.js";import"./Icon-DLuaEcmj.js";import"./label-CWq3E_vx.js";import"./create-id-DyTfIm46.js";import"./plus-CSmk7NxA.js";import"./x-FwE0VrNm.js";const P={title:"UI/IpListEditor",component:r,args:{label:"Allowed IPs",placeholder:"IP address or CIDR (e.g. 10.0.0.0/8)",variant:"secondary",emptyText:"No addresses configured.",disabled:!1},argTypes:{label:{control:"text"},placeholder:{control:"text"},variant:{control:"select",options:["secondary","destructive"]},emptyText:{control:"text"},disabled:{control:"boolean"}}},{Story:l}=L();var V=C("<!> <!> <!> <!>",1);function x(f,T){I(T,!0);let b=o(i([])),u=o(i(["10.0.0.0/8","192.168.1.0/24","172.16.0.0/12"])),v=o(i(["10.0.0.1","192.168.1.100"]));var g=V(),_=$(g);l(_,{name:"Empty",args:{label:"Allowed IPs"},template:(t,e=a)=>{r(t,{get label(){return e().label},get placeholder(){return e().placeholder},get variant(){return e().variant},get emptyText(){return e().emptyText},get disabled(){return e().disabled},get addresses(){return c(b)},set addresses(s){m(b,s,!0)}})},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<IpListEditor
	bind:addresses={emptyAddresses}
	label={args.label}
	placeholder={args.placeholder}
	variant={args.variant}
	emptyText={args.emptyText}
	disabled={args.disabled}
/>`}}});var y=p(_,2);l(y,{name:"With Addresses",args:{label:"Allow List"},template:(t,e=a)=>{r(t,{get label(){return e().label},get placeholder(){return e().placeholder},get variant(){return e().variant},get emptyText(){return e().emptyText},get disabled(){return e().disabled},get addresses(){return c(u)},set addresses(s){m(u,s,!0)}})},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<IpListEditor
	bind:addresses={populatedAddresses}
	label={args.label}
	placeholder={args.placeholder}
	variant={args.variant}
	emptyText={args.emptyText}
	disabled={args.disabled}
/>`}}});var h=p(y,2);l(h,{name:"Destructive Variant",args:{label:"Deny List",variant:"destructive",placeholder:"Block IP address...",emptyText:"No blocked addresses."},template:(t,e=a)=>{r(t,{get label(){return e().label},get placeholder(){return e().placeholder},get variant(){return e().variant},get emptyText(){return e().emptyText},get disabled(){return e().disabled},get addresses(){return c(v)},set addresses(s){m(v,s,!0)}})},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<IpListEditor
	bind:addresses={destructiveAddresses}
	label={args.label}
	placeholder={args.placeholder}
	variant={args.variant}
	emptyText={args.emptyText}
	disabled={args.disabled}
/>`}}});var A=p(h,2);l(A,{name:"Disabled",args:{label:"Read-only IPs",disabled:!0},template:(t,e=a)=>{r(t,{addresses:["10.0.0.0/8","192.168.1.0/24"],get label(){return e().label},get placeholder(){return e().placeholder},get variant(){return e().variant},get emptyText(){return e().emptyText},get disabled(){return e().disabled}})},$$slots:{template:!0},parameters:{__svelteCsf:{rawCode:`<IpListEditor
	addresses={['10.0.0.0/8', '192.168.1.0/24']}
	label={args.label}
	placeholder={args.placeholder}
	variant={args.variant}
	emptyText={args.emptyText}
	disabled={args.disabled}
/>`}}}),D(f,g),E()}x.__docgen={data:[],name:"ip-list-editor.stories.svelte"};const d=w(x,P),X=["Empty","WithAddresses","DestructiveVariant","Disabled"],Y={...d.Empty,tags:["svelte-csf-v5"]},Z={...d.WithAddresses,tags:["svelte-csf-v5"]},ee={...d.DestructiveVariant,tags:["svelte-csf-v5"]},te={...d.Disabled,tags:["svelte-csf-v5"]};export{ee as DestructiveVariant,te as Disabled,Y as Empty,Z as WithAddresses,X as __namedExportsOrder,P as default};
