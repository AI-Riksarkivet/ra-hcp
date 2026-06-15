import{i as e}from"./preload-helper-xPQekRTU.js";import{$ as t,H as n,Ht as r,It as i,Nt as a,Ot as o,Qt as s,Rt as c,St as l,Zt as ee,hn as u,ht as d,jt as f,kt as p,nt as m,on as h,rt as g,sn as _,st as v,t as y,tt as b,vn as x}from"./client-DASBvjj6.js";import{O as S,b as te,t as C}from"./lucide-svelte-C1WN62Nk.js";import{s as ne}from"./users-Dot7R9NU.js";import{n as w,t as T}from"./button-C86ki4bN.js";import{n as E,t as D}from"./input-BDV8AcLC.js";import{c as re,d as O,g as k,h as ie,i as ae,m as A,n as j,o as oe,p as M,r as N,s as P,t as F}from"./data-table-CigOhQsQ.js";function I(e,u){s(u,!0);let g=[{name:`production-data`,description:`Main production namespace`,hardQuota:`500 GB`,hashScheme:`SHA-256`},{name:`staging-env`,description:`Staging environment`,hardQuota:`100 GB`,hashScheme:`SHA-256`},{name:`dev-sandbox`,description:`Developer sandbox`,hardQuota:`50 GB`,hashScheme:`MD5`},{name:`analytics-warehouse`,description:`Analytics data lake`,hardQuota:`1 TB`,hashScheme:`SHA-256`},{name:`backup-vault`,description:`Encrypted backups`,hardQuota:`2 TB`,hashScheme:`SHA-512`},{name:`media-assets`,description:`Images and videos`,hardQuota:`200 GB`,hashScheme:`SHA-256`},{name:`compliance-archive`,description:`Regulatory compliance data`,hardQuota:`500 GB`,hashScheme:`SHA-256`},{name:`ml-training`,description:`Machine learning datasets`,hardQuota:`1 TB`,hashScheme:`SHA-256`},{name:`logs-archive`,description:`Centralized log storage`,hardQuota:`300 GB`,hashScheme:`MD5`},{name:`shared-assets`,description:`Cross-team shared files`,hardQuota:`100 GB`,hashScheme:`SHA-256`}],y=c(``),x=r(()=>g.filter(e=>e.name.toLowerCase().includes(d(y).toLowerCase()))),C=c(a([])),T=c(a({pageIndex:0,pageSize:25})),D=c(a({})),k=r(()=>Object.keys(d(D)).filter(e=>d(D)[e]).map(e=>N.getCoreRowModel().rows[Number(e)]?.original.name).filter(Boolean)),A=r(()=>d(k).length),N=ae({get data(){return d(x)},columns:[{id:`select`,header:({table:e})=>O(M,{checked:e.getIsAllPageRowsSelected(),onCheckedChange:t=>e.toggleAllPageRowsSelected(!!t),"aria-label":`Select all rows`}),cell:({row:e})=>O(M,{checked:e.getIsSelected(),onCheckedChange:t=>e.toggleSelected(!!t),"aria-label":`Select ${e.original.name}`}),meta:{headerClass:`w-10 px-4 py-3`,cellClass:`px-4 py-3`}},{accessorKey:`name`,header:({column:e})=>O(j,{label:`Name`,onclick:e.getToggleSortingHandler()}),meta:{cellClass:`px-4 py-3 font-medium`}},{accessorKey:`description`,header:({column:e})=>O(j,{label:`Description`,onclick:e.getToggleSortingHandler()}),meta:{cellClass:`px-4 py-3 text-muted-foreground`}},{accessorKey:`hardQuota`,header:`Hard Quota`,meta:{cellClass:`px-4 py-3 text-muted-foreground`}},{id:`hashScheme`,header:`Hash Scheme`,cell:({row:e})=>e.original.hashScheme,meta:{cellClass:`px-4 py-3 text-muted-foreground`}}],state:{get sorting(){return d(C)},get pagination(){return d(T)},get rowSelection(){return d(D)}},onSortingChange:e=>{i(C,typeof e==`function`?e(d(C)):e,!0)},onPaginationChange:e=>{i(T,typeof e==`function`?e(d(T)):e,!0)},onRowSelectionChange:e=>{i(D,typeof e==`function`?e(d(D)):e,!0)},getCoreRowModel:oe(),getSortedRowModel:re(),getPaginationRowModel:P(),enableRowSelection:!0});var F=B(),I=o(F),V=o(I);S(V,{class:`absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground`}),E(f(V,2),{placeholder:`Search namespaces...`,class:`pl-10`,"aria-label":`Search namespaces`,get value(){return d(y)},set value(e){i(y,e,!0)}}),_(I);var H=f(I,2),U=e=>{var n=z(),r=o(n),a=o(r);_(r);var s=f(r,2);w(s,{variant:`destructive`,size:`sm`,children:(e,t)=>{var n=L();te(p(n),{class:`h-3.5 w-3.5`}),h(),b(e,n)},$$slots:{default:!0}});var c=f(s,2);w(c,{variant:`outline`,size:`sm`,children:(e,t)=>{var n=R();ne(p(n),{class:`h-3.5 w-3.5`}),h(),b(e,n)},$$slots:{default:!0}}),w(f(c,2),{variant:`ghost`,size:`sm`,onclick:()=>i(D,{},!0),children:(e,t)=>{h(),b(e,v(`Deselect All`))},$$slots:{default:!0}}),_(n),l(()=>t(a,`${d(A)??``} selected`)),b(e,n)};n(H,e=>{d(A)>0&&e(U)});var W=f(H,2);{let e=e=>{var r=m(),i=p(r),a=e=>{var n=v();l(()=>t(n,`${d(A)??``} of ${d(x).length??``} row(s) selected.`)),b(e,n)};n(i,e=>{d(A)>0&&e(a)}),b(e,r)},i=r(()=>`No results matching "${d(y)}"`);ie(W,{get table(){return N},get noResultsMessage(){return d(i)},footer:e,$$slots:{footer:!0}})}_(F),b(e,F),ee()}var L,R,z,B,V=e((()=>{x(),u(),y(),C(),F(),k(),N(),A(),T(),D(),L=g(`<!>Delete Selected`,1),R=g(`<!>Grant Access`,1),z=g(`<div class="flex items-center gap-3 rounded-lg border bg-muted/50 px-4 py-2"><span class="text-sm font-medium"> </span> <!> <!> <!></div>`),B=g(`<div class="space-y-3"><div class="relative max-w-md"><!> <!></div> <!> <!></div>`),I.__docgen={data:[],name:`data-table-test-harness.svelte`}})),H,U,W,G,K,q,J,Y,X,Z,Q,$;e((()=>{V(),{expect:H,userEvent:U,within:W}=__STORYBOOK_MODULE_TEST__,G={title:`Tests/DataTable Interactions`,component:I,tags:[`!autodocs`]},K={play:async({canvasElement:e})=>{let t=W(e);await H(t.getAllByRole(`row`).length).toBe(11),await H(t.getByText(`production-data`)).toBeInTheDocument(),await H(t.getByText(`ml-training`)).toBeInTheDocument(),await H(t.getByText(`shared-assets`)).toBeInTheDocument()}},q={play:async({canvasElement:e})=>{let t=W(e),n=t.getByPlaceholderText(`Search namespaces...`);await U.clear(n),await U.type(n,`prod`),await H(t.getByText(`production-data`)).toBeInTheDocument(),await H(t.queryByText(`staging-env`)).not.toBeInTheDocument(),await H(t.queryByText(`dev-sandbox`)).not.toBeInTheDocument(),await U.clear(n),await U.type(n,`backup`),await H(t.getByText(`backup-vault`)).toBeInTheDocument(),await H(t.queryByText(`production-data`)).not.toBeInTheDocument(),await U.clear(n),await H(t.getAllByRole(`row`).length).toBe(11)}},J={play:async({canvasElement:e})=>{let t=W(e),n=t.getByPlaceholderText(`Search namespaces...`);await U.clear(n),await U.type(n,`zzz-nonexistent`),await H(t.getByText(/No results matching/)).toBeInTheDocument(),await U.clear(n)}},Y={play:async({canvasElement:e})=>{let t=U.setup({pointerEventsCheck:0}),n=W(e),r=n.getAllByRole(`checkbox`);await t.click(r[1]),await H(n.getByText(`1 selected`)).toBeInTheDocument(),await t.click(r[2]),await H(n.getByText(`2 selected`)).toBeInTheDocument();let i=n.getByText(`Deselect All`);await t.click(i),await H(n.queryByText(`Deselect All`)).not.toBeInTheDocument()}},X={play:async({canvasElement:e})=>{let t=U.setup({pointerEventsCheck:0}),n=W(e),r=n.getAllByRole(`checkbox`);await t.click(r[0]),await H(n.getByText(`10 selected`)).toBeInTheDocument(),await t.click(r[0]),await H(n.queryByText(`Deselect All`)).not.toBeInTheDocument()}},Z={play:async({canvasElement:e})=>{let t=W(e),n=t.getByRole(`button`,{name:/Name/});await U.click(n);let r=t.getAllByRole(`row`)[1];await H(W(r).getByText(`analytics-warehouse`)).toBeInTheDocument(),await U.click(n);let i=t.getAllByRole(`row`)[1];await H(W(i).getByText(`staging-env`)).toBeInTheDocument(),await U.click(n)}},Q={play:async({canvasElement:e})=>{let t=U.setup({pointerEventsCheck:0}),n=W(e),r=n.getAllByRole(`checkbox`);await H(n.queryByText(`Delete Selected`)).not.toBeInTheDocument(),await t.click(r[1]),await t.click(r[2]),await t.click(r[3]),await H(n.getByText(`3 selected`)).toBeInTheDocument(),await H(n.getByText(`Delete Selected`)).toBeInTheDocument(),await H(n.getByText(`Grant Access`)).toBeInTheDocument(),await H(n.getByText(`Deselect All`)).toBeInTheDocument();let i=n.getByText(`Deselect All`);await t.click(i)}},K.parameters={...K.parameters,docs:{...K.parameters?.docs,source:{originalSource:`{
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
}`,...K.parameters?.docs?.source},description:{story:`Verify the table renders all rows.`,...K.parameters?.docs?.description}}},q.parameters={...q.parameters,docs:{...q.parameters?.docs,source:{originalSource:`{
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
}`,...q.parameters?.docs?.source},description:{story:`Type in the search box and verify filtering works.`,...q.parameters?.docs?.description}}},J.parameters={...J.parameters,docs:{...J.parameters?.docs,source:{originalSource:`{
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
}`,...J.parameters?.docs?.source},description:{story:`Verify "no results" message when search matches nothing.`,...J.parameters?.docs?.description}}},Y.parameters={...Y.parameters,docs:{...Y.parameters?.docs,source:{originalSource:`{
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
}`,...Y.parameters?.docs?.source},description:{story:`Select individual rows via checkboxes, verify selection bar appears.`,...Y.parameters?.docs?.description}}},X.parameters={...X.parameters,docs:{...X.parameters?.docs,source:{originalSource:`{
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
}`,...X.parameters?.docs?.source},description:{story:`Click "select all" checkbox, verify all rows selected.`,...X.parameters?.docs?.description}}},Z.parameters={...Z.parameters,docs:{...Z.parameters?.docs,source:{originalSource:`{
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
}`,...Z.parameters?.docs?.source},description:{story:`Verify sortable column headers work (click Name header to sort).`,...Z.parameters?.docs?.description}}},Q.parameters={...Q.parameters,docs:{...Q.parameters?.docs,source:{originalSource:`{
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
}`,...Q.parameters?.docs?.source},description:{story:`Verify bulk delete button appears when rows are selected.`,...Q.parameters?.docs?.description}}},$=[`RendersAllRows`,`SearchFiltering`,`SearchNoResults`,`RowSelection`,`SelectAll`,`ColumnSorting`,`BulkActionBar`]}))();export{Q as BulkActionBar,Z as ColumnSorting,K as RendersAllRows,Y as RowSelection,q as SearchFiltering,J as SearchNoResults,X as SelectAll,$ as __namedExportsOrder,G as default};