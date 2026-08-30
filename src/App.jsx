import { useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  Polygon,
  Popup
} from "react-leaflet";

import "leaflet/dist/leaflet.css";
import "./App.css";

// Backend URL
// Local: http://127.0.0.1:8000
// Netlify: set VITE_API_URL to your deployed Render backend URL
const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";


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
  // Get heatmap, risk and agent data
  // --------------------------------------------------

  useEffect(() => {

    Promise.all([
      fetch(`${API_URL}/api/heatmap`),
      fetch(`${API_URL}/api/risk`),
      fetch(`${API_URL}/api/agent`)
    ])

      .then(async ([heatmapResponse, riskResponse, agentResponse]) => {

        if (!heatmapResponse.ok) {
          throw new Error(
            `Heatmap request failed (${heatmapResponse.status})`
          );
        }

        if (!riskResponse.ok) {
          throw new Error(
            `Risk request failed (${riskResponse.status})`
          );
        }

        if (!agentResponse.ok) {
          throw new Error(
            `Agent request failed (${agentResponse.status})`
          );
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

        console.error("HeatShield API error:", err);

        setError(err.message);

      });

  }, []);


  // --------------------------------------------------
  // Analyze heat risk
  // --------------------------------------------------

  function analyzeHeatRisk() {

    setAnalyzing(true);

    setError(null);


    fetch(`${API_URL}/api/analysis`)

      .then((response) => {

        if (!response.ok) {

          throw new Error(
            `Analysis request failed (${response.status})`
          );

        }

        return response.json();

      })

      .then((result) => {

        setAnalysis(result);

      })

      .catch((err) => {

        console.error("Analysis error:", err);

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

        {error ? (

          <p>
            Unable to load heat intelligence: {error}
          </p>

        ) : (

          <p>
            Loading heat intelligence...
          </p>

        )}

      </div>

    );
  }


  // --------------------------------------------------
  // Heatmap features
  // --------------------------------------------------

  const features =
    data.heatmap?.features || [];


  const analysisData =
    analysis?.analysis;


  // --------------------------------------------------
  // Main UI
  // --------------------------------------------------

  return (

    <div className="app">


      {/* HEADER */}

      <header className="header">

        <div>

          <h1>
            🔥 HeatShield AI
          </h1>

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


        {/* RISK ASSESSMENT */}

        <section className="risk-section">

          <div className="section-title">

            <h2>
              ⚠️ Heat Risk Assessment
            </h2>

            <p>
              AI-powered risk analysis of the monitored area
            </p>

          </div>


          {riskData && (

            <div className="risk-grid">


              <div className="risk-card">

                <span>⚠️</span>

                <h3>
                  Overall Risk
                </h3>

                <strong>
                  {riskData.risk.risk_level}
                </strong>

              </div>


              <div className="risk-card">

                <span>🎯</span>

                <h3>
                  Risk Score
                </h3>

                <strong>
                  {riskData.risk.risk_score}/100
                </strong>

              </div>


              <div className="risk-card">

                <span>🔥</span>

                <h3>
                  Hotspots
                </h3>

                <strong>
                  {riskData.analysis.hotspot_count}
                </strong>

              </div>


              <div className="risk-card">

                <span>📊</span>

                <h3>
                  Hotspot Area
                </h3>

                <strong>
                  {riskData.risk.hotspot_percentage}%
                </strong>

              </div>


            </div>

          )}

        </section>


        {/* RISK REASONS */}

        {riskData && (

          <section className="reasons-section">

            <div className="section-title">

              <h2>
                🧠 Why is this area at risk?
              </h2>

            </div>


            <div className="reasons-card">

              {riskData.risk.reasons.map(
                (reason, index) => (

                  <div
                    className="reason"
                    key={index}
                  >

                    <span>✓</span>

                    <p>
                      {reason}
                    </p>

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
                getTemperatureColor(temperature);


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

                    Average:{" "}
                    {temperature.toFixed(2)}°C

                    <br />

                    Minimum:{" "}
                    {feature.properties.min_temperature.toFixed(2)}°C

                    <br />

                    Maximum:{" "}
                    {feature.properties.max_temperature.toFixed(2)}°C

                  </Popup>


                </Polygon>

              );

            })}


          </MapContainer>


        </section>


        {/* AI AGENT */}

        <section className="agent-section">


          <div className="section-title">

            <h2>
              🤖 HeatShield AI Agent
            </h2>

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

                      <span>
                        ✓
                      </span>

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


        {/* OPTIONAL ANALYSIS BUTTON */}

        {analysisData && (

          <section className="analysis-section">

            <div className="section-title">

              <h2>
                📊 AI Analysis
              </h2>

            </div>

            <div className="analysis-card">

              <pre>
                {JSON.stringify(
                  analysisData,
                  null,
                  2
                )}
              </pre>

            </div>

          </section>

        )}


      </main>

    </div>

  );
}


export default App;