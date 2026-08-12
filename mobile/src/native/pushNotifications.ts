import AsyncStorage from "@react-native-async-storage/async-storage";
import Constants from "expo-constants";
import * as Device from "expo-device";
import * as Notifications from "expo-notifications";
import { Platform } from "react-native";
import { api } from "../api/client";

const STORAGE_KEY = "rinko_push_token";

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: false,
    shouldSetBadge: false,
  }),
});

/**
 * Asks for notification permission and returns an Expo push token, or null
 * if unavailable — no physical device, permission denied, running on web
 * (expo-notifications push tokens are a native-only concept), or no EAS
 * project configured yet (`projectId` only exists once `eas init` has run
 * against a real Expo account, which this app doesn't have here).
 */
export async function registerForPushNotificationsAsync(): Promise<string | null> {
  if (Platform.OS === "web") return null;
  if (!Device.isDevice) return null;

  const projectId = Constants.expoConfig?.extra?.eas?.projectId as string | undefined;
  if (!projectId) {
    console.warn("No EAS projectId configured — skipping push token registration.");
    return null;
  }

  const existing = await Notifications.getPermissionsAsync();
  let status = existing.status;
  if (status !== "granted") {
    const requested = await Notifications.requestPermissionsAsync();
    status = requested.status;
  }
  if (status !== "granted") return null;

  if (Platform.OS === "android") {
    await Notifications.setNotificationChannelAsync("default", {
      name: "default",
      importance: Notifications.AndroidImportance.DEFAULT,
    });
  }

  try {
    const { data } = await Notifications.getExpoPushTokenAsync({ projectId });
    await AsyncStorage.setItem(STORAGE_KEY, data);
    return data;
  } catch (err) {
    console.warn("Failed to get Expo push token:", err);
    return null;
  }
}

/** Registers the device's push token with the backend, if one was obtained. */
export async function syncPushTokenWithBackend(): Promise<void> {
  const token = await registerForPushNotificationsAsync();
  if (token) await api.post("/account/push-token", { token }).catch(() => {});
}

/** Call on logout so a signed-out device stops getting this driver's reminders. */
export async function unregisterPushToken(): Promise<void> {
  const token = await AsyncStorage.getItem(STORAGE_KEY);
  if (!token) return;
  await api.del("/account/push-token", { token }).catch(() => {});
  await AsyncStorage.removeItem(STORAGE_KEY);
}
