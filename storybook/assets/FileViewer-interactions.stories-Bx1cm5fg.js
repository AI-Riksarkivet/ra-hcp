import{i as e}from"./preload-helper-xPQekRTU.js";import{$ as t,H as n,Ht as r,It as i,N as a,Ot as o,Rt as s,St as c,ct as l,hn as u,ht as d,jt as f,kt as p,lt as m,nt as h,rt as g,sn as _,t as v,tt as y,vn as b,zt as x}from"./client-DASBvjj6.js";import{n as S,t as C}from"./iframe-CEOTwOQE.js";import{n as w,t as T}from"./FileViewer-B1QpRQBg.js";function E(e){let l=s(!0),u=s(0),g=[{filename:`photo-001.jpg`,url:`https://placehold.co/400x300/1a1a2e/eee?text=Photo+001`,size:245760,objectKey:`photos/photo-001.jpg`,lastModified:`2024-11-15T10:30:00Z`,etag:`"abc123"`,storageClass:`STANDARD`},{filename:`photo-002.png`,url:`https://placehold.co/400x300/2d3436/dfe6e9?text=Photo+002`,size:512e3,objectKey:`photos/photo-002.png`,lastModified:`2024-11-16T14:00:00Z`,etag:`"def456"`,storageClass:`STANDARD`},{filename:`data-export.parquet`,url:`#`,size:52428800,objectKey:`exports/data-export.parquet`,lastModified:`2024-12-01T08:00:00Z`,storageClass:`GLACIER`}],v=r(()=>g[d(u)]);function b(){d(u)>0&&x(u,-1)}function C(){d(u)<g.length-1&&x(u)}var w=h();a(p(w),()=>S,(e,a)=>{a(e,{children:(e,a)=>{var s=O(),p=o(s),h=e=>{var t=D();m(`click`,t,()=>i(l,!0)),y(e,t)};n(p,e=>{d(l)||e(h)});var x=f(p,2),S=o(x,!0);_(x);var w=f(x,2);{let e=r(()=>d(u)>0),t=r(()=>d(u)<g.length-1);T(w,{get filename(){return d(v).filename},get url(){return d(v).url},get size(){return d(v).size},get objectKey(){return d(v).objectKey},get lastModified(){return d(v).lastModified},get etag(){return d(v).etag},get storageClass(){return d(v).storageClass},get hasPrev(){return d(e)},get hasNext(){return d(t)},onprev:b,onnext:C,onclose:()=>i(l,!1),get currentIndex(){return d(u)},get totalCount(){return g.length},get open(){return d(l)},set open(e){i(l,e,!0)}})}_(s),c(()=>t(S,d(v).filename)),y(e,s)},$$slots:{default:!0}})}),y(e,w)}var D,O,k=e((()=>{b(),u(),v(),w(),C(),D=g(`<button data-testid="reopen-btn">Reopen</button>`),O=g(`<div class="p-4"><!> <div data-testid="current-file" class="text-xs text-muted-foreground"> </div> <!></div>`),l([`click`]),E.__docgen={data:[],name:`FileViewer-test-harness.svelte`}}));function A(){return N(document.body)}var j,M,N,P,F,I,L,R,z,B;e((()=>{k(),{expect:j,userEvent:M,within:N}=__STORYBOOK_MODULE_TEST__,P={title:`Tests/FileViewer Interactions`,component:E,tags:[`!autodocs`]},F={play:async()=>{let e=A();await j(await e.findByRole(`heading`,{name:`photo-001.jpg`})).toBeInTheDocument(),await j(await e.findByText(`1 of 3`)).toBeInTheDocument(),await j(await e.findByText(`240.0 KB`)).toBeInTheDocument(),await j(await e.findByText(`STANDARD`)).toBeInTheDocument()}},I={play:async({canvasElement:e})=>{let t=A(),n=N(e),r=await t.findByRole(`button`,{name:`Next file`});await M.click(r),await j(await t.findByRole(`heading`,{name:`photo-002.png`})).toBeInTheDocument(),await j(await t.findByText(`2 of 3`)).toBeInTheDocument(),await j(n.getByTestId(`current-file`)).toHaveTextContent(`photo-002.png`)}},L={play:async()=>{let e=A(),t=await e.findByRole(`button`,{name:`Next file`});await M.click(t),await M.click(t),await j(await e.findByRole(`heading`,{name:`data-export.parquet`})).toBeInTheDocument(),await j(await e.findByText(/Preview not available/)).toBeInTheDocument(),await j(await e.findByText(`3 of 3`)).toBeInTheDocument()}},R={play:async()=>{let e=A();await j(await e.findByText(`Details`)).toBeInTheDocument(),await j(await e.findByText(`photos/photo-001.jpg`)).toBeInTheDocument();let t=await e.findByRole(`button`,{name:`Toggle metadata`});await M.click(t),await j(e.queryByText(`Details`)).not.toBeInTheDocument(),await M.click(t),await j(await e.findByText(`Details`)).toBeInTheDocument()}},z={play:async({canvasElement:e})=>{let t=A(),n=N(e);await j(await t.findByRole(`heading`,{name:`photo-001.jpg`})).toBeInTheDocument();let r=await t.findByRole(`button`,{name:`Close`});await M.click(r),await j(await n.findByTestId(`reopen-btn`)).toBeInTheDocument()}},F.parameters={...F.parameters,docs:{...F.parameters?.docs,source:{originalSource:`{
  play: async () => {
    const page = getPage();

    // Use heading role to target the dialog title (not the harness data-testid div)
    await expect(await page.findByRole("heading", {
      name: "photo-001.jpg"
    })).toBeInTheDocument();
    await expect(await page.findByText("1 of 3")).toBeInTheDocument();
    await expect(await page.findByText("240.0 KB")).toBeInTheDocument();
    await expect(await page.findByText("STANDARD")).toBeInTheDocument();
  }
}`,...F.parameters?.docs?.source},description:{story:`Verify the viewer opens with the first file's details.`,...F.parameters?.docs?.description}}},I.parameters={...I.parameters,docs:{...I.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const page = getPage();
    const canvas = within(canvasElement);

    // Click "Next file" button
    const nextBtn = await page.findByRole("button", {
      name: "Next file"
    });
    await userEvent.click(nextBtn);

    // Should now show second file
    await expect(await page.findByRole("heading", {
      name: "photo-002.png"
    })).toBeInTheDocument();
    await expect(await page.findByText("2 of 3")).toBeInTheDocument();

    // Verify the harness state also updated
    await expect(canvas.getByTestId("current-file")).toHaveTextContent("photo-002.png");
  }
}`,...I.parameters?.docs?.source},description:{story:`Navigate forward to the next file.`,...I.parameters?.docs?.description}}},L.parameters={...L.parameters,docs:{...L.parameters?.docs,source:{originalSource:`{
  play: async () => {
    const page = getPage();

    // Navigate to third file (parquet — unsupported)
    const nextBtn = await page.findByRole("button", {
      name: "Next file"
    });
    await userEvent.click(nextBtn);
    await userEvent.click(nextBtn);
    await expect(await page.findByRole("heading", {
      name: "data-export.parquet"
    })).toBeInTheDocument();
    await expect(await page.findByText(/Preview not available/)).toBeInTheDocument();
    await expect(await page.findByText("3 of 3")).toBeInTheDocument();
  }
}`,...L.parameters?.docs?.source},description:{story:`Navigate to unsupported file type shows download prompt.`,...L.parameters?.docs?.description}}},R.parameters={...R.parameters,docs:{...R.parameters?.docs,source:{originalSource:`{
  play: async () => {
    const page = getPage();

    // Metadata should be visible initially (objectKey is set)
    await expect(await page.findByText("Details")).toBeInTheDocument();
    await expect(await page.findByText("photos/photo-001.jpg")).toBeInTheDocument();

    // Click the info toggle button
    const infoBtn = await page.findByRole("button", {
      name: "Toggle metadata"
    });
    await userEvent.click(infoBtn);

    // Details heading should be gone
    await expect(page.queryByText("Details")).not.toBeInTheDocument();

    // Toggle back
    await userEvent.click(infoBtn);
    await expect(await page.findByText("Details")).toBeInTheDocument();
  }
}`,...R.parameters?.docs?.source},description:{story:`Toggle metadata panel visibility.`,...R.parameters?.docs?.description}}},z.parameters={...z.parameters,docs:{...z.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const page = getPage();
    const canvas = within(canvasElement);

    // Verify dialog is open
    await expect(await page.findByRole("heading", {
      name: "photo-001.jpg"
    })).toBeInTheDocument();

    // Click close button
    const closeBtn = await page.findByRole("button", {
      name: "Close"
    });
    await userEvent.click(closeBtn);

    // Reopen button should appear in harness
    await expect(await canvas.findByTestId("reopen-btn")).toBeInTheDocument();
  }
}`,...z.parameters?.docs?.source},description:{story:`Close the viewer dialog.`,...z.parameters?.docs?.description}}},B=[`RendersFirstFile`,`NavigateNext`,`UnsupportedFileType`,`ToggleMetadata`,`CloseViewer`]}))();export{z as CloseViewer,I as NavigateNext,F as RendersFirstFile,R as ToggleMetadata,L as UnsupportedFileType,B as __namedExportsOrder,P as default};