import{i as e}from"./preload-helper-xPQekRTU.js";import{$ as t,Ht as n,It as r,Ot as i,Qt as a,Rt as o,St as s,Zt as c,_ as l,f as u,hn as d,ht as f,i as p,jt as m,rt as h,sn as g,t as _,tt as v,vn as y}from"./client-DjbtzEc-.js";function b(e,t,n){let r=t.trim();return r.length===0?{prefix:e,flat:n}:{prefix:e+r,flat:n}}var x=e((()=>{}));function S(e,d){a(d,!0);let h=p(d,`navigatedPrefix`,3,``),_=p(d,`initialFlat`,3,!1),y=o(``),x=n(()=>b(h(),f(y),_()));var S=C(),w=i(S);l(w);var T=m(w,2),E=i(T,!0);g(T);var D=m(T,2),O=i(D,!0);g(D),g(S),s(e=>{t(E,f(x).prefix),t(O,e)},[()=>String(f(x).flat)]),u(w,()=>f(y),e=>r(y,e)),v(e,S),c()}var C,w=e((()=>{y(),d(),_(),x(),C=h(`<div class="space-y-2 p-4"><input class="rounded border px-3 py-1 text-sm" placeholder="Search…" data-testid="search"/> <div data-testid="query-prefix"> </div> <div data-testid="query-flat"> </div></div>`),S.__docgen={data:[{name:`navigatedPrefix`,visibility:`public`,keywords:[],kind:`let`,type:{kind:`type`,type:`string`,text:`string`},static:!1,readonly:!1,defaultValue:`""`},{name:`initialFlat`,visibility:`public`,keywords:[],kind:`let`,type:{kind:`type`,type:`boolean`,text:`boolean`},static:!1,readonly:!1,defaultValue:`false`}],name:`object-search-test-harness.svelte`}})),T,E,D,O,k,A,j,M,N;e((()=>{w(),{expect:T,userEvent:E,within:D}=__STORYBOOK_MODULE_TEST__,O={title:`Tests/ObjectSearch`,component:S,tags:[`!autodocs`]},k={args:{navigatedPrefix:``,initialFlat:!1},play:async({canvasElement:e})=>{let t=D(e);await T(t.getByTestId(`query-prefix`)).toBeEmptyDOMElement(),await T(t.getByTestId(`query-flat`)).toHaveTextContent(`false`)}},A={args:{navigatedPrefix:``,initialFlat:!1},play:async({canvasElement:e})=>{let t=D(e);await E.type(t.getByTestId(`search`),`A0075850`),await T(t.getByTestId(`query-prefix`)).toHaveTextContent(`A0075850`),await T(t.getByTestId(`query-flat`)).toHaveTextContent(`true`)}},j={args:{navigatedPrefix:`A0075850/`,initialFlat:!1},play:async({canvasElement:e})=>{let t=D(e);await E.type(t.getByTestId(`search`),`A0075850_002`),await T(t.getByTestId(`query-prefix`)).toHaveTextContent(`A0075850/A0075850_002`),await T(t.getByTestId(`query-flat`)).toHaveTextContent(`true`)}},M={args:{navigatedPrefix:``,initialFlat:!1},play:async({canvasElement:e})=>{let t=D(e);await E.type(t.getByTestId(`search`),`   `),await T(t.getByTestId(`query-prefix`)).toBeEmptyDOMElement(),await T(t.getByTestId(`query-flat`)).toHaveTextContent(`false`)}},k.parameters={...k.parameters,docs:{...k.parameters?.docs,source:{originalSource:`{
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
}`,...k.parameters?.docs?.source},description:{story:`No search term: list the navigated prefix in the current (folder) view.`,...k.parameters?.docs?.description}}},A.parameters={...A.parameters,docs:{...A.parameters?.docs,source:{originalSource:`{
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
}`,...A.parameters?.docs?.source},description:{story:`Searching at the bucket root must query the backend by prefix in flat mode,
so a batch far down the alphabet (e.g. after tens of thousands of numeric
keys) is found instead of silently missing.`,...A.parameters?.docs?.description}}},j.parameters={...j.parameters,docs:{...j.parameters?.docs,source:{originalSource:`{
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
}`,...j.parameters?.docs?.source},description:{story:`Searching inside a folder prepends the navigated prefix to the term.`,...j.parameters?.docs?.description}}},M.parameters={...M.parameters,docs:{...M.parameters?.docs,source:{originalSource:`{
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
}`,...M.parameters?.docs?.source},description:{story:`Whitespace-only input is not treated as a search (no prefix narrowing).`,...M.parameters?.docs?.description}}},N=[`EmptySearchKeepsFolderView`,`SearchAtRootMatchesPrefixFlat`,`SearchWithinFolderPrependsPrefix`,`WhitespaceIsNotASearch`]}))();export{k as EmptySearchKeepsFolderView,A as SearchAtRootMatchesPrefixFlat,j as SearchWithinFolderPrependsPrefix,M as WhitespaceIsNotASearch,N as __namedExportsOrder,O as default};