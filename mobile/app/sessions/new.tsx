import { useEffect, useState } from "react";
import { useRouter } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { api, ApiError } from "../../src/api/client";
import type { Carrier, WorkSession } from "../../src/api/types";
import { AppButton, Card, ErrorBanner, Field, Screen, Title, TopBar } from "../../src/components/ui";
import { colors } from "../../src/theme";

const NEW_CARRIER = "__new__";

export default function StartSessionScreen() {
  const router = useRouter();
  const [carriers, setCarriers] = useState<Carrier[] | null>(null);
  const [carrierId, setCarrierId] = useState("");
  const [newCarrierName, setNewCarrierName] = useState("");
  const [routeId, setRouteId] = useState("");
  const [serviceDate, setServiceDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [packagesAssigned, setPackagesAssigned] = useState("");
  const [rateDollars, setRateDollars] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api
      .get<Carrier[]>("/carriers")
      .then((list) => {
        setCarriers(list);
        setCarrierId(list.length > 0 ? list[0].id : NEW_CARRIER);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load"));
  }, []);

  async function handleSubmit() {
    setError(null);
    setLoading(true);
    try {
      let carrier = carriers?.find((c) => c.id === carrierId) ?? null;
      if (carrierId === NEW_CARRIER || carrier === null) {
        if (!newCarrierName.trim()) {
          throw new Error("Informe o nome da contratante");
        }
        carrier = await api.post<Carrier>("/carriers", {
          name: newCarrierName.trim(),
          default_rate_cents: rateDollars ? Math.round(parseFloat(rateDollars) * 100) : null,
        });
      }

      const session = await api.post<WorkSession>("/sessions", {
        carrier_id: carrier.id,
        route_id: routeId || null,
        service_date: serviceDate,
        packages_assigned: packagesAssigned ? parseInt(packagesAssigned, 10) : 0,
        agreed_rate_cents: rateDollars ? Math.round(parseFloat(rateDollars) * 100) : null,
      });
      router.replace(`/sessions/${session.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : (err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Screen>
      <TopBar>
        <Title>Iniciar Work Session</Title>
      </TopBar>

      {error && <ErrorBanner message={error} />}

      <Card>
        <Text style={styles.label}>Carrier / Contractor</Text>
        <View style={styles.chipList}>
          {carriers?.map((c) => (
            <Pressable
              key={c.id}
              onPress={() => setCarrierId(c.id)}
              style={[styles.chip, carrierId === c.id && styles.chipActive]}
            >
              <Text style={[styles.chipText, carrierId === c.id && styles.chipTextActive]}>
                {c.name}
              </Text>
            </Pressable>
          ))}
          <Pressable
            onPress={() => setCarrierId(NEW_CARRIER)}
            style={[styles.chip, carrierId === NEW_CARRIER && styles.chipActive]}
          >
            <Text style={[styles.chipText, carrierId === NEW_CARRIER && styles.chipTextActive]}>
              + Nova contratante
            </Text>
          </Pressable>
        </View>

        {carrierId === NEW_CARRIER && (
          <Field
            label="Nome da contratante"
            placeholder="UniUni, GOFO, OnTrac…"
            value={newCarrierName}
            onChangeText={setNewCarrierName}
          />
        )}

        <Field label="Route ID" value={routeId} onChangeText={setRouteId} />
        <Field label="Data (AAAA-MM-DD)" value={serviceDate} onChangeText={setServiceDate} />
        <Field
          label="Packages assigned"
          value={packagesAssigned}
          onChangeText={setPackagesAssigned}
          keyboardType="number-pad"
        />
        <Field
          label="Agreed rate ($/pacote)"
          placeholder="1.80"
          value={rateDollars}
          onChangeText={setRateDollars}
          keyboardType="decimal-pad"
        />

        <AppButton title="Iniciar Work Session" onPress={handleSubmit} loading={loading} />
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
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
    backgroundColor: colors.violet,
    borderColor: colors.violet,
  },
  chipText: {
    color: colors.textMuted,
    fontSize: 13,
  },
  chipTextActive: {
    color: colors.accentInk,
    fontWeight: "600",
  },
});
