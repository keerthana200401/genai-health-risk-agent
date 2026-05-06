import React, { useEffect, useMemo, useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

const API_BASE = "http://127.0.0.1:8000";

function cardStyle() {
  return {
    background: "#ffffff",
    borderRadius: 22,
    padding: 22,
    boxShadow: "0 10px 28px rgba(15, 23, 42, 0.08)",
    border: "1px solid #e5e7eb",
  };
}

function softBlockStyle() {
  return {
    background: "#f8fafc",
    borderRadius: 16,
    padding: 16,
    border: "1px solid #e5e7eb",
  };
}

function badgeStyle(level) {
  if ((level || "").includes("High")) {
    return { background: "#fee2e2", color: "#991b1b", border: "1px solid #fecaca" };
  }
  if ((level || "").includes("Moderate")) {
    return { background: "#fef3c7", color: "#92400e", border: "1px solid #fde68a" };
  }
  return { background: "#dcfce7", color: "#166534", border: "1px solid #bbf7d0" };
}

function StatCard({ title, value, subtitle }) {
  return (
    <div style={cardStyle()}>
      <div style={{ fontSize: 14, color: "#64748b" }}>{title}</div>
      <div style={{ marginTop: 8, fontSize: 34, fontWeight: 800 }}>{value}</div>
      <div style={{ marginTop: 6, fontSize: 13, color: "#64748b" }}>{subtitle}</div>
    </div>
  );
}

function SectionCard({ title, children }) {
  return (
    <div style={cardStyle()}>
      <div style={{ fontSize: 21, fontWeight: 800, marginBottom: 16 }}>{title}</div>
      {children}
    </div>
  );
}

export default function ClinicalAlertDashboard() {
  const [records, setRecords] = useState([]);
  const [summary, setSummary] = useState(null);
  const [limit, setLimit] = useState(50);
  const [riskFilter, setRiskFilter] = useState("All");
  const [sortMode, setSortMode] = useState("Severity High to Low");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchDashboardData = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE}/batch-analyze?limit=${limit}`);

      if (!response.ok) {
        throw new Error("Backend request failed.");
      }

      const data = await response.json();

      const cleaned = (data.results || [])
        .filter((item) => item.success)
        .map((item) => ({
          patient: item.patient_data,
          flags: item.grounded_flags,
        }));

      setRecords(cleaned);
      setSummary(data.summary || null);
    } catch (err) {
      console.error(err);
      setError("Unable to load dashboard data from FastAPI backend.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const filteredRecords = useMemo(() => {
    let rows = [...records];

    if (riskFilter !== "All") {
      rows = rows.filter((item) => item.flags.alert_level === riskFilter);
    }

    if (search.trim()) {
      rows = rows.filter((item) =>
        String(item.patient.patient_id).toLowerCase().includes(search.trim().toLowerCase())
      );
    }

    rows.sort((a, b) => {
      const aScore = a.flags.severity_score || 0;
      const bScore = b.flags.severity_score || 0;

      if (sortMode === "Severity Low to High") return aScore - bScore;
      return bScore - aScore;
    });

    return rows;
  }, [records, riskFilter, search, sortMode]);

  const totalPatients = records.length;
  const highRiskCount = summary?.high_risk ?? 0;
  const moderateRiskCount = summary?.moderate_risk ?? 0;
  const lowRiskCount = summary?.low_risk ?? 0;
  const averageSeverity = summary?.average_severity ?? 0;

  const distributionData = [
    { name: "High Risk", value: highRiskCount },
    { name: "Moderate Risk", value: moderateRiskCount },
    { name: "Low Risk", value: lowRiskCount },
  ];

  const severityData = filteredRecords.slice(0, 20).map((item) => ({
    patient: `P-${item.patient.patient_id}`,
    severity: item.flags.severity_score,
  }));

  const priorityCases = [...records]
    .sort((a, b) => b.flags.severity_score - a.flags.severity_score)
    .slice(0, 3);

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f8fafc",
        padding: 28,
        boxSizing: "border-box",
        fontFamily: "Inter, Arial, sans-serif",
        color: "#0f172a",
      }}
    >
      <div style={{ maxWidth: 1450, margin: "0 auto", display: "grid", gap: 24 }}>
        <div style={{ ...cardStyle(), padding: 30 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 20, alignItems: "flex-start" }}>
            <div>
              <div
                style={{
                  fontSize: 12,
                  letterSpacing: 2.8,
                  textTransform: "uppercase",
                  color: "#64748b",
                  marginBottom: 10,
                }}
              >
                FastAPI-powered operations layer
              </div>

              <div style={{ fontSize: 42, fontWeight: 900, lineHeight: 1.05 }}>
                Clinical Operations Risk Dashboard
              </div>

              <div style={{ marginTop: 12, fontSize: 15, color: "#64748b", maxWidth: 820 }}>
                Population-level monitoring view powered by the FastAPI backend and grounded chronic disease alert engine.
              </div>
            </div>

            <div
              style={{
                ...badgeStyle(highRiskCount > 0 ? "High Risk Alert" : moderateRiskCount > 0 ? "Moderate Risk Alert" : "No Immediate Alert"),
                borderRadius: 999,
                padding: "12px 18px",
                fontWeight: 800,
                whiteSpace: "nowrap",
              }}
            >
              {loading
                ? "Loading..."
                : highRiskCount > 0
                ? `${highRiskCount} High Priority Alerts`
                : moderateRiskCount > 0
                ? `${moderateRiskCount} Moderate Alerts`
                : "All Patients Stable"}
            </div>
          </div>

          <div style={{ marginTop: 18, display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
            <button
              onClick={fetchDashboardData}
              style={{
                padding: "11px 16px",
                borderRadius: 14,
                border: "none",
                background: "#2563eb",
                color: "#fff",
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              Refresh Dashboard
            </button>

            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              style={{ padding: "10px 12px", borderRadius: 12, border: "1px solid #cbd5e1" }}
            >
              <option value={25}>25 patients</option>
              <option value={50}>50 patients</option>
              <option value={100}>100 patients</option>
              <option value={200}>200 patients</option>
            </select>

            <span style={{ color: "#64748b", fontSize: 14 }}>
              Backend endpoint: <b>/batch-analyze</b>
            </span>
          </div>

          {error && (
            <div style={{ marginTop: 16, color: "#991b1b", background: "#fee2e2", padding: 12, borderRadius: 12 }}>
              {error}
            </div>
          )}
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 18 }}>
          <StatCard title="Total Patients Monitored" value={totalPatients} subtitle="Loaded from backend dataset" />
          <StatCard title="High Risk Alerts" value={highRiskCount} subtitle="Require clinical review" />
          <StatCard title="Moderate Risk Alerts" value={moderateRiskCount} subtitle="Need preventive follow-up" />
          <StatCard title="Average Severity" value={`${averageSeverity}/100`} subtitle="Across monitored queue" />
        </div>

        <SectionCard title="Dashboard Controls">
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14 }}>
            <div>
              <label style={{ fontWeight: 700, fontSize: 14 }}>Search Patient ID</label>
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Example: 1001"
                style={{
                  marginTop: 8,
                  width: "100%",
                  padding: 12,
                  borderRadius: 12,
                  border: "1px solid #cbd5e1",
                  boxSizing: "border-box",
                }}
              />
            </div>

            <div>
              <label style={{ fontWeight: 700, fontSize: 14 }}>Risk Filter</label>
              <select
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value)}
                style={{
                  marginTop: 8,
                  width: "100%",
                  padding: 12,
                  borderRadius: 12,
                  border: "1px solid #cbd5e1",
                  boxSizing: "border-box",
                }}
              >
                <option value="All">All</option>
                <option value="High Risk Alert">High Risk</option>
                <option value="Moderate Risk Alert">Moderate Risk</option>
                <option value="No Immediate Alert">Low Risk</option>
              </select>
            </div>

            <div>
              <label style={{ fontWeight: 700, fontSize: 14 }}>Sort</label>
              <select
                value={sortMode}
                onChange={(e) => setSortMode(e.target.value)}
                style={{
                  marginTop: 8,
                  width: "100%",
                  padding: 12,
                  borderRadius: 12,
                  border: "1px solid #cbd5e1",
                  boxSizing: "border-box",
                }}
              >
                <option value="Severity High to Low">Severity High to Low</option>
                <option value="Severity Low to High">Severity Low to High</option>
              </select>
            </div>
          </div>
        </SectionCard>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
          <SectionCard title="Risk Distribution">
            <div style={{ height: 320 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={distributionData} dataKey="value" nameKey="name" outerRadius={110} label>
                    {distributionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </SectionCard>

          <SectionCard title="Severity Ranking">
            <div style={{ height: 320 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={severityData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="patient" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Bar dataKey="severity" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </SectionCard>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1.2fr 0.8fr", gap: 24 }}>
          <SectionCard title="Patient Risk Queue">
            {loading ? (
              <div style={softBlockStyle()}>Loading patient queue from backend...</div>
            ) : (
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
                  <thead>
                    <tr style={{ background: "#f8fafc", color: "#475569" }}>
                      <th style={{ textAlign: "left", padding: 12 }}>Patient</th>
                      <th style={{ textAlign: "left", padding: 12 }}>Age / Gender</th>
                      <th style={{ textAlign: "left", padding: 12 }}>Alert Level</th>
                      <th style={{ textAlign: "left", padding: 12 }}>Severity</th>
                      <th style={{ textAlign: "left", padding: 12 }}>Contributors</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredRecords.map((item) => (
                      <tr key={item.patient.patient_id}>
                        <td style={{ padding: 12, borderBottom: "1px solid #f1f5f9", fontWeight: 700 }}>
                          P-{item.patient.patient_id}
                        </td>
                        <td style={{ padding: 12, borderBottom: "1px solid #f1f5f9" }}>
                          {item.patient.age} · {item.patient.gender}
                        </td>
                        <td style={{ padding: 12, borderBottom: "1px solid #f1f5f9" }}>
                          <span
                            style={{
                              ...badgeStyle(item.flags.alert_level),
                              borderRadius: 999,
                              padding: "6px 10px",
                              fontWeight: 700,
                            }}
                          >
                            {item.flags.alert_level}
                          </span>
                        </td>
                        <td style={{ padding: 12, borderBottom: "1px solid #f1f5f9", fontWeight: 700 }}>
                          {item.flags.severity_score}/100
                        </td>
                        <td style={{ padding: 12, borderBottom: "1px solid #f1f5f9" }}>
                          {(item.flags.contributors || []).slice(0, 3).join(", ") || "None"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {!filteredRecords.length && (
                  <div style={{ marginTop: 14, ...softBlockStyle() }}>
                    No patients match the current filters.
                  </div>
                )}
              </div>
            )}
          </SectionCard>

          <SectionCard title="Priority Cases">
            <div style={{ display: "grid", gap: 14 }}>
              {priorityCases.map((item) => (
                <div key={item.patient.patient_id} style={softBlockStyle()}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                    <div style={{ fontWeight: 800 }}>P-{item.patient.patient_id}</div>
                    <span
                      style={{
                        ...badgeStyle(item.flags.alert_level),
                        borderRadius: 999,
                        padding: "5px 10px",
                        fontSize: 13,
                        fontWeight: 700,
                      }}
                    >
                      {item.flags.alert_level}
                    </span>
                  </div>

                  <div style={{ marginTop: 8, color: "#475569", fontSize: 14 }}>
                    Severity: <b>{item.flags.severity_score}/100</b>
                  </div>

                  <div style={{ marginTop: 8, color: "#475569", fontSize: 14 }}>
                    Recommended action:{" "}
                    <b>
                      {item.flags.alert_level.includes("High")
                        ? "Clinical review"
                        : item.flags.alert_level.includes("Moderate")
                        ? "Preventive follow-up"
                        : "Routine monitoring"}
                    </b>
                  </div>

                  <div style={{ marginTop: 10, display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {(item.flags.contributors || []).slice(0, 3).map((factor) => (
                      <span
                        key={factor}
                        style={{
                          background: "#eef2ff",
                          color: "#3730a3",
                          borderRadius: 999,
                          padding: "5px 9px",
                          fontSize: 12,
                          fontWeight: 600,
                        }}
                      >
                        {factor}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
          <SectionCard title="System Workflow">
            <div style={{ display: "grid", gap: 12 }}>
              <div style={softBlockStyle()}>
                <b>1. Dataset Intake</b>
                <div style={{ marginTop: 4, color: "#64748b", fontSize: 14 }}>
                  React requests patient records from FastAPI.
                </div>
              </div>
              <div style={softBlockStyle()}>
                <b>2. Batch Risk Analysis</b>
                <div style={{ marginTop: 4, color: "#64748b", fontSize: 14 }}>
                  FastAPI runs the grounded risk engine across multiple patient records.
                </div>
              </div>
              <div style={softBlockStyle()}>
                <b>3. Operations Dashboard</b>
                <div style={{ marginTop: 4, color: "#64748b", fontSize: 14 }}>
                  Risk counts, severity rankings, and priority cases update from backend output.
                </div>
              </div>
              <div style={softBlockStyle()}>
                <b>4. Clinical Workbench Handoff</b>
                <div style={{ marginTop: 4, color: "#64748b", fontSize: 14 }}>
                  High-priority records can be reviewed in the Streamlit multi-agent workbench.
                </div>
              </div>
            </div>
          </SectionCard>

          <SectionCard title="Operational Summary">
            <div style={{ display: "grid", gap: 14, fontSize: 15, color: "#475569", lineHeight: 1.7 }}>
              <p>
                This dashboard provides an operations-level monitoring layer for chronic disease early warning alerts.
                It uses the FastAPI backend to analyze multiple patient records and prioritize review needs.
              </p>

              <div style={{ ...softBlockStyle(), background: "#ecfdf5", color: "#166534", fontWeight: 700 }}>
                Current queue status: {highRiskCount} high-risk, {moderateRiskCount} moderate-risk,
                and {lowRiskCount} low-risk patients.
              </div>

              <div style={{ ...softBlockStyle(), background: "#eff6ff", color: "#1d4ed8", fontWeight: 700 }}>
                React dashboard role: population-level operations monitoring.
                Streamlit role: detailed patient-level multi-agent clinical analysis.
              </div>
            </div>
          </SectionCard>
        </div>
      </div>
    </div>
  );
}