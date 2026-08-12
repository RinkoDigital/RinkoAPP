import * as Location from "expo-location";

export type Coords = {
  latitude: number;
  longitude: number;
  capturedAt: string;
};

/** Asks for location permission and returns the current GPS fix, or null
 * on denial/error — GPS is a nice extra on evidence, never something that
 * should block an upload. */
export async function getCurrentLocation(): Promise<Coords | null> {
  try {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== "granted") return null;
    const pos = await Location.getCurrentPositionAsync({});
    return {
      latitude: pos.coords.latitude,
      longitude: pos.coords.longitude,
      capturedAt: new Date(pos.timestamp).toISOString(),
    };
  } catch {
    return null;
  }
}

export function formatCoords(lat: number, lon: number): string {
  const latDir = lat >= 0 ? "N" : "S";
  const lonDir = lon >= 0 ? "E" : "W";
  return `${Math.abs(lat).toFixed(5)}° ${latDir}, ${Math.abs(lon).toFixed(5)}° ${lonDir}`;
}
