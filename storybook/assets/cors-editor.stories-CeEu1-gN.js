import{p as C,f as _,d as t,a as f,o as c,k as u}from"./iframe-DFtYtFsL.js";import{i as v}from"./legacy-D7OnDY3G.js";import{c as h,d as O}from"./create-runtime-stories-CO2bfBCH.js";import{C as w}from"./cors-editor-H7GRF4-7.js";import"./preload-helper-PPVm8Dsz.js";import"./button-BbjatG8g.js";import"./index-KRrpyZZM.js";import"./this-Dypaan2Q.js";import"./label-mrAA5l7e.js";import"./input-BYhCp0Wp.js";import"./card-title-DCJX056x.js";import"./save-button-_AMgjLGF.js";import"./loader-circle-DukIKDwt.js";import"./Icon-CYtk7mac.js";import"./each-BlWt3Neu.js";import"./delete-confirm-dialog-JITcKrtu.js";import"./alert-dialog-description-DTSoaOgT.js";import"./dialog-description-SOuRhX3N.js";import"./checkbox-DA4Nl7aN.js";import"./check-rNiRaSFp.js";import"./toast-state.svelte-BnSQK711.js";const{fn:l}=__STORYBOOK_MODULE_TEST__,E={title:"UI/CorsEditor",component:w,args:{corsXml:"",loading:!1,title:"CORS Configuration",description:"",onsave:l(),ondelete:l()}},{Story:e}=O();var R=u("<!> <!> <!> <!> <!>",1);function d(m,p){C(p,!1),v();var r=R(),s=_(r);e(s,{name:"Empty",args:{corsXml:""},parameters:{__svelteCsf:{rawCode:"<CorsEditor {...args} />"}}});var i=t(s,2);e(i,{name:"With Configuration",args:{corsXml:`<CORSConfiguration>
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
