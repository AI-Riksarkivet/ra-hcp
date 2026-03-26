import{p as se,x as E,L as q,B as j,a as p,o as ce,m as $,d as w,v as s,k as N,C as H,u as v,f as Q,t as U,g as Y,c as oe,h as J}from"./iframe-DFtYtFsL.js";import{c as re,D as le,g as ie,a as de,b as he,r as M,d as W,e as X}from"./data-table-header-button-Dtp2h2b-.js";import{B as z}from"./button-BbjatG8g.js";import{I as ue}from"./input-Btbn_eAX.js";import{S as pe}from"./search-CIyswr76.js";import{T as me}from"./trash-2-C9avNWSC.js";import{S as we}from"./shield-C0akJcpU.js";import"./preload-helper-PPVm8Dsz.js";import"./each-BlWt3Neu.js";import"./this-Dypaan2Q.js";import"./checkbox-DA4Nl7aN.js";import"./legacy-D7OnDY3G.js";import"./input-BYhCp0Wp.js";import"./check-rNiRaSFp.js";import"./Icon-CYtk7mac.js";import"./chevron-right-D1u9wVOz.js";import"./index-KRrpyZZM.js";var ge=N("<!>Delete Selected",1),ye=N("<!>Grant Access",1),ve=N('<div class="flex items-center gap-3 rounded-lg border bg-muted/50 px-4 py-2"><span class="text-sm font-medium"> </span> <!> <!> <!></div>'),Be=N('<div class="space-y-3"><div class="relative max-w-md"><!> <!></div> <!> <!></div>');function Z(o,a){se(a,!0);const t=[{name:"production-data",description:"Main production namespace",hardQuota:"500 GB",hashScheme:"SHA-256"},{name:"staging-env",description:"Staging environment",hardQuota:"100 GB",hashScheme:"SHA-256"},{name:"dev-sandbox",description:"Developer sandbox",hardQuota:"50 GB",hashScheme:"MD5"},{name:"analytics-warehouse",description:"Analytics data lake",hardQuota:"1 TB",hashScheme:"SHA-256"},{name:"backup-vault",description:"Encrypted backups",hardQuota:"2 TB",hashScheme:"SHA-512"},{name:"media-assets",description:"Images and videos",hardQuota:"200 GB",hashScheme:"SHA-256"},{name:"compliance-archive",description:"Regulatory compliance data",hardQuota:"500 GB",hashScheme:"SHA-256"},{name:"ml-training",description:"Machine learning datasets",hardQuota:"1 TB",hashScheme:"SHA-256"},{name:"logs-archive",description:"Centralized log storage",hardQuota:"300 GB",hashScheme:"MD5"},{name:"shared-assets",description:"Cross-team shared files",hardQuota:"100 GB",hashScheme:"SHA-256"}];let c=E(""),i=H(()=>t.filter(e=>e.name.toLowerCase().includes(s(c).toLowerCase()))),f=E(q([])),g=E(q({pageIndex:0,pageSize:25})),m=E(q({})),ee=H(()=>Object.keys(s(m)).filter(e=>s(m)[e]).map(e=>G.getCoreRowModel().rows[Number(e)]?.original.name).filter(Boolean)),I=H(()=>s(ee).length);const G=re({get data(){return s(i)},columns:[{id:"select",header:({table:e})=>M(W,{checked:e.getIsAllPageRowsSelected(),onCheckedChange:d=>e.toggleAllPageRowsSelected(!!d),"aria-label":"Select all rows"}),cell:({row:e})=>M(W,{checked:e.getIsSelected(),onCheckedChange:d=>e.toggleSelected(!!d),"aria-label":`Select ${e.original.name}`}),meta:{headerClass:"w-10 px-4 py-3",cellClass:"px-4 py-3"}},{accessorKey:"name",header:({column:e})=>M(X,{label:"Name",onclick:e.getToggleSortingHandler()}),meta:{cellClass:"px-4 py-3 font-medium"}},{accessorKey:"description",header:({column:e})=>M(X,{label:"Description",onclick:e.getToggleSortingHandler()}),meta:{cellClass:"px-4 py-3 text-muted-foreground"}},{accessorKey:"hardQuota",header:"Hard Quota",meta:{cellClass:"px-4 py-3 text-muted-foreground"}},{id:"hashScheme",header:"Hash Scheme",cell:({row:e})=>e.original.hashScheme,meta:{cellClass:"px-4 py-3 text-muted-foreground"}}],state:{get sorting(){return s(f)},get pagination(){return s(g)},get rowSelection(){return s(m)}},onSortingChange:e=>{v(f,typeof e=="function"?e(s(f)):e,!0)},onPaginationChange:e=>{v(g,typeof e=="function"?e(s(g)):e,!0)},onRowSelectionChange:e=>{v(m,typeof e=="function"?e(s(m)):e,!0)},getCoreRowModel:he(),getSortedRowModel:de(),getPaginationRowModel:ie(),enableRowSelection:!0});var O=Be(),F=$(O),K=$(F);pe(K,{class:"absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"});var te=w(K,2);ue(te,{placeholder:"Search namespaces...",class:"pl-10","aria-label":"Search namespaces",get value(){return s(c)},set value(e){v(c,e,!0)}});var L=w(F,2);{var ae=e=>{var d=ve(),A=$(d),R=$(A),_=w(A,2);z(_,{variant:"destructive",size:"sm",children:(h,V)=>{var u=ge(),P=Q(u);me(P,{class:"h-3.5 w-3.5"}),p(h,u)},$$slots:{default:!0}});var C=w(_,2);z(C,{variant:"outline",size:"sm",children:(h,V)=>{var u=ye(),P=Q(u);we(P,{class:"h-3.5 w-3.5"}),p(h,u)},$$slots:{default:!0}});var y=w(C,2);z(y,{variant:"ghost",size:"sm",onclick:()=>v(m,{},!0),children:(h,V)=>{var u=U("Deselect All");p(h,u)},$$slots:{default:!0}}),Y(()=>J(R,`${s(I)??""} selected`)),p(e,d)};j(L,e=>{s(I)>0&&e(ae)})}var ne=w(L,2);{const e=A=>{var R=oe(),_=Q(R);{var C=y=>{var h=U();Y(()=>J(h,`${s(I)??""} of ${s(i).length??""} row(s) selected.`)),p(y,h)};j(_,y=>{s(I)>0&&y(C)})}p(A,R)};let d=H(()=>`No results matching "${s(c)}"`);le(ne,{get table(){return G},get noResultsMessage(){return s(d)},footer:e,$$slots:{footer:!0}})}p(o,O),ce()}Z.__docgen={data:[],name:"data-table-test-harness.svelte"};const{expect:n,userEvent:r,within:l}=__STORYBOOK_MODULE_TEST__,qe={title:"Tests/DataTable Interactions",component:Z,tags:["!autodocs"]},B={play:async({canvasElement:o})=>{const a=l(o),t=a.getAllByRole("row");await n(t.length).toBe(11),await n(a.getByText("production-data")).toBeInTheDocument(),await n(a.getByText("ml-training")).toBeInTheDocument(),await n(a.getByText("shared-assets")).toBeInTheDocument()}},x={play:async({canvasElement:o})=>{const a=l(o),t=a.getByPlaceholderText("Search namespaces...");await r.clear(t),await r.type(t,"prod"),await n(a.getByText("production-data")).toBeInTheDocument(),await n(a.queryByText("staging-env")).not.toBeInTheDocument(),await n(a.queryByText("dev-sandbox")).not.toBeInTheDocument(),await r.clear(t),await r.type(t,"backup"),await n(a.getByText("backup-vault")).toBeInTheDocument(),await n(a.queryByText("production-data")).not.toBeInTheDocument(),await r.clear(t);const c=a.getAllByRole("row");await n(c.length).toBe(11)}},T={play:async({canvasElement:o})=>{const a=l(o),t=a.getByPlaceholderText("Search namespaces...");await r.clear(t),await r.type(t,"zzz-nonexistent"),await n(a.getByText(/No results matching/)).toBeInTheDocument(),await r.clear(t)}},k={play:async({canvasElement:o})=>{const a=r.setup({pointerEventsCheck:0}),t=l(o),c=t.getAllByRole("checkbox");await a.click(c[1]),await n(t.getByText("1 selected")).toBeInTheDocument(),await a.click(c[2]),await n(t.getByText("2 selected")).toBeInTheDocument();const i=t.getByText("Deselect All");await a.click(i),await n(t.queryByText("Deselect All")).not.toBeInTheDocument()}},D={play:async({canvasElement:o})=>{const a=r.setup({pointerEventsCheck:0}),t=l(o),c=t.getAllByRole("checkbox");await a.click(c[0]),await n(t.getByText("10 selected")).toBeInTheDocument(),await a.click(c[0]),await n(t.queryByText("Deselect All")).not.toBeInTheDocument()}},b={play:async({canvasElement:o})=>{const a=l(o),t=a.getByRole("button",{name:/Name/});await r.click(t);const i=a.getAllByRole("row")[1];await n(l(i).getByText("analytics-warehouse")).toBeInTheDocument(),await r.click(t);const g=a.getAllByRole("row")[1];await n(l(g).getByText("staging-env")).toBeInTheDocument(),await r.click(t)}},S={play:async({canvasElement:o})=>{const a=r.setup({pointerEventsCheck:0}),t=l(o),c=t.getAllByRole("checkbox");await n(t.queryByText("Delete Selected")).not.toBeInTheDocument(),await a.click(c[1]),await a.click(c[2]),await a.click(c[3]),await n(t.getByText("3 selected")).toBeInTheDocument(),await n(t.getByText("Delete Selected")).toBeInTheDocument(),await n(t.getByText("Grant Access")).toBeInTheDocument(),await n(t.getByText("Deselect All")).toBeInTheDocument();const i=t.getByText("Deselect All");await a.click(i)}};B.parameters={...B.parameters,docs:{...B.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);

    // 10 mock namespaces should produce 10 data rows
    const rows = canvas.getAllByRole("row");
    // 1 header row + 10 data rows = 11
    await expect(rows.length).toBe(11);

    // Check specific namespaces are visible
    await expect(canvas.getByText("production-data")).toBeInTheDocument();
    await expect(canvas.getByText("ml-training")).toBeInTheDocument();
    await expect(canvas.getByText("shared-assets")).toBeInTheDocument();
  }
}`,...B.parameters?.docs?.source},description:{story:"Verify the table renders all rows.",...B.parameters?.docs?.description}}};x.parameters={...x.parameters,docs:{...x.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const searchInput = canvas.getByPlaceholderText("Search namespaces...");

    // Type "prod" — should filter to 1 result
    await userEvent.clear(searchInput);
    await userEvent.type(searchInput, "prod");
    await expect(canvas.getByText("production-data")).toBeInTheDocument();
    await expect(canvas.queryByText("staging-env")).not.toBeInTheDocument();
    await expect(canvas.queryByText("dev-sandbox")).not.toBeInTheDocument();

    // Clear and type "backup"
    await userEvent.clear(searchInput);
    await userEvent.type(searchInput, "backup");
    await expect(canvas.getByText("backup-vault")).toBeInTheDocument();
    await expect(canvas.queryByText("production-data")).not.toBeInTheDocument();

    // Clear search — all rows should return
    await userEvent.clear(searchInput);
    const rows = canvas.getAllByRole("row");
    await expect(rows.length).toBe(11);
  }
}`,...x.parameters?.docs?.source},description:{story:"Type in the search box and verify filtering works.",...x.parameters?.docs?.description}}};T.parameters={...T.parameters,docs:{...T.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const searchInput = canvas.getByPlaceholderText("Search namespaces...");
    await userEvent.clear(searchInput);
    await userEvent.type(searchInput, "zzz-nonexistent");
    await expect(canvas.getByText(/No results matching/)).toBeInTheDocument();

    // Clean up
    await userEvent.clear(searchInput);
  }
}`,...T.parameters?.docs?.source},description:{story:'Verify "no results" message when search matches nothing.',...T.parameters?.docs?.description}}};k.parameters={...k.parameters,docs:{...k.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const user = userEvent.setup({
      pointerEventsCheck: 0
    });
    const canvas = within(canvasElement);
    const checkboxes = canvas.getAllByRole("checkbox");

    // First checkbox is "select all", rest are row checkboxes
    // Click first row checkbox (index 1)
    await user.click(checkboxes[1]);

    // Selection bar should appear — use exact text to avoid matching footer
    await expect(canvas.getByText("1 selected")).toBeInTheDocument();

    // Click second row checkbox
    await user.click(checkboxes[2]);
    await expect(canvas.getByText("2 selected")).toBeInTheDocument();

    // Click "Deselect All"
    const deselectBtn = canvas.getByText("Deselect All");
    await user.click(deselectBtn);

    // Selection bar should disappear
    await expect(canvas.queryByText("Deselect All")).not.toBeInTheDocument();
  }
}`,...k.parameters?.docs?.source},description:{story:"Select individual rows via checkboxes, verify selection bar appears.",...k.parameters?.docs?.description}}};D.parameters={...D.parameters,docs:{...D.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const user = userEvent.setup({
      pointerEventsCheck: 0
    });
    const canvas = within(canvasElement);
    const checkboxes = canvas.getAllByRole("checkbox");

    // First checkbox is "select all"
    await user.click(checkboxes[0]);

    // Should show "10 selected" in the bar
    await expect(canvas.getByText("10 selected")).toBeInTheDocument();

    // Deselect all
    await user.click(checkboxes[0]);
    await expect(canvas.queryByText("Deselect All")).not.toBeInTheDocument();
  }
}`,...D.parameters?.docs?.source},description:{story:'Click "select all" checkbox, verify all rows selected.',...D.parameters?.docs?.description}}};b.parameters={...b.parameters,docs:{...b.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);

    // Find the "Name" sort button
    const nameHeader = canvas.getByRole("button", {
      name: /Name/
    });
    await userEvent.click(nameHeader);

    // After ascending sort, first data row should be alphabetically first
    const rows = canvas.getAllByRole("row");
    // Row 0 is header, row 1 is first data row
    const firstDataRow = rows[1];
    await expect(within(firstDataRow).getByText("analytics-warehouse")).toBeInTheDocument();

    // Click again for descending
    await userEvent.click(nameHeader);
    const rowsDesc = canvas.getAllByRole("row");
    const firstDataRowDesc = rowsDesc[1];
    await expect(within(firstDataRowDesc).getByText("staging-env")).toBeInTheDocument();

    // Click again to clear sort
    await userEvent.click(nameHeader);
  }
}`,...b.parameters?.docs?.source},description:{story:"Verify sortable column headers work (click Name header to sort).",...b.parameters?.docs?.description}}};S.parameters={...S.parameters,docs:{...S.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const user = userEvent.setup({
      pointerEventsCheck: 0
    });
    const canvas = within(canvasElement);
    const checkboxes = canvas.getAllByRole("checkbox");

    // No bulk bar initially
    await expect(canvas.queryByText("Delete Selected")).not.toBeInTheDocument();

    // Select 3 rows
    await user.click(checkboxes[1]);
    await user.click(checkboxes[2]);
    await user.click(checkboxes[3]);

    // Bulk bar should show with correct count and all action buttons
    await expect(canvas.getByText("3 selected")).toBeInTheDocument();
    await expect(canvas.getByText("Delete Selected")).toBeInTheDocument();
    await expect(canvas.getByText("Grant Access")).toBeInTheDocument();
    await expect(canvas.getByText("Deselect All")).toBeInTheDocument();

    // Clean up
    const deselectBtn = canvas.getByText("Deselect All");
    await user.click(deselectBtn);
  }
}`,...S.parameters?.docs?.source},description:{story:"Verify bulk delete button appears when rows are selected.",...S.parameters?.docs?.description}}};const Qe=["RendersAllRows","SearchFiltering","SearchNoResults","RowSelection","SelectAll","ColumnSorting","BulkActionBar"];export{S as BulkActionBar,b as ColumnSorting,B as RendersAllRows,k as RowSelection,x as SearchFiltering,T as SearchNoResults,D as SelectAll,Qe as __namedExportsOrder,qe as default};
