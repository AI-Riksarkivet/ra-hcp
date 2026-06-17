import{i as e}from"./preload-helper-xPQekRTU.js";import{Qt as t,Zt as n,hn as r,jt as i,kt as a,rt as o,s,t as c,tt as l,vn as u}from"./client-DASBvjj6.js";import{rt as d}from"./iframe-DJqng2Wf.js";import{i as f,n as p,r as m,t as h}from"./create-runtime-stories-B6HvUOJ0.js";import{n as g,t as _}from"./cors-editor-QTkjroW-.js";function v(e,r){t(r,!1),s();var o=S(),c=a(o);x(c,{name:`Empty`,args:{corsXml:``},parameters:{__svelteCsf:{rawCode:`<CorsEditor {...args} />`}}});var u=i(c,2);x(u,{name:`With Configuration`,args:{corsXml:`<CORSConfiguration>
  <CORSRule>
    <AllowedOrigin>https://example.com</AllowedOrigin>
    <AllowedMethod>GET</AllowedMethod>
    <AllowedMethod>PUT</AllowedMethod>
    <AllowedHeader>*</AllowedHeader>
    <MaxAgeSeconds>3600</MaxAgeSeconds>
  </CORSRule>
</CORSConfiguration>`},parameters:{__svelteCsf:{rawCode:`<CorsEditor {...args} />`}}});var d=i(u,2);x(d,{name:`Loading`,args:{corsXml:``,loading:!0,ondelete:void 0},parameters:{__svelteCsf:{rawCode:`<CorsEditor {...args} />`}}});var f=i(d,2);x(f,{name:`Without Delete`,args:{corsXml:`<CORSConfiguration>
  <CORSRule>
    <AllowedOrigin>*</AllowedOrigin>
    <AllowedMethod>GET</AllowedMethod>
  </CORSRule>
</CORSConfiguration>`,ondelete:void 0},parameters:{__svelteCsf:{rawCode:`<CorsEditor {...args} />`}}}),x(i(f,2),{name:`Custom Title`,args:{corsXml:``,title:`Namespace CORS`,description:`Configure cross-origin resource sharing rules for this namespace.`,ondelete:void 0},parameters:{__svelteCsf:{rawCode:`<CorsEditor {...args} />`}}}),l(e,o),n()}var y,b,x,S,C,w,T,E,D,O,k;e((()=>{u(),d(),r(),f(),g(),c(),p(),{fn:y}=__STORYBOOK_MODULE_TEST__,b={title:`UI/CorsEditor`,component:_,args:{corsXml:``,loading:!1,title:`CORS Configuration`,description:``,onsave:y(),ondelete:y()}},{Story:x}=m(b),S=o(`<!> <!> <!> <!> <!>`,1),v.__docgen={data:[],name:`cors-editor.stories.svelte`},C=h(v,b),w=[`Empty`,`WithConfiguration`,`Loading`,`WithoutDelete`,`CustomTitle`],T={...C.Empty,tags:[`svelte-csf-v5`]},E={...C.WithConfiguration,tags:[`svelte-csf-v5`]},D={...C.Loading,tags:[`svelte-csf-v5`]},O={...C.WithoutDelete,tags:[`svelte-csf-v5`]},k={...C.CustomTitle,tags:[`svelte-csf-v5`]}}))();export{k as CustomTitle,T as Empty,D as Loading,E as WithConfiguration,O as WithoutDelete,w as __namedExportsOrder,b as default};