import { toast } from "svelte-sonner";

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
    } catch {
      toast.error(`Failed to delete ${opts.entityName}`);
    } finally {
      deleting = false;
      deleteDialogOpen = false;
      deleteTarget = "";
    }
  }

  async function confirmBulkDelete(
    names: string[],
    deleteFn: (name: string, isLast: boolean) => Promise<unknown>,
    onDone?: () => void,
  ) {
    deleting = true;
    let successCount = 0;
    let failCount = 0;
    for (let i = 0; i < names.length; i++) {
      try {
        await deleteFn(names[i], i === names.length - 1);
        successCount++;
      } catch {
        failCount++;
      }
    }
    if (successCount > 0) {
      toast.success(
        `Deleted ${successCount} ${opts.entityName}${
          successCount !== 1 ? "s" : ""
        }`,
      );
    }
    if (failCount > 0) {
      toast.error(
        `Failed to delete ${failCount} ${opts.entityName}${
          failCount !== 1 ? "s" : ""
        }`,
      );
    }
    onDone?.();
    deleting = false;
    bulkDeleteOpen = false;
  }

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
    confirmBulkDelete,
  };
}
