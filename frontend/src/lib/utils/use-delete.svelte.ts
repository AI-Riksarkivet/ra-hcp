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
    } catch (err) {
      const msg = err instanceof Error
        ? err.message
        : `Failed to delete ${opts.entityName}`;
      toast.error(msg);
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
    const errors: string[] = [];
    for (let i = 0; i < names.length; i++) {
      try {
        await deleteFn(names[i], i === names.length - 1);
        successCount++;
      } catch (err) {
        failCount++;
        if (err instanceof Error && err.message) {
          errors.push(`${names[i]}: ${err.message}`);
        }
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
      const summary = errors.length > 0
        ? errors.join("\n")
        : `Failed to delete ${failCount} ${opts.entityName}${
          failCount !== 1 ? "s" : ""
        }`;
      toast.error(summary);
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
