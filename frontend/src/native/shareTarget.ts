import { Capacitor, registerPlugin } from "@capacitor/core";

export type SharedItem = {
  present: boolean;
  mimeType?: string;
  fileName?: string;
  base64Data?: string;
};

interface ShareTargetPluginApi {
  getSharedItem(): Promise<SharedItem>;
  addListener(
    eventName: "shareReceived",
    listener: (data: SharedItem) => void
  ): Promise<{ remove: () => void }>;
}

const ShareTargetNative = registerPlugin<ShareTargetPluginApi>("ShareTarget");

export function isNativeApp(): boolean {
  return Capacitor.isNativePlatform();
}

/** Checks whether the OS handed us a file via the Share Sheet on this launch. No-op on web. */
export async function consumePendingShare(): Promise<SharedItem | null> {
  if (!isNativeApp()) return null;
  try {
    const item = await ShareTargetNative.getSharedItem();
    return item.present ? item : null;
  } catch {
    return null;
  }
}

/** Fires while the app is already open and a new share arrives (Android onNewIntent / iOS resume). */
export function onShareReceived(listener: (item: SharedItem) => void): () => void {
  if (!isNativeApp()) return () => {};
  const handlePromise = ShareTargetNative.addListener("shareReceived", listener);
  return () => {
    handlePromise.then((h) => h.remove()).catch(() => {});
  };
}

export function sharedItemToFile(item: SharedItem): File {
  const byteChars = atob(item.base64Data ?? "");
  const byteNumbers = new Array(byteChars.length);
  for (let i = 0; i < byteChars.length; i++) {
    byteNumbers[i] = byteChars.charCodeAt(i);
  }
  const byteArray = new Uint8Array(byteNumbers);
  return new File([byteArray], item.fileName ?? "shared-file", {
    type: item.mimeType ?? "application/octet-stream",
  });
}
