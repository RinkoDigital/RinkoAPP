import * as Location from "expo-location";

export type Coords = {
  latitude: number;
  longitude: number;
  address: string | null;
  capturedAt: string;
};

/** Reverse-geocodes via the device's native OS geocoder — no API key or
 * network service needed. Resolves to null on any failure (permission
 * quirks, no result, simulator without geocoding support); callers should
 * fall back to raw coordinates rather than blocking on this. */
async function reverseGeocode(lat: number, lon: number): Promise<string | null> {
  try {
    const results = await Location.reverseGeocodeAsync({ latitude: lat, longitude: lon });
    const first = results[0];
    if (!first) return null;
    const line = [first.streetNumber, first.street].filter(Boolean).join(" ");
    const city = first.city ?? first.subregion ?? first.district;
    const parts = [line, city, first.region].filter(Boolean);
    return parts.length > 0 ? parts.join(", ") : null;
  } catch {
    return null;
  }
}

/** Asks for location permission and returns the current GPS fix (with
 * reverse-geocoded address, when available), or null on denial/error — GPS
 * is a nice extra on evidence, never something that should block an
 * upload. */
export async function getCurrentLocation(): Promise<Coords | null> {
  try {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== "granted") return null;
    const pos = await Location.getCurrentPositionAsync({});
    const address = await reverseGeocode(pos.coords.latitude, pos.coords.longitude);
    return {
      latitude: pos.coords.latitude,
      longitude: pos.coords.longitude,
      address,
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
