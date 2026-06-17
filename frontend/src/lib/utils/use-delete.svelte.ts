import { toast } from "svelte-sonner";
import { getErrorMessage } from "$lib/utils/get-error-message.js";

interface UseDeleteOptions {
  entityName: string;
}

export function useDelete(opts: UseDeleteOptions) {
  let deleteTarget = $state("");
  let deleteDialogOpen = $state(false);
  let bulkDeleteOpen = $state(false);
  let deleting = $state(false);

  function requestDelete(name: string) {
    deleteTarget = name;
    deleteDialogOpen = true;
  }

  function requestBulkDelete() {
    bulkDeleteOpen = true;
  }

  async function confirmDelete(
    deleteFn: () => Promise<unknown>,
  ) {
    if (!deleteTarget) return;
    deleting = true;
    try {
      await deleteFn();
      toast.success(`Deleted ${opts.entityName} "${deleteTarget}"`);
    } catch (err) {
      toast.error(getErrorMessage(err, `Failed to delete ${opts.entityName}`));
    } finally {
      deleting = false;
      deleteDialogOpen = false;
      deleteTarget = "";
    }
  }

  // Bulk delete is owned by the global bulk-delete-progress store
  // (bounded-parallel, survives navigation); this hook only manages the
  // single-item flow + the bulk dialog's open state.

  return {
    get deleteTarget() {
      return deleteTarget;
    },
    get deleteDialogOpen() {
      return deleteDialogOpen;
    },
    set deleteDialogOpen(v: boolean) {
      deleteDialogOpen = v;
    },
    get bulkDeleteOpen() {
      return bulkDeleteOpen;
    },
    set bulkDeleteOpen(v: boolean) {
      bulkDeleteOpen = v;
    },
    get deleting() {
      return deleting;
    },
    requestDelete,
    requestBulkDelete,
    confirmDelete,
  };
}
