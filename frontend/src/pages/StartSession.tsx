import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { Carrier, WorkSession } from "../api/types";

const NEW_CARRIER = "__new__";

export function StartSessionPage() {
  const navigate = useNavigate();
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

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
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
      navigate(`/sessions/${session.id}`, { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : (err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <div className="top-bar">
        <h1>Iniciar Work Session</h1>
      </div>
      <div className="screen">
        {error && <div className="error-banner">{error}</div>}

        <form onSubmit={handleSubmit} className="card">
          <div className="field">
            <label htmlFor="carrier">Carrier / Contractor</label>
            {carriers === null ? (
              <span className="spinner" />
            ) : (
              <select id="carrier" value={carrierId} onChange={(e) => setCarrierId(e.target.value)}>
                {carriers.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
                <option value={NEW_CARRIER}>+ Nova contratante</option>
              </select>
            )}
          </div>

          {carrierId === NEW_CARRIER && (
            <div className="field">
              <label htmlFor="newCarrier">Nome da contratante</label>
              <input
                id="newCarrier"
                placeholder="UniUni, GOFO, OnTrac…"
                value={newCarrierName}
                onChange={(e) => setNewCarrierName(e.target.value)}
              />
            </div>
          )}

          <div className="field">
            <label htmlFor="routeId">Route ID</label>
            <input id="routeId" value={routeId} onChange={(e) => setRouteId(e.target.value)} />
          </div>

          <div className="field">
            <label htmlFor="serviceDate">Data</label>
            <input
              id="serviceDate"
              type="date"
              value={serviceDate}
              onChange={(e) => setServiceDate(e.target.value)}
              required
            />
          </div>

          <div className="field">
            <label htmlFor="packages">Packages assigned</label>
            <input
              id="packages"
              type="number"
              min={0}
              value={packagesAssigned}
              onChange={(e) => setPackagesAssigned(e.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="rate">Agreed rate ($/pacote)</label>
            <input
              id="rate"
              type="number"
              step="0.01"
              min={0}
              placeholder="1.80"
              value={rateDollars}
              onChange={(e) => setRateDollars(e.target.value)}
            />
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? <span className="spinner" /> : "Iniciar Work Session"}
          </button>
        </form>
      </div>
    </div>
  );
}
