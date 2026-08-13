import { useCallback, useRef, useState } from "react";
import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import * as ImagePicker from "expo-image-picker";
import * as DocumentPicker from "expo-document-picker";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";
import { api, ApiError } from "../../../src/api/client";
import { formatCents, formatDate } from "../../../src/api/format";
import type {
  Evidence,
  EvidenceKind,
  Package,
  PackageBulkImportResult,
  ReturnReason,
  WorkSession,
} from "../../../src/api/types";
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

const RETURN_REASONS: { value: ReturnReason; label: string }[] = [
  { value: "refused", label: "Recusado" },
  { value: "wrong_address", label: "Endereço errado" },
  { value: "damaged", label: "Danificado" },
  { value: "undeliverable", label: "Não entregável" },
  { value: "other", label: "Outro" },
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

  const [packages, setPackages] = useState<Package[]>([]);
  const [importCourier, setImportCourier] = useState("uniuni");
  const [importText, setImportText] = useState("");
  const [importing, setImporting] = useState(false);
  const [refreshingStatus, setRefreshingStatus] = useState(false);
  const [resolvingId, setResolvingId] = useState<string | null>(null);
  const [resolveOutcome, setResolveOutcome] = useState<"delivered" | "returned">("delivered");
  const [resolveReturnReason, setResolveReturnReason] = useState<ReturnReason>("wrong_address");

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
    api
      .get<Package[]>(`/sessions/${sessionId}/packages`)
      .then(setPackages)
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

  async function handleBulkImport() {
    if (!sessionId) return;
    const codes = importText
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);
    if (codes.length === 0) return;

    setError(null);
    setImporting(true);
    try {
      const result = await api.post<PackageBulkImportResult>(
        `/sessions/${sessionId}/packages/bulk-import`,
        { tracking_codes: codes, courier_code: importCourier || null }
      );
      setImportText("");
      if (result.skipped_duplicates.length > 0) {
        setError(`${result.skipped_duplicates.length} código(s) já existiam nessa sessão e foram ignorados.`);
      }
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to import packages");
    } finally {
      setImporting(false);
    }
  }

  async function handleRefreshStatus() {
    if (!sessionId) return;
    setError(null);
    setRefreshingStatus(true);
    try {
      await api.post(`/sessions/${sessionId}/packages/refresh-status`, {});
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to refresh carrier status");
    } finally {
      setRefreshingStatus(false);
    }
  }

  async function handleResolve(pkg: Package) {
    if (!sessionId) return;
    setError(null);
    try {
      await api.post(`/sessions/${sessionId}/packages/${pkg.id}/resolve`, {
        outcome: resolveOutcome,
        return_reason: resolveOutcome === "returned" ? resolveReturnReason : null,
      });
      setResolvingId(null);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to resolve package");
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
        if (coords.address) {
          form.append("address", coords.address);
        }
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

  async function pickImage(source: "camera" | "library") {
    let result: ImagePicker.ImagePickerResult;
    if (source === "camera") {
      const { status } = await ImagePicker.requestCameraPermissionsAsync();
      if (status !== "granted") {
        setError("Permissão de câmera negada.");
        return;
      }
      result = await ImagePicker.launchCameraAsync({ mediaTypes: ["images"], quality: 0.9 });
    } else {
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (status !== "granted") {
        setError("Permissão de galeria negada.");
        return;
      }
      result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ["images"], quality: 0.9 });
    }
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
        <View style={styles.rowBetween}>
          <Text style={styles.cardTitle}>Pacotes</Text>
          {packages.some((p) => p.source !== "manual") && (
            <Pressable onPress={handleRefreshStatus} disabled={refreshingStatus}>
              <Text style={styles.refreshLink}>
                {refreshingStatus ? "..." : "↻ Atualizar status"}
              </Text>
            </Pressable>
          )}
        </View>

        <View style={{ marginBottom: 14 }}>
          {packages.length === 0 && <Faint>Nenhum pacote registrado ainda.</Faint>}
          {packages.map((pkg) => (
            <View key={pkg.id} style={styles.packageRow}>
              <View style={styles.rowBetween}>
                <Mono>{pkg.tracking_code}</Mono>
                <View
                  style={[
                    styles.outcomePill,
                    pkg.outcome === null && { backgroundColor: colors.pendingBg },
                    pkg.outcome === "delivered" && { backgroundColor: colors.goodBg },
                    pkg.outcome === "returned" && { backgroundColor: colors.badBg },
                  ]}
                >
                  <Text
                    style={[
                      styles.outcomePillText,
                      pkg.outcome === null && { color: colors.pending },
                      pkg.outcome === "delivered" && { color: colors.good },
                      pkg.outcome === "returned" && { color: colors.bad },
                    ]}
                  >
                    {pkg.outcome === null ? "PENDENTE" : pkg.outcome === "delivered" ? "ENTREGUE" : "DEVOLVIDO"}
                  </Text>
                </View>
              </View>

              {pkg.carrier_status && (
                <Faint style={{ fontSize: 12, marginTop: 2 }}>
                  {pkg.source !== "manual" ? pkg.source.toUpperCase() : ""} · {pkg.carrier_status}
                </Faint>
              )}

              {pkg.outcome === null && resolvingId !== pkg.id && (
                <Pressable onPress={() => setResolvingId(pkg.id)} style={{ marginTop: 6 }}>
                  <Text style={styles.refreshLink}>Confirmar entrega/devolução</Text>
                </Pressable>
              )}

              {resolvingId === pkg.id && (
                <View style={{ marginTop: 8, gap: 8 }}>
                  <View style={styles.chipList}>
                    {(["delivered", "returned"] as const).map((o) => (
                      <Pressable
                        key={o}
                        onPress={() => setResolveOutcome(o)}
                        style={[styles.chip, resolveOutcome === o && styles.chipActive]}
                      >
                        <Text style={[styles.chipText, resolveOutcome === o && styles.chipTextActive]}>
                          {o === "delivered" ? "Entregue" : "Devolvido"}
                        </Text>
                      </Pressable>
                    ))}
                  </View>
                  {resolveOutcome === "returned" && (
                    <View style={styles.chipList}>
                      {RETURN_REASONS.map((r) => (
                        <Pressable
                          key={r.value}
                          onPress={() => setResolveReturnReason(r.value)}
                          style={[styles.chip, resolveReturnReason === r.value && styles.chipActive]}
                        >
                          <Text
                            style={[
                              styles.chipText,
                              resolveReturnReason === r.value && styles.chipTextActive,
                            ]}
                          >
                            {r.label}
                          </Text>
                        </Pressable>
                      ))}
                    </View>
                  )}
                  <View style={{ flexDirection: "row", gap: 10 }}>
                    <AppButton title="Confirmar" onPress={() => handleResolve(pkg)} style={{ flex: 1 }} />
                    <AppButton
                      title="Cancelar"
                      variant="ghost"
                      onPress={() => setResolvingId(null)}
                      style={{ flex: 1 }}
                    />
                  </View>
                </View>
              )}
            </View>
          ))}
        </View>

        <Text style={styles.label}>Transportadora</Text>
        <View style={styles.chipList}>
          {[
            { value: "uniuni", label: "UniUni" },
            { value: "gofo", label: "GOFO" },
            { value: "", label: "Auto" },
          ].map((c) => (
            <Pressable
              key={c.value}
              onPress={() => setImportCourier(c.value)}
              style={[styles.chip, importCourier === c.value && styles.chipActive]}
            >
              <Text style={[styles.chipText, importCourier === c.value && styles.chipTextActive]}>
                {c.label}
              </Text>
            </Pressable>
          ))}
        </View>
        <Field
          label="Códigos de rastreio (um por linha)"
          value={importText}
          onChangeText={setImportText}
          multiline
          numberOfLines={4}
          placeholder={"LV209031969CN\nLV209031970CN"}
        />
        <AppButton
          title="Importar pacotes"
          variant="secondary"
          onPress={handleBulkImport}
          loading={importing}
          disabled={!importText.trim()}
        />
      </Card>

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

        <View style={{ flexDirection: "row", gap: 10, marginBottom: 10 }}>
          <AppButton
            title="Câmera"
            variant="secondary"
            onPress={() => pickImage("camera")}
            loading={uploadingEvidence}
            style={{ flex: 1 }}
          />
          <AppButton
            title="Galeria"
            variant="secondary"
            onPress={() => pickImage("library")}
            loading={uploadingEvidence}
            style={{ flex: 1 }}
          />
        </View>
        <AppButton
          title="PDF"
          variant="secondary"
          onPress={pickPdf}
          loading={uploadingEvidence}
        />
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
  refreshLink: {
    color: colors.crimsonGlow,
    fontSize: 13,
  },
  packageRow: {
    borderTopWidth: 1,
    borderTopColor: colors.line,
    paddingVertical: 10,
  },
  outcomePill: {
    paddingVertical: 3,
    paddingHorizontal: 10,
    borderRadius: 999,
  },
  outcomePillText: {
    fontSize: 11,
    fontWeight: "700",
    textTransform: "uppercase",
  },
});
