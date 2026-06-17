import{i as e}from"./preload-helper-xPQekRTU.js";import{H as t,It as n,Ot as r,Qt as i,Rt as a,Zt as o,a as s,hn as c,ht as l,jt as u,kt as d,o as f,rt as p,sn as m,t as h,tt as g,vn as _}from"./client-DASBvjj6.js";import{B as v,Pt as y,X as b,c as x,i as S,n as C,nt as w,o as T,p as E,v as D}from"./lucide-svelte-M3lzhF2e.js";import{n as O,t as k}from"./cors-editor-QTkjroW-.js";import{n as A,t as j}from"./dist-D-dHTnUt.js";import{i as M,t as N}from"./dist-AqWqpq32.js";function P(e,t){i(t,!0);let n=s(t,F);A(e,f({get theme(){return M.current},class:`toaster group`,style:`--normal-bg: var(--color-popover); --normal-text: var(--color-popover-foreground); --normal-border: var(--color-border);`},()=>n,{loadingIcon:e=>{b(e,{class:`size-4 animate-spin`})},successIcon:e=>{y(e,{class:`size-4`})},errorIcon:e=>{v(e,{class:`size-4`})},infoIcon:e=>{w(e,{class:`size-4`})},warningIcon:e=>{D(e,{class:`size-4`})},$$slots:{loadingIcon:!0,successIcon:!0,errorIcon:!0,infoIcon:!0,warningIcon:!0}})),o()}var F,I=e((()=>{_(),c(),h(),T(),x(),E(),S(),C(),j(),N(),F=new Set([`$$slots`,`$$events`,`$$legacy`]),P.__docgen={data:[{name:`invert`,visibility:`public`,description:`Dark toasts in light mode and vice versa.`,keywords:[],kind:`let`,type:{kind:`type`,type:`boolean`,text:`boolean`},static:!1,readonly:!1},{name:`theme`,visibility:`public`,description:`Toast's theme, either light, dark, or system.

If using [mode-watcher](https://mode-watcher.sveco.dev), you can set this to the
\`userPrefersMode.current\` to automatically switch themes based on those preferences.`,keywords:[],kind:`let`,type:{kind:`union`,type:[{kind:`const`,type:`string`,value:`light`,text:`"light"`},{kind:`const`,type:`string`,value:`dark`,text:`"dark"`},{kind:`const`,type:`string`,value:`system`,text:`"system"`}],text:`"light" | "dark" | "system"`},static:!1,readonly:!1},{name:`position`,visibility:`public`,description:`Place where the toasts will be rendered`,keywords:[],kind:`let`,type:{kind:`union`,type:[{kind:`const`,type:`string`,value:`top-left`,text:`"top-left"`},{kind:`const`,type:`string`,value:`top-right`,text:`"top-right"`},{kind:`const`,type:`string`,value:`bottom-left`,text:`"bottom-left"`},{kind:`const`,type:`string`,value:`bottom-right`,text:`"bottom-right"`},{kind:`const`,type:`string`,value:`top-center`,text:`"top-center"`},{kind:`const`,type:`string`,value:`bottom-center`,text:`"bottom-center"`}],text:`"top-left" | "top-right" | "bottom-left" | "bottom-right" | "top-center" | "bottom-center"`},static:!1,readonly:!1},{name:`hotkey`,visibility:`public`,description:`Keyboard shortcut that will move focus to the toaster area.`,keywords:[],kind:`let`,type:{kind:`type`,type:`array`,text:`string[]`},static:!1,readonly:!1},{name:`richColors`,visibility:`public`,description:`Makes error and success state more colorful`,keywords:[],kind:`let`,type:{kind:`type`,type:`boolean`,text:`boolean`},static:!1,readonly:!1},{name:`expand`,visibility:`public`,description:`Toasts will be expanded by default`,keywords:[],kind:`let`,type:{kind:`type`,type:`boolean`,text:`boolean`},static:!1,readonly:!1},{name:`duration`,visibility:`public`,description:`The duration of the toast in milliseconds.`,keywords:[],kind:`let`,type:{kind:`type`,type:`number`,text:`number`},static:!1,readonly:!1},{name:`gap`,visibility:`public`,description:`Gap between toasts when expanded, in pixels.`,keywords:[],kind:`let`,type:{kind:`type`,type:`number`,text:`number`},static:!1,readonly:!1},{name:`visibleToasts`,visibility:`public`,description:`Amount of visible toasts`,keywords:[],kind:`let`,type:{kind:`type`,type:`number`,text:`number`},static:!1,readonly:!1},{name:`closeButton`,visibility:`public`,description:`Adds a close button to all toasts, shows on hover`,keywords:[],kind:`let`,type:{kind:`type`,type:`boolean`,text:`boolean`},static:!1,readonly:!1},{name:`toastOptions`,visibility:`public`,description:`These will act as default options for all toasts.`,keywords:[],kind:`let`,type:{kind:`type`,type:`object`,text:`ToastOptions`},static:!1,readonly:!1},{name:`offset`,visibility:`public`,description:`Offset from the edges of the screen.`,keywords:[],kind:`let`,type:{kind:`union`,type:[{kind:`type`,type:`string`,text:`string`},{kind:`type`,type:`number`,text:`number`},{kind:`type`,type:`object`,text:`{ top?: string | number | undefined; right?: string | number | undefined; bottom?: string | number | undefined; left?: string | number | undefined; }`}],text:`string | number | { top?: string | number | undefined; right?: string | number | undefined; bottom?: string | number | undefined; left?: string | number | undefined; }`},static:!1,readonly:!1},{name:`mobileOffset`,visibility:`public`,description:`Offset from the edges of the screen for mobile devices.`,keywords:[],kind:`let`,type:{kind:`union`,type:[{kind:`type`,type:`string`,text:`string`},{kind:`type`,type:`number`,text:`number`},{kind:`type`,type:`object`,text:`{ top?: string | number | undefined; right?: string | number | undefined; bottom?: string | number | undefined; left?: string | number | undefined; }`}],text:`string | number | { top?: string | number | undefined; right?: string | number | undefined; bottom?: string | number | undefined; left?: string | number | undefined; }`},static:!1,readonly:!1},{name:`pauseWhenPageIsHidden`,visibility:`public`,description:`Pause the toast timer when the page is hidden, e.g. when the user switches
tabs. Toasts will not expire while the page is hidden.`,keywords:[],kind:`let`,type:{kind:`type`,type:`boolean`,text:`boolean`},static:!1,readonly:!1},{name:`dir`,visibility:`public`,description:`Directionality of toast's text`,keywords:[],kind:`let`,type:{kind:`union`,type:[{kind:`const`,type:`string`,value:`ltr`,text:`"ltr"`},{kind:`const`,type:`string`,value:`rtl`,text:`"rtl"`},{kind:`const`,type:`string`,value:`auto`,text:`"auto"`}],text:`"ltr" | "rtl" | "auto"`},static:!1,readonly:!1},{name:`swipeDirections`,visibility:`public`,description:`The directions in which the toast can be swiped.`,keywords:[],kind:`let`,type:{kind:`type`,type:`array`,text:`SwipeDirection[]`},static:!1,readonly:!1},{name:`containerAriaLabel`,visibility:`public`,description:`The aria-label to use for the container element, which will
be combined with the hotkey, if provided like so:

\`\`\`svelte
<section aria-label="{containerAriaLabel} {hotkeyLabel}"
</section>
\`\`\``,keywords:[],kind:`let`,type:{kind:`type`,type:`string`,text:`string`},static:!1,readonly:!1},{name:`closeButtonAriaLabel`,visibility:`public`,description:`The aria label for the close button.`,keywords:[],kind:`let`,type:{kind:`type`,type:`string`,text:`string`},static:!1,readonly:!1},{name:`successIcon`,visibility:`public`,description:"The icon to use for the success toast,\ncan be either a snippet, a component, or `null` to not render an icon.",keywords:[],kind:`let`,type:{kind:`function`,text:`Snippet<[]>`},static:!1,readonly:!1},{name:`infoIcon`,visibility:`public`,description:"The icon to use for the info toast,\ncan be either a snippet, a component, or `null` to not render an icon.",keywords:[],kind:`let`,type:{kind:`function`,text:`Snippet<[]>`},static:!1,readonly:!1},{name:`warningIcon`,visibility:`public`,description:"The icon to use for the warning toast,\ncan be either a snippet, a component, or `null` to not render an icon.",keywords:[],kind:`let`,type:{kind:`function`,text:`Snippet<[]>`},static:!1,readonly:!1},{name:`errorIcon`,visibility:`public`,description:"The icon to use for the error toast,\ncan be either a snippet, a component, or `null` to not render an icon.",keywords:[],kind:`let`,type:{kind:`function`,text:`Snippet<[]>`},static:!1,readonly:!1},{name:`loadingIcon`,visibility:`public`,description:"The icon to use for the loading toast,\ncan be either a snippet, a component, or `null` to not render an icon.",keywords:[],kind:`let`,type:{kind:`function`,text:`Snippet<[]>`},static:!1,readonly:!1},{name:`closeIcon`,visibility:`public`,description:"The icon to use for the close button,\ncan be either a snippet, a component, or `null` to not render an icon.",keywords:[],kind:`let`,type:{kind:`function`,text:`Snippet<[]>`},static:!1,readonly:!1}],name:`sonner.svelte`}})),L=e((()=>{I()}));function R(e,s){i(s,!0);let c=a(!1),f=a(!1);async function p(e){await new Promise(e=>setTimeout(e,100)),n(c,!0)}async function h(){await new Promise(e=>setTimeout(e,100)),n(f,!0)}var _=V(),v=d(_);P(v,{});var y=u(v,2),b=r(y);k(b,{corsXml:`<CORSConfiguration>
  <CORSRule>
    <AllowedOrigin>*</AllowedOrigin>
    <AllowedMethod>GET</AllowedMethod>
  </CORSRule>
</CORSConfiguration>`,onsave:p,ondelete:h});var x=u(b,2),S=e=>{g(e,z())};t(x,e=>{l(c)&&e(S)});var C=u(x,2),w=e=>{g(e,B())};t(C,e=>{l(f)&&e(w)}),m(y),g(e,_),o()}var z,B,V,H=e((()=>{_(),c(),h(),O(),L(),z=p(`<div data-testid="save-result" class="text-sm text-emerald-600">CORS saved</div>`),B=p(`<div data-testid="delete-result" class="text-sm text-destructive">CORS deleted</div>`),V=p(`<!> <div class="max-w-lg space-y-4 p-4"><!> <!> <!></div>`,1),R.__docgen={data:[],name:`cors-editor-test-harness.svelte`}})),U,W,G,K,q,J,Y,X;e((()=>{H(),{expect:U,userEvent:W,within:G}=__STORYBOOK_MODULE_TEST__,K={title:`Tests/CorsEditor Interactions`,component:R,tags:[`!autodocs`]},q={play:async({canvasElement:e})=>{let t=G(e);await U(t.getByText(`CORS Configuration`)).toBeInTheDocument(),await U(t.getByText(`Delete CORS`)).toBeInTheDocument(),await U(t.getByRole(`textbox`).value).toContain(`<CORSConfiguration>`)}},J={play:async({canvasElement:e})=>{let t=G(e),n=t.getByRole(`textbox`),r=t.getByRole(`button`,{name:/save/i});await U(r).toBeDisabled(),await W.type(n,`
<!-- modified -->`),await U(r).not.toBeDisabled()}},Y={play:async({canvasElement:e})=>{let t=G(e),n=t.getByRole(`textbox`);await W.type(n,`
<!-- saved -->`);let r=t.getByRole(`button`,{name:/save/i});await W.click(r),await U(await t.findByTestId(`save-result`)).toHaveTextContent(`CORS saved`)}},q.parameters={...q.parameters,docs:{...q.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText("CORS Configuration")).toBeInTheDocument();
    await expect(canvas.getByText("Delete CORS")).toBeInTheDocument();

    // The textarea should contain the initial XML
    const textarea = canvas.getByRole("textbox") as HTMLTextAreaElement;
    await expect(textarea.value).toContain("<CORSConfiguration>");
  }
}`,...q.parameters?.docs?.source},description:{story:`Verify the editor renders with initial XML content.`,...q.parameters?.docs?.description}}},J.parameters={...J.parameters,docs:{...J.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const textarea = canvas.getByRole("textbox");

    // Save button should be disabled initially (not dirty)
    const saveButton = canvas.getByRole("button", {
      name: /save/i
    });
    await expect(saveButton).toBeDisabled();

    // Type additional content
    await userEvent.type(textarea, "\\n<!-- modified -->");

    // Save button should now be enabled
    await expect(saveButton).not.toBeDisabled();
  }
}`,...J.parameters?.docs?.source},description:{story:`Edit XML and verify the Save button becomes enabled (dirty).`,...J.parameters?.docs?.description}}},Y.parameters={...Y.parameters,docs:{...Y.parameters?.docs,source:{originalSource:`{
  play: async ({
    canvasElement
  }) => {
    const canvas = within(canvasElement);
    const textarea = canvas.getByRole("textbox");

    // Make a change to enable save
    await userEvent.type(textarea, "\\n<!-- saved -->");

    // Click save
    const saveButton = canvas.getByRole("button", {
      name: /save/i
    });
    await userEvent.click(saveButton);

    // Verify save was called (async — wait for the handler to complete)
    await expect(await canvas.findByTestId("save-result")).toHaveTextContent("CORS saved");
  }
}`,...Y.parameters?.docs?.source},description:{story:`Edit and save the CORS configuration.`,...Y.parameters?.docs?.description}}},X=[`RendersWithContent`,`EditMakesDirty`,`SaveConfiguration`]}))();export{J as EditMakesDirty,q as RendersWithContent,Y as SaveConfiguration,X as __namedExportsOrder,K as default};