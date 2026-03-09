import { toast } from "svelte-sonner";

interface UseSaveOptions {
  successMsg: string;
  errorMsg: string;
}

export function useSave(opts: UseSaveOptions) {
  let saving = $state(false);
  let syncVersion = $state(0);

  async function run(fn: () => Promise<unknown>) {
    saving = true;
    try {
      await fn();
      syncVersion++;
      toast.success(opts.successMsg);
    } catch {
      toast.error(opts.errorMsg);
    } finally {
      saving = false;
    }
  }

  return {
    get saving() {
      return saving;
    },
    get syncVersion() {
      return syncVersion;
    },
    run,
  };
}
