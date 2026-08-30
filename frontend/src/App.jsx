import { useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  Polygon,
  Popup
} from "react-leaflet";

import "leaflet/dist/leaflet.css";
import "./App.css";

function getTemperatureColor(temp) {
  if (temp < 25) return "#2ecc71";
  if (temp < 30) return "#f1c40f";
  if (temp < 35) return "#e67e22";
  return "#e74c3c";
}

function App() {
  const [data, setData] = useState(null);
  const [riskData, setRiskData] = useState(null);
  const [agentData, setAgentData] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);

// --------------------------------------------------
  // Get heatmap
  // --------------------------------------------------

  useEffect(() => {
    Promise.all([
      fetch("/api/heatmap"),
      fetch("/api/risk"),
      fetch("/api/agent")
    ])
      .then(async ([heatmapResponse, riskResponse, agentResponse]) => {
        if (!heatmapResponse.ok) {
          throw new Error("Failed to fetch heatmap data");
        }

        if (!riskResponse.ok) {
          throw new Error("Failed to fetch risk data");
        }

        if (!agentResponse.ok) {
          throw new Error("Failed to fetch agent data");
        }

        const heatmap = await heatmapResponse.json();
        const risk = await riskResponse.json();
        const agent = await agentResponse.json();
        return {
          heatmap,
          risk,
          agent
        };
      })
      .then((result) => {
        setData(result.heatmap);
        setRiskData(result.risk);
        setAgentData(result.agent);
      })
      .catch((err) => {
        setError(err.message);
      });
  }, []);

  // --------------------------------------------------
  // Analyze heat risk
  // --------------------------------------------------

  function analyzeHeatRisk() {
    setAnalyzing(true);
    setError(null);

    fetch("/api/analysis")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to analyze heat risk");
        }

        return response.json();
      })
      .then((result) => {
        setAnalysis(result);
      })
      .catch((err) => {
        setError(err.message);
      })
      .finally(() => {
        setAnalyzing(false);
      });
  }

  // --------------------------------------------------
  // Loading
  // --------------------------------------------------

  if (!data) {
    return (
      <div className="loading">
        🔥 HeatShield AI
        <p>Loading heat intelligence...</p>
      </div>
    );
  }

  const features = data.heatmap?.features || [];

  const analysisData = analysis?.analysis;

  return (
    <div className="app">

      {/* HEADER */}

      <header className="header">

        <div>
          <h1>🔥 HeatShield AI</h1>

          <p>
            AI-powered Urban Heat Intelligence
          </p>
        </div>

        <div className="status">
          ● LIVE
        </div>

      </header>


      <main>

        {/* ERROR */}

        {error && (
          <div className="error">
            {error}
          </div>
        )}


        {/* TEMPERATURE CARDS */}

        <section className="cards">

          <div className="card">
            <span>🌡️</span>

            <h3>
              Average Temperature
            </h3>

            <strong>
              {data.temperature.average.toFixed(2)}°C
            </strong>
          </div>


          <div className="card">
            <span>⬇️</span>

            <h3>
              Minimum
            </h3>

            <strong>
              {data.temperature.minimum.toFixed(2)}°C
            </strong>
          </div>


          <div className="card">
            <span>⬆️</span>

            <h3>
              Maximum
            </h3>

            <strong>
              {data.temperature.maximum.toFixed(2)}°C
            </strong>
          </div>


          <div className="card">
            <span>🧩</span>

            <h3>
              Tiles Analyzed
            </h3>

            <strong>
              {data.tiles_analyzed}
            </strong>
          </div>

        </section>

<section className="risk-section">

  <div className="section-title">
    <h2>⚠️ Heat Risk Assessment</h2>
    <p>AI-powered risk analysis of the monitored area</p>
  </div>

  {riskData && (
    <div className="risk-grid">

      <div className="risk-card">

        <span>⚠️</span>

        <h3>Overall Risk</h3>

        <strong>
          {riskData.risk.risk_level}
        </strong>

      </div>


      <div className="risk-card">

        <span>🎯</span>

        <h3>Risk Score</h3>

        <strong>
          {riskData.risk.risk_score}/100
        </strong>

      </div>


      <div className="risk-card">

        <span>🔥</span>

        <h3>Hotspots</h3>

        <strong>
          {riskData.analysis.hotspot_count}
        </strong>

      </div>


      <div className="risk-card">

        <span>📊</span>

        <h3>Hotspot Area</h3>

        <strong>
          {riskData.risk.hotspot_percentage}%
        </strong>

      </div>

    </div>
  )}

</section>

{riskData && (
  <section className="reasons-section">

    <div className="section-title">
      <h2>🧠 Why is this area at risk?</h2>
    </div>

    <div className="reasons-card">

      {riskData.risk.reasons.map(
        (reason, index) => (
          <div
            className="reason"
            key={index}
          >
            <span>✓</span>
            <p>{reason}</p>
          </div>
        )
      )}

    </div>

  </section>
)}

        {/* MAP */}

        <section className="map-section">

          <div className="section-title">

            <h2>
              🗺️ Urban Heat Map
            </h2>

            <p>
              {data.location.city},{" "}
              {data.location.state},{" "}
              {data.location.country}
            </p>

          </div>


          <MapContainer
            center={[40.711, -74.01]}
            zoom={15}
            className="map"
          >

            <TileLayer
              attribution="&copy; OpenStreetMap contributors"
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />


            {features.map((feature) => {

              const coordinates =
                feature.geometry.coordinates[0];

              const positions =
                coordinates.map(
                  ([longitude, latitude]) => [
                    latitude,
                    longitude
                  ]
                );


              const temperature =
                feature.properties.average_temperature;


              const color =
                getTemperatureColor(
                  temperature
                );


              return (
                <Polygon
                  key={feature.id}
                  positions={positions}
                  pathOptions={{
                    color: color,
                    fillColor: color,
                    fillOpacity: 0.55
                  }}
                >

                  <Popup>

                    <strong>
                      Heat Tile #{feature.id}
                    </strong>

                    <br />

                    Average:
                    {" "}
                    {temperature.toFixed(2)}°C

                    <br />

                    Minimum:
                    {" "}
                    {feature.properties.min_temperature.toFixed(2)}°C

                    <br />

                    Maximum:
                    {" "}
                    {feature.properties.max_temperature.toFixed(2)}°C

                  </Popup>

                </Polygon>
              );
            })}

          </MapContainer>

        </section>


        {/* AGENT */}

  <section className="agent-section">

  <div className="section-title">
    <h2>🤖 HeatShield AI Agent</h2>

    <p>
      Automated heat-risk assessment and response planning
    </p>
  </div>

  {agentData && (
    <div className="agent-card">

      <div className="agent-header">

        <div>
          <h3>
            Agent Assessment
          </h3>

          <p>
            {agentData.agent.assessment}
          </p>
        </div>

        <div className="priority-badge">
          {agentData.agent.priority}
        </div>

      </div>


      <div className="agent-status">

        <span>
          ● {agentData.agent.agent_status}
        </span>

        <span>
          {agentData.agent.automation_ready
            ? "⚡ AUTOMATION READY"
            : "MONITORING MODE"}
        </span>

      </div>


      <div className="actions">

        <h3>
          Recommended Actions
        </h3>

        {agentData.agent.recommended_actions.map(
          (action, index) => (

            <div
              className="action"
              key={index}
            >

              <span>✓</span>

              <p>
                {action}
              </p>

            </div>

          )
        )}

      </div>

    </div>
  )}

</section>

      </main>

    </div>
  );
}

export default App;