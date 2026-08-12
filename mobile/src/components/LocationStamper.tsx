import { forwardRef, useImperativeHandle, useRef, useState } from "react";
import { Image, Text, View } from "react-native";
import { captureRef } from "react-native-view-shot";
import { colors } from "../theme";
import { formatCoords, type Coords } from "../native/locationStamp";

export type LocationStamperHandle = {
  /** Renders `uri` off-screen with the GPS coords stamped in the bottom-right
   * corner, captures it, and resolves to a new local file URI — the
   * original file is untouched. */
  stamp: (uri: string, coords: Coords) => Promise<string>;
};

type PendingJob = {
  uri: string;
  coords: Coords;
  width: number;
  height: number;
  resolve: (uri: string) => void;
  reject: (err: unknown) => void;
};

const MAX_DIMENSION = 1600;

/** Mount once per screen that uploads evidence photos. Renders nothing
 * visible — the composited image (photo + stamp) is built off-screen and
 * captured to a file, since React Native has no <canvas> to draw on
 * directly the way a browser does. */
export const LocationStamper = forwardRef<LocationStamperHandle>((_props, ref) => {
  const [job, setJob] = useState<PendingJob | null>(null);
  const containerRef = useRef<View>(null);

  useImperativeHandle(ref, () => ({
    stamp: (uri, coords) =>
      new Promise<string>((resolve, reject) => {
        Image.getSize(
          uri,
          (width, height) => {
            const scale = Math.min(1, MAX_DIMENSION / Math.max(width, height));
            setJob({
              uri,
              coords,
              width: Math.round(width * scale),
              height: Math.round(height * scale),
              resolve,
              reject,
            });
          },
          (err) => reject(err)
        );
      }),
  }));

  async function handleImageReady() {
    if (!job || !containerRef.current) return;
    // A short delay so the absolutely-positioned stamp text has definitely
    // painted before we capture — onLoadEnd only guarantees the photo did.
    await new Promise((r) => setTimeout(r, 50));
    try {
      const capturedUri = await captureRef(containerRef, { format: "jpg", quality: 0.9 });
      job.resolve(capturedUri);
    } catch (err) {
      job.reject(err);
    } finally {
      setJob(null);
    }
  }

  if (!job) return null;

  const fontSize = Math.max(14, Math.round(job.width * 0.028));

  return (
    <View style={{ position: "absolute", top: -100000, left: 0 }} collapsable={false}>
      <View ref={containerRef} style={{ width: job.width, height: job.height }} collapsable={false}>
        <Image
          source={{ uri: job.uri }}
          style={{ width: job.width, height: job.height }}
          onLoadEnd={handleImageReady}
        />
        <View
          style={{
            position: "absolute",
            right: fontSize * 0.7,
            bottom: fontSize * 0.7,
            backgroundColor: "rgba(10,7,7,0.62)",
            borderRadius: 8,
            paddingVertical: fontSize * 0.5,
            paddingHorizontal: fontSize * 0.7,
          }}
        >
          <Text style={{ color: colors.paper, fontWeight: "600", fontSize }}>
            {formatCoords(job.coords.latitude, job.coords.longitude)}
          </Text>
          <Text style={{ color: colors.sakura, fontSize: fontSize * 0.8, marginTop: 2 }}>
            {new Date(job.coords.capturedAt).toLocaleString()}
          </Text>
        </View>
      </View>
    </View>
  );
});

LocationStamper.displayName = "LocationStamper";
