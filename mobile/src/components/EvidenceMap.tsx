import { StyleSheet, View } from "react-native";
import { WebView } from "react-native-webview";
import { colors, radii } from "../theme";

export type EvidencePin = {
  id: string;
  latitude: number;
  longitude: number;
  label: string;
};

function buildMapHtml(pins: EvidencePin[]): string {
  const avgLat = pins.reduce((sum, p) => sum + p.latitude, 0) / pins.length;
  const avgLon = pins.reduce((sum, p) => sum + p.longitude, 0) / pins.length;
  const markers = pins
    .map(
      (p) =>
        `L.marker([${p.latitude}, ${p.longitude}]).addTo(map).bindPopup(${JSON.stringify(p.label)});`
    )
    .join("\n");

  return `<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>html,body,#map{height:100%;margin:0;padding:0;background:#150f0f}</style>
</head><body><div id="map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
var map = L.map('map').setView([${avgLat}, ${avgLon}], ${pins.length > 1 ? 12 : 15});
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors',
  maxZoom: 19,
}).addTo(map);
${markers}
${pins.length > 1 ? `map.fitBounds([${pins.map((p) => `[${p.latitude},${p.longitude}]`).join(",")}], { padding: [24, 24] });` : ""}
</script>
</body></html>`;
}

export function EvidenceMap({ pins }: { pins: EvidencePin[] }) {
  if (pins.length === 0) return null;
  return (
    <View style={styles.wrapper}>
      <WebView
        source={{ html: buildMapHtml(pins) }}
        style={styles.webview}
        scrollEnabled={false}
        originWhitelist={["*"]}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    height: 220,
    borderRadius: radii.card,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: colors.line,
    marginBottom: 14,
  },
  webview: {
    flex: 1,
    backgroundColor: colors.cardSunken,
  },
});
