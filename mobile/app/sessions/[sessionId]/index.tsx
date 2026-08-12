import { useCallback, useRef, useState } from "react";
import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import * as ImagePicker from "expo-image-picker";
import * as DocumentPicker from "expo-document-picker";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";
import { api, ApiError } from "../../../src/api/client";
import { formatCents, formatDate } from "../../../src/api/format";
import type { Evidence, EvidenceKind, WorkSession } from "../../../src/api/types";
import { LocationStamper, type LocationStamperHandle } from "../../../src/components/LocationStamper";
import { StatusPill } from "../../../src/components/StatusPill";
import {
  AppButton,
  Card,
  ErrorBanner,
  Faint,
  Field,
  Mono,
  Row,
  Screen,
  Title,
  TopBar,
} from "../../../src/components/ui";
import { getCurrentLocation, type Coords } from "../../../src/native/locationStamp";
import { colors } from "../../../src/theme";

const EVIDENCE_KINDS: { value: EvidenceKind; label: string }[] = [
  { value: "route_screenshot", label: "Route screenshot" },
  { value: "rate_screenshot", label: "Rate screenshot" },
  { value: "gps_session", label: "GPS session" },
  { value: "completion_record", label: "Completion record" },
  { value: "settlement_statement", label: "Settlement statement" },
  { value: "other", label: "Other" },
];

export default function SessionDetailScreen() {
  const { sessionId } = useLocalSearchParams<{ sessionId: string }>();
  const router = useRouter();
  const [session, setSession] = useState<WorkSession | null>(null);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [exceptionsCount, setExceptionsCount] = useState("0");
  const [mileage, setMileage] = useState("");
  const [closing, setClosing] = useState(false);

  const [paymentReceived, setPaymentReceived] = useState("");
  const [recordingPayment, setRecordingPayment] = useState(false);

  const [evidenceKind, setEvidenceKind] = useState<EvidenceKind>("route_screenshot");
  const [uploadingEvidence, setUploadingEvidence] = useState(false);
  const stamperRef = useRef<LocationStamperHandle>(null);

  const load = useCallback(() => {
    if (!sessionId) return;
    api
      .get<WorkSession>(`/sessions/${sessionId}`)
      .then(setSession)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load"));
    api
      .get<Evidence[]>(`/sessions/${sessionId}/evidence`)
      .then(setEvidence)
      .catch(() => {});
  }, [sessionId]);

  useFocusEffect(load);

  async function handleClose() {
    if (!sessionId) return;
    setError(null);
    setClosing(true);
    try {
      await api.post<WorkSession>(`/sessions/${sessionId}/close`, {
        exceptions_count: parseInt(exceptionsCount || "0", 10),
        mileage: mileage ? parseFloat(mileage) : null,
      });
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to close session");
    } finally {
      setClosing(false);
    }
  }

  async function handleRecordPayment() {
    if (!sessionId || !paymentReceived) return;
    setError(null);
    setRecordingPayment(true);
    try {
      await api.post<WorkSession>(`/sessions/${sessionId}/record-payment`, {
        payment_received_cents: Math.round(parseFloat(paymentReceived) * 100),
      });
      setPaymentReceived("");
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to record payment");
    } finally {
      setRecordingPayment(false);
    }
  }

  async function uploadFile(uri: string, name: string, type: string, coords?: Coords | null) {
    if (!sessionId) return;
    setError(null);
    setUploadingEvidence(true);
    try {
      const form = new FormData();
      form.append("kind", evidenceKind);
      if (uri.startsWith("data:")) {
        // Web only: react-native-view-shot has no real filesystem there, so
        // captureRef() resolves to a data URI instead of a file:// one — the
        // {uri, name, type} descriptor below is a React Native FormData
        // convention the browser's real FormData doesn't understand.
        const blob = await (await fetch(uri)).blob();
        form.append("file", blob, name);
      } else {
        // React Native's FormData accepts this file-descriptor shape directly.
        form.append("file", { uri, name, type } as unknown as Blob);
      }
      if (coords) {
        form.append("latitude", String(coords.latitude));
        form.append("longitude", String(coords.longitude));
        form.append("captured_at", coords.capturedAt);
      }
      await api.postForm<Evidence>(`/sessions/${sessionId}/evidence`, form);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to upload evidence");
    } finally {
      setUploadingEvidence(false);
    }
  }

  async function pickImage() {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ["images"],
      quality: 0.9,
    });
    if (result.canceled || result.assets.length === 0) return;
    const asset = result.assets[0];
    const name = asset.fileName ?? "evidence.jpg";
    const type = asset.mimeType ?? "image/jpeg";

    const coords = await getCurrentLocation();
    if (coords && stamperRef.current) {
      try {
        const stampedUri = await stamperRef.current.stamp(asset.uri, coords);
        await uploadFile(stampedUri, name, "image/jpeg", coords);
        return;
      } catch {
        // Stamping failed (decode/capture error) — fall through and upload
        // the original photo with the coordinates as plain metadata.
      }
    }
    await uploadFile(asset.uri, name, type, coords);
  }

  async function pickPdf() {
    const result = await DocumentPicker.getDocumentAsync({ type: "application/pdf" });
    if (result.canceled || result.assets.length === 0) return;
    const asset = result.assets[0];
    await uploadFile(asset.uri, asset.name, asset.mimeType ?? "application/pdf");
  }

  if (error && !session) {
    return (
      <Screen>
        <ErrorBanner message={error} />
      </Screen>
    );
  }

  if (!session) {
    return (
      <Screen>
        <ActivityIndicator color={colors.crimsonGlow} />
      </Screen>
    );
  }

  return (
    <Screen>
      <LocationStamper ref={stamperRef} />
      <TopBar>
        <Pressable onPress={() => router.back()}>
          <Text style={styles.backLink}>← Voltar</Text>
        </Pressable>
      </TopBar>

      {error && <ErrorBanner message={error} />}

      <Card>
        <View style={styles.rowBetween}>
          <Text style={styles.carrier}>
            {session.carrier_name}
            {session.route_id ? <Text style={{ color: colors.textFaint }}> · {session.route_id}</Text> : null}
          </Text>
          <StatusPill status={session.status === "open" ? "pending" : session.payment_status} />
        </View>
        <Faint>{formatDate(session.service_date)}</Faint>

        <Row label="Packages assigned" value={session.packages_assigned} />
        <Row label="Packages completed" value={session.packages_completed} />
        <Row label="Agreed rate" value={`${formatCents(session.agreed_rate_cents)}/pkg`} />
        {session.expected_gross_cents !== null && (
          <Row label="Expected gross" value={formatCents(session.expected_gross_cents)} />
        )}
        {session.status === "closed" && (
          <Row label="Outstanding" value={formatCents(session.outstanding_cents)} />
        )}
      </Card>

      {session.status === "open" && (
        <Card>
          <Text style={styles.cardTitle}>Encerrar sessão</Text>
          <Field
            label="Exceptions"
            value={exceptionsCount}
            onChangeText={setExceptionsCount}
            keyboardType="number-pad"
          />
          <Field label="Mileage" value={mileage} onChangeText={setMileage} keyboardType="decimal-pad" />
          <AppButton title="Encerrar e gerar Work Report" onPress={handleClose} loading={closing} />
        </Card>
      )}

      {session.status === "closed" && session.payment_status !== "received" && (
        <Card>
          <Text style={styles.cardTitle}>Registrar pagamento recebido</Text>
          <Field
            label="Recebido ($)"
            value={paymentReceived}
            onChangeText={setPaymentReceived}
            keyboardType="decimal-pad"
          />
          <AppButton
            title="Registrar pagamento"
            onPress={handleRecordPayment}
            loading={recordingPayment}
          />
        </Card>
      )}

      <Card>
        <Text style={styles.cardTitle}>Evidence</Text>
        <View style={styles.chipList}>
          {evidence.length === 0 && <Faint>Nenhuma evidência anexada ainda.</Faint>}
          {evidence.map((ev) => (
            <View key={ev.id} style={styles.evidenceChip}>
              <Text style={styles.evidenceChipText}>
                ✓ {EVIDENCE_KINDS.find((k) => k.value === ev.kind)?.label ?? ev.kind}
                {ev.latitude !== null ? " 📍" : ""}
              </Text>
            </View>
          ))}
        </View>

        <Text style={styles.label}>Tipo</Text>
        <View style={styles.chipList}>
          {EVIDENCE_KINDS.map((k) => (
            <Pressable
              key={k.value}
              onPress={() => setEvidenceKind(k.value)}
              style={[styles.chip, evidenceKind === k.value && styles.chipActive]}
            >
              <Text style={[styles.chipText, evidenceKind === k.value && styles.chipTextActive]}>
                {k.label}
              </Text>
            </Pressable>
          ))}
        </View>

        <View style={{ flexDirection: "row", gap: 10 }}>
          <AppButton
            title="Foto/imagem"
            variant="secondary"
            onPress={pickImage}
            loading={uploadingEvidence}
            style={{ flex: 1 }}
          />
          <AppButton
            title="PDF"
            variant="secondary"
            onPress={pickPdf}
            loading={uploadingEvidence}
            style={{ flex: 1 }}
          />
        </View>
      </Card>

      {session.status === "closed" && (
        <AppButton
          title="Ver Work Report"
          onPress={() => router.push(`/sessions/${session.id}/report`)}
        />
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  backLink: {
    color: colors.crimsonGlow,
  },
  rowBetween: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  carrier: {
    color: colors.text,
    fontWeight: "700",
  },
  cardTitle: {
    color: colors.text,
    fontWeight: "700",
    fontSize: 15,
    marginBottom: 12,
  },
  label: {
    color: colors.textMuted,
    fontSize: 13,
    marginBottom: 8,
  },
  chipList: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginBottom: 14,
  },
  chip: {
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: 999,
    paddingVertical: 7,
    paddingHorizontal: 14,
    backgroundColor: colors.cardSunken,
  },
  chipActive: {
    backgroundColor: colors.crimson,
    borderColor: colors.crimson,
  },
  chipText: {
    color: colors.textMuted,
    fontSize: 13,
  },
  chipTextActive: {
    color: colors.accentInk,
    fontWeight: "600",
  },
  evidenceChip: {
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: 999,
    paddingVertical: 5,
    paddingHorizontal: 12,
    backgroundColor: colors.cardSunken,
  },
  evidenceChipText: {
    color: colors.text,
    fontSize: 12,
  },
});
