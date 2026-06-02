import{p as q,z as h,g as b,v as o,a as S,o as F,x as A,m as f,k as P,d as T,h as w,u as C,C as H}from"./iframe-BLq-IXw7.js";import{b as O}from"./input-CSZEXQ_3.js";import"./preload-helper-PPVm8Dsz.js";function k(t,e,d){const c=e.trim();return c.length===0?{prefix:t,flat:d}:{prefix:t+c,flat:!0}}var M=P('<div class="space-y-2 p-4"><input class="rounded border px-3 py-1 text-sm" placeholder="Search…" data-testid="search"/> <div data-testid="query-prefix"> </div> <div data-testid="query-flat"> </div></div>');function B(t,e){q(e,!0);let d=h(e,"navigatedPrefix",3,""),c=h(e,"initialFlat",3,!1),p=A(""),u=H(()=>k(d(),o(p),c()));var m=M(),x=f(m),g=T(x,2),E=f(g),_=T(g,2),I=f(_);b(y=>{w(E,o(u).prefix),w(I,y)},[()=>String(o(u).flat)]),O(x,()=>o(p),y=>C(p,y)),S(t,m),F()}B.__docgen={data:[{name:"navigatedPrefix",visibility:"public",keywords:[],kind:"let",type:{kind:"type",type:"string",text:"string"},static:!1,readonly:!1,defaultValue:'""'},{name:"initialFlat",visibility:"public",keywords:[],kind:"let",type:{kind:"type",type:"boolean",text:"boolean"},static:!1,readonly:!1,defaultValue:"false"}],name:"object-search-test-harness.svelte"};const{expect:a,userEvent:v,within:l}=__STORYBOOK_MODULE_TEST__,V={title:"Tests/ObjectSearch",component:B,tags:["!autodocs"]},s={args:{navigatedPrefix:"",initialFlat:!1},play:async({canvasElement:t})=>{const e=l(t);await a(e.getByTestId("query-prefix")).toBeEmptyDOMElement(),await a(e.getByTestId("query-flat")).toHaveTextContent("false")}},n={args:{navigatedPrefix:"",initialFlat:!1},play:async({canvasElement:t})=>{const e=l(t);await v.type(e.getByTestId("search"),"A0075850"),await a(e.getByTestId("query-prefix")).toHaveTextContent("A0075850"),await a(e.getByTestId("query-flat")).toHaveTextContent("true")}},r={args:{navigatedPrefix:"A0075850/",initialFlat:!1},play:async({canvasElement:t})=>{const e=l(t);await v.type(e.getByTestId("search"),"A0075850_002"),await a(e.getByTestId("query-prefix")).toHaveTextContent("A0075850/A0075850_002"),await a(e.getByTestId("query-flat")).toHaveTextContent("true")}},i={args:{navigatedPrefix:"",initialFlat:!1},play:async({canvasElement:t})=>{const e=l(t);await v.type(e.getByTestId("search"),"   "),await a(e.getByTestId("query-prefix")).toBeEmptyDOMElement(),await a(e.getByTestId("query-flat")).toHaveTextContent("false")}};s.parameters={...s.parameters,docs:{...s.parameters?.docs,source:{originalSource:`{
  args: {
    navigatedPrefix: "",
    initialFlat: false
  },
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByTestId("query-prefix")).toBeEmptyDOMElement();
    await expect(canvas.getByTestId("query-flat")).toHaveTextContent("false");
  }
}`,...s.parameters?.docs?.source},description:{story:"No search term: list the navigated prefix in the current (folder) view.",...s.parameters?.docs?.description}}};n.parameters={...n.parameters,docs:{...n.parameters?.docs,source:{originalSource:`{
  args: {
    navigatedPrefix: "",
    initialFlat: false
  },
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    await userEvent.type(canvas.getByTestId("search"), "A0075850");
    await expect(canvas.getByTestId("query-prefix")).toHaveTextContent("A0075850");
    await expect(canvas.getByTestId("query-flat")).toHaveTextContent("true");
  }
}`,...n.parameters?.docs?.source},description:{story:`Searching at the bucket root must query the backend by prefix in flat mode,
so a batch far down the alphabet (e.g. after tens of thousands of numeric
keys) is found instead of silently missing.`,...n.parameters?.docs?.description}}};r.parameters={...r.parameters,docs:{...r.parameters?.docs,source:{originalSource:`{
  args: {
    navigatedPrefix: "A0075850/",
    initialFlat: false
  },
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    await userEvent.type(canvas.getByTestId("search"), "A0075850_002");
    await expect(canvas.getByTestId("query-prefix")).toHaveTextContent("A0075850/A0075850_002");
    await expect(canvas.getByTestId("query-flat")).toHaveTextContent("true");
  }
}`,...r.parameters?.docs?.source},description:{story:"Searching inside a folder prepends the navigated prefix to the term.",...r.parameters?.docs?.description}}};i.parameters={...i.parameters,docs:{...i.parameters?.docs,source:{originalSource:`{
  args: {
    navigatedPrefix: "",
    initialFlat: false
  },
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    await userEvent.type(canvas.getByTestId("search"), "   ");
    await expect(canvas.getByTestId("query-prefix")).toBeEmptyDOMElement();
    await expect(canvas.getByTestId("query-flat")).toHaveTextContent("false");
  }
}`,...i.parameters?.docs?.source},description:{story:"Whitespace-only input is not treated as a search (no prefix narrowing).",...i.parameters?.docs?.description}}};const K=["EmptySearchKeepsFolderView","SearchAtRootMatchesPrefixFlat","SearchWithinFolderPrependsPrefix","WhitespaceIsNotASearch"];export{s as EmptySearchKeepsFolderView,n as SearchAtRootMatchesPrefixFlat,r as SearchWithinFolderPrependsPrefix,i as WhitespaceIsNotASearch,K as __namedExportsOrder,V as default};
