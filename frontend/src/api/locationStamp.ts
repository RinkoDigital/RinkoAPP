export type Coords = {
  latitude: number;
  longitude: number;
  capturedAt: string;
};

/** Wraps the browser Geolocation API in a promise; resolves to null on
 * denial/timeout/unsupported browser rather than throwing — GPS is a nice
 * extra on evidence, never something that should block an upload. */
export function getCurrentLocation(timeoutMs = 8000): Promise<Coords | null> {
  return new Promise((resolve) => {
    if (!("geolocation" in navigator)) {
      resolve(null);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) =>
        resolve({
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
          capturedAt: new Date(pos.timestamp).toISOString(),
        }),
      () => resolve(null),
      { enableHighAccuracy: true, timeout: timeoutMs, maximumAge: 60_000 }
    );
  });
}

function formatCoords(lat: number, lon: number): string {
  const latDir = lat >= 0 ? "N" : "S";
  const lonDir = lon >= 0 ? "E" : "W";
  return `${Math.abs(lat).toFixed(5)}° ${latDir}, ${Math.abs(lon).toFixed(5)}° ${lonDir}`;
}

/** Draws a semi-transparent stamp with the coordinates + date/time onto the
 * bottom-right corner of an image file, so the location is visible at a
 * glance on the photo itself — not just stored as metadata. Returns a new
 * File; the original is left untouched. Falls back to the original file if
 * the browser can't decode/re-encode the image for any reason. */
export async function stampImageWithLocation(file: File, coords: Coords): Promise<File> {
  try {
    const bitmap = await createImageBitmap(file);
    const canvas = document.createElement("canvas");
    canvas.width = bitmap.width;
    canvas.height = bitmap.height;
    const ctx = canvas.getContext("2d");
    if (!ctx) return file;

    ctx.drawImage(bitmap, 0, 0);

    const coordsText = formatCoords(coords.latitude, coords.longitude);
    const dateText = new Date(coords.capturedAt).toLocaleString();
    const fontSize = Math.max(14, Math.round(canvas.width * 0.022));
    const padding = Math.round(fontSize * 0.7);
    const lineGap = Math.round(fontSize * 0.35);

    ctx.font = `600 ${fontSize}px -apple-system, sans-serif`;
    const coordsWidth = ctx.measureText(coordsText).width;
    ctx.font = `${Math.round(fontSize * 0.8)}px -apple-system, sans-serif`;
    const dateWidth = ctx.measureText(dateText).width;

    const boxWidth = Math.max(coordsWidth, dateWidth) + padding * 2;
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
    ctx.fillText(coordsText, boxX + boxWidth - padding, boxY + padding);
    ctx.fillStyle = "#E98DA0";
    ctx.font = `${Math.round(fontSize * 0.8)}px -apple-system, sans-serif`;
    ctx.fillText(dateText, boxX + boxWidth - padding, boxY + padding + fontSize + lineGap);

    const blob: Blob | null = await new Promise((resolve) =>
      canvas.toBlob(resolve, file.type || "image/jpeg", 0.92)
    );
    if (!blob) return file;
    return new File([blob], file.name, { type: blob.type });
  } catch {
    return file;
  }
}
