export type Coords = {
  latitude: number;
  longitude: number;
  address: string | null;
  capturedAt: string;
};

function formatCoords(lat: number, lon: number): string {
  const latDir = lat >= 0 ? "N" : "S";
  const lonDir = lon >= 0 ? "E" : "W";
  return `${Math.abs(lat).toFixed(5)}° ${latDir}, ${Math.abs(lon).toFixed(5)}° ${lonDir}`;
}

/** Reverse-geocodes via OpenStreetMap's Nominatim — free, no API key. Resolves
 * to null on any failure (offline, rate-limited, no match); callers should
 * fall back to raw coordinates rather than blocking on this. */
async function reverseGeocode(lat: number, lon: number): Promise<string | null> {
  try {
    const resp = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lon}&zoom=18&addressdetails=1`
    );
    if (!resp.ok) return null;
    const data = await resp.json();
    const addr = data.address ?? {};
    const line = [addr.house_number, addr.road].filter(Boolean).join(" ");
    const city = addr.city ?? addr.town ?? addr.village ?? addr.county;
    const parts = [line, city, addr.state].filter(Boolean);
    if (parts.length > 0) return parts.join(", ");
    return typeof data.display_name === "string" ? data.display_name : null;
  } catch {
    return null;
  }
}

/** Wraps the browser Geolocation API + reverse geocoding in a promise;
 * resolves to null on denial/timeout/unsupported browser rather than
 * throwing — GPS is a nice extra on evidence, never something that should
 * block an upload. */
export function getCurrentLocation(timeoutMs = 8000): Promise<Coords | null> {
  return new Promise((resolve) => {
    if (!("geolocation" in navigator)) {
      resolve(null);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude } = pos.coords;
        const address = await reverseGeocode(latitude, longitude);
        resolve({
          latitude,
          longitude,
          address,
          capturedAt: new Date(pos.timestamp).toISOString(),
        });
      },
      () => resolve(null),
      { enableHighAccuracy: true, timeout: timeoutMs, maximumAge: 60_000 }
    );
  });
}

function truncateToWidth(ctx: CanvasRenderingContext2D, text: string, maxWidth: number): string {
  if (ctx.measureText(text).width <= maxWidth) return text;
  let truncated = text;
  while (truncated.length > 1 && ctx.measureText(truncated + "…").width > maxWidth) {
    truncated = truncated.slice(0, -1);
  }
  return truncated + "…";
}

/** Draws a semi-transparent stamp with the address (falls back to raw
 * coordinates if reverse geocoding failed) + date/time onto the bottom-right
 * corner of an image file, so the location is visible at a glance on the
 * photo itself — not just stored as metadata. Returns a new File; the
 * original is left untouched. Falls back to the original file if the
 * browser can't decode/re-encode the image for any reason. */
export async function stampImageWithLocation(file: File, coords: Coords): Promise<File> {
  try {
    const bitmap = await createImageBitmap(file);
    const canvas = document.createElement("canvas");
    canvas.width = bitmap.width;
    canvas.height = bitmap.height;
    const ctx = canvas.getContext("2d");
    if (!ctx) return file;

    ctx.drawImage(bitmap, 0, 0);

    const locationText = coords.address ?? formatCoords(coords.latitude, coords.longitude);
    const dateText = new Date(coords.capturedAt).toLocaleString();
    const fontSize = Math.max(14, Math.round(canvas.width * 0.022));
    const padding = Math.round(fontSize * 0.7);
    const lineGap = Math.round(fontSize * 0.35);
    const maxTextWidth = canvas.width * 0.6 - padding * 2;

    ctx.font = `600 ${fontSize}px -apple-system, sans-serif`;
    const locationLine = truncateToWidth(ctx, locationText, maxTextWidth);
    const locationWidth = ctx.measureText(locationLine).width;
    ctx.font = `${Math.round(fontSize * 0.8)}px -apple-system, sans-serif`;
    const dateLine = truncateToWidth(ctx, dateText, maxTextWidth);
    const dateWidth = ctx.measureText(dateLine).width;

    const boxWidth = Math.max(locationWidth, dateWidth) + padding * 2;
    const boxHeight = fontSize + Math.round(fontSize * 0.8) + lineGap + padding * 2;
    const boxX = canvas.width - boxWidth - padding;
    const boxY = canvas.height - boxHeight - padding;

    ctx.fillStyle = "rgba(10, 7, 7, 0.62)";
    const radius = 8;
    ctx.beginPath();
    ctx.moveTo(boxX + radius, boxY);
    ctx.arcTo(boxX + boxWidth, boxY, boxX + boxWidth, boxY + boxHeight, radius);
    ctx.arcTo(boxX + boxWidth, boxY + boxHeight, boxX, boxY + boxHeight, radius);
    ctx.arcTo(boxX, boxY + boxHeight, boxX, boxY, radius);
    ctx.arcTo(boxX, boxY, boxX + boxWidth, boxY, radius);
    ctx.closePath();
    ctx.fill();

    ctx.textAlign = "right";
    ctx.textBaseline = "top";
    ctx.fillStyle = "#F4EDE8";
    ctx.font = `600 ${fontSize}px -apple-system, sans-serif`;
    ctx.fillText(locationLine, boxX + boxWidth - padding, boxY + padding);
    ctx.fillStyle = "#E98DA0";
    ctx.font = `${Math.round(fontSize * 0.8)}px -apple-system, sans-serif`;
    ctx.fillText(dateLine, boxX + boxWidth - padding, boxY + padding + fontSize + lineGap);

    const blob: Blob | null = await new Promise((resolve) =>
      canvas.toBlob(resolve, file.type || "image/jpeg", 0.92)
    );
    if (!blob) return file;
    return new File([blob], file.name, { type: blob.type });
  } catch {
    return file;
  }
}
