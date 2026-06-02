import{p as C,f as _,d as t,a as f,o as c,k as u}from"./iframe-BLq-IXw7.js";import{i as v}from"./legacy-Ci8bO8La.js";import{c as h,d as O}from"./create-runtime-stories-Bj5LuboW.js";import{C as w}from"./cors-editor-B07DO98L.js";import"./preload-helper-PPVm8Dsz.js";import"./button-DqmmnB3v.js";import"./index-ldovL64k.js";import"./this-5dDYTdTk.js";import"./label-B532bab9.js";import"./input-CSZEXQ_3.js";import"./card-title-ezM6MUMx.js";import"./save-button-D5BaFS8u.js";import"./loader-circle-BONFkgg1.js";import"./Icon-BM2c6fgH.js";import"./each-BUqwbEfg.js";import"./delete-confirm-dialog-Fxz93GrN.js";import"./alert-dialog-description-Cnqao1aK.js";import"./dialog-description-8sP4BR7d.js";import"./checkbox-BYm6U598.js";import"./check-BHS15c9r.js";import"./toast-state.svelte-ahoTWQ3c.js";const{fn:l}=__STORYBOOK_MODULE_TEST__,E={title:"UI/CorsEditor",component:w,args:{corsXml:"",loading:!1,title:"CORS Configuration",description:"",onsave:l(),ondelete:l()}},{Story:e}=O();var R=u("<!> <!> <!> <!> <!>",1);function d(m,p){C(p,!1),v();var r=R(),s=_(r);e(s,{name:"Empty",args:{corsXml:""},parameters:{__svelteCsf:{rawCode:"<CorsEditor {...args} />"}}});var i=t(s,2);e(i,{name:"With Configuration",args:{corsXml:`<CORSConfiguration>
  <CORSRule>
    <AllowedOrigin>https://example.com</AllowedOrigin>
    <AllowedMethod>GET</AllowedMethod>
    <AllowedMethod>PUT</AllowedMethod>
    <AllowedHeader>*</AllowedHeader>
    <MaxAgeSeconds>3600</MaxAgeSeconds>
  </CORSRule>
</CORSConfiguration>`},parameters:{__svelteCsf:{rawCode:"<CorsEditor {...args} />"}}});var a=t(i,2);e(a,{name:"Loading",args:{corsXml:"",loading:!0,ondelete:void 0},parameters:{__svelteCsf:{rawCode:"<CorsEditor {...args} />"}}});var n=t(a,2);e(n,{name:"Without Delete",args:{corsXml:`<CORSConfiguration>
  <CORSRule>
    <AllowedOrigin>*</AllowedOrigin>
    <AllowedMethod>GET</AllowedMethod>
  </CORSRule>
</CORSConfiguration>`,ondelete:void 0},parameters:{__svelteCsf:{rawCode:"<CorsEditor {...args} />"}}});var g=t(n,2);e(g,{name:"Custom Title",args:{corsXml:"",title:"Namespace CORS",description:"Configure cross-origin resource sharing rules for this namespace.",ondelete:void 0},parameters:{__svelteCsf:{rawCode:"<CorsEditor {...args} />"}}}),f(m,r),c()}d.__docgen={data:[],name:"cors-editor.stories.svelte"};const o=h(d,E),Y=["Empty","WithConfiguration","Loading","WithoutDelete","CustomTitle"],j={...o.Empty,tags:["svelte-csf-v5"]},q={...o.WithConfiguration,tags:["svelte-csf-v5"]},z={...o.Loading,tags:["svelte-csf-v5"]},F={...o.WithoutDelete,tags:["svelte-csf-v5"]},J={...o.CustomTitle,tags:["svelte-csf-v5"]};export{J as CustomTitle,j as Empty,z as Loading,q as WithConfiguration,F as WithoutDelete,Y as __namedExportsOrder,E as default};
