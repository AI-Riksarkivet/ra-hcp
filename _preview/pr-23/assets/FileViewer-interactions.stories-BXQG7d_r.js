import{c as q,f as $,b as z,d as w,H as O,o as U,h as a,i as I,r as h,g as H,s as Z,k as b,E as L,u as B,j as k,q as _,M as R}from"./iframe-Bko5EKxf.js";import{F as G}from"./FileViewer-B3NrQRJI.js";import{T as Y}from"./tooltip-provider-ClMs9gNk.js";import"./preload-helper-FELLgOHk.js";import"./this-BsXXU8aY.js";import"./cn-_yov3II5.js";import"./dialog-description-D5sJVh7W.js";import"./scroll-lock-C24tszpE.js";import"./is-URtbfbCP.js";import"./create-id--OBs3Sml.js";import"./dialog-description-Bj7fRn2W.js";import"./x-BPmqx3Ww.js";import"./legacy-Cs_nBadi.js";import"./Icon-XojSPnKq.js";import"./each-Rgc3mc9m.js";import"./button-J7gse9ZS.js";import"./index-DW9qdgWl.js";import"./badge-Cl061XlS.js";import"./chevron-right-DCOsVW06.js";import"./info-BM6xr0gM.js";import"./loader-circle-DYEG2CY8.js";import"./popper-layer-force-mount-C2Wn9W2o.js";var J=k('<button data-testid="reopen-btn">Reopen</button>'),Q=k('<div class="p-4"><!> <div data-testid="current-file" class="text-xs text-muted-foreground"> </div> <!></div>');function C(e){let t=_(!0),o=_(0);const i=[{filename:"photo-001.jpg",url:"https://placehold.co/400x300/1a1a2e/eee?text=Photo+001",size:245760,objectKey:"photos/photo-001.jpg",lastModified:"2024-11-15T10:30:00Z",etag:'"abc123"',storageClass:"STANDARD"},{filename:"photo-002.png",url:"https://placehold.co/400x300/2d3436/dfe6e9?text=Photo+002",size:512e3,objectKey:"photos/photo-002.png",lastModified:"2024-11-16T14:00:00Z",etag:'"def456"',storageClass:"STANDARD"},{filename:"data-export.parquet",url:"#",size:52428800,objectKey:"exports/data-export.parquet",lastModified:"2024-12-01T08:00:00Z",storageClass:"GLACIER"}];let s=B(()=>i[a(o)]);function N(){a(o)>0&&R(o,-1)}function E(){a(o)<i.length-1&&R(o)}var T=q(),j=$(T);z(j,()=>Y,(P,S)=>{S(P,{children:(F,W)=>{var x=Q(),v=b(x);{var M=c=>{var f=J();L("click",f,()=>h(t,!0)),w(c,f)};U(v,c=>{a(t)||c(M)})}var D=I(v,2),A=b(D),K=I(D,2);{let c=B(()=>a(o)>0),f=B(()=>a(o)<i.length-1);G(K,{get filename(){return a(s).filename},get url(){return a(s).url},get size(){return a(s).size},get objectKey(){return a(s).objectKey},get lastModified(){return a(s).lastModified},get etag(){return a(s).etag},get storageClass(){return a(s).storageClass},get hasPrev(){return a(c)},get hasNext(){return a(f)},onprev:N,onnext:E,onclose:()=>h(t,!1),get currentIndex(){return a(o)},get totalCount(){return i.length},get open(){return a(t)},set open(V){h(t,V,!0)}})}H(()=>Z(A,a(s).filename)),w(F,x)},$$slots:{default:!0}})}),w(e,T)}O(["click"]);C.__docgen={data:[],name:"FileViewer-test-harness.svelte"};const{expect:n,userEvent:r,within:y}=__STORYBOOK_MODULE_TEST__,xe={title:"Tests/FileViewer Interactions",component:C,tags:["!autodocs"]};function m(){return y(document.body)}const p={play:async()=>{const e=m();await n(await e.findByRole("heading",{name:"photo-001.jpg"})).toBeInTheDocument(),await n(await e.findByText("1 of 3")).toBeInTheDocument(),await n(await e.findByText("240.0 KB")).toBeInTheDocument(),await n(await e.findByText("STANDARD")).toBeInTheDocument()}},l={play:async({canvasElement:e})=>{const t=m(),o=y(e),i=await t.findByRole("button",{name:"Next file"});await r.click(i),await n(await t.findByRole("heading",{name:"photo-002.png"})).toBeInTheDocument(),await n(await t.findByText("2 of 3")).toBeInTheDocument(),await n(o.getByTestId("current-file")).toHaveTextContent("photo-002.png")}},d={play:async()=>{const e=m(),t=await e.findByRole("button",{name:"Next file"});await r.click(t),await r.click(t),await n(await e.findByRole("heading",{name:"data-export.parquet"})).toBeInTheDocument(),await n(await e.findByText(/Preview not available/)).toBeInTheDocument(),await n(await e.findByText("3 of 3")).toBeInTheDocument()}},g={play:async()=>{const e=m();await n(await e.findByText("Details")).toBeInTheDocument(),await n(await e.findByText("photos/photo-001.jpg")).toBeInTheDocument();const t=await e.findByRole("button",{name:"Toggle metadata"});await r.click(t),await n(e.queryByText("Details")).not.toBeInTheDocument(),await r.click(t),await n(await e.findByText("Details")).toBeInTheDocument()}},u={play:async({canvasElement:e})=>{const t=m(),o=y(e);await n(await t.findByRole("heading",{name:"photo-001.jpg"})).toBeInTheDocument();const i=await t.findByRole("button",{name:"Close"});await r.click(i),await n(await o.findByTestId("reopen-btn")).toBeInTheDocument()}};p.parameters={...p.parameters,docs:{...p.parameters?.docs,source:{originalSource:`{
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
}`,...p.parameters?.docs?.source},description:{story:"Verify the viewer opens with the first file's details.",...p.parameters?.docs?.description}}};l.parameters={...l.parameters,docs:{...l.parameters?.docs,source:{originalSource:`{
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
}`,...l.parameters?.docs?.source},description:{story:"Navigate forward to the next file.",...l.parameters?.docs?.description}}};d.parameters={...d.parameters,docs:{...d.parameters?.docs,source:{originalSource:`{
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
}`,...d.parameters?.docs?.source},description:{story:"Navigate to unsupported file type shows download prompt.",...d.parameters?.docs?.description}}};g.parameters={...g.parameters,docs:{...g.parameters?.docs,source:{originalSource:`{
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
}`,...g.parameters?.docs?.source},description:{story:"Toggle metadata panel visibility.",...g.parameters?.docs?.description}}};u.parameters={...u.parameters,docs:{...u.parameters?.docs,source:{originalSource:`{
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
}`,...u.parameters?.docs?.source},description:{story:"Close the viewer dialog.",...u.parameters?.docs?.description}}};const ve=["RendersFirstFile","NavigateNext","UnsupportedFileType","ToggleMetadata","CloseViewer"];export{u as CloseViewer,l as NavigateNext,p as RendersFirstFile,g as ToggleMetadata,d as UnsupportedFileType,ve as __namedExportsOrder,xe as default};
