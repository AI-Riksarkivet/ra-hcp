import Root from "./sheet.svelte";
import Portal from "./sheet-portal.svelte";
import Trigger from "./sheet-trigger.svelte";
import Close from "./sheet-close.svelte";
import Overlay from "./sheet-overlay.svelte";
import Content from "./sheet-content.svelte";
import Header from "./sheet-header.svelte";
import Footer from "./sheet-footer.svelte";
import Title from "./sheet-title.svelte";
import Description from "./sheet-description.svelte";

export {
  Close,
  Close as SheetClose,
  Content,
  Content as SheetContent,
  Description,
  Description as SheetDescription,
  Footer,
  Footer as SheetFooter,
  Header,
  Header as SheetHeader,
  Overlay,
  Overlay as SheetOverlay,
  Portal,
  Portal as SheetPortal,
  Root,
  //
  Root as Sheet,
  Title,
  Title as SheetTitle,
  Trigger,
  Trigger as SheetTrigger,
};
