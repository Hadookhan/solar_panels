import { useMemo, useState } from "react";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ScatterChart,
    Scatter,
    ZAxis,
} from "recharts";

import { getBestHouseOrientation } from "./api/api";
import "./App.css";

const SYSTEMS = [
    {
        house_id: "House 1",
        inverter_kw: 4.0,
        arrays: [
            { array_id: "Panel 1", installed_capacity_kwp: 4.0 },
            { array_id: "Panel 2", installed_capacity_kwp: 1.5 },
            { array_id: "Panel 3", installed_capacity_kwp: 0.75 },
        ],
    },
    {
        house_id: "House 2",
        inverter_kw: 2.2,
        arrays: [
            { array_id: "Panel 1", installed_capacity_kwp: 2.4 },
        ],
    },
    {
        house_id: "Reactor",
        inverter_kw: 22.0,
        arrays: [
            { array_id: "Panel 1", installed_capacity_kwp: 16.35 },
            { array_id: "Panel 2", installed_capacity_kwp: 16.35 },
        ],
    },
];

const BASIC_INFO = [
    {
        name: "House 1",
        inverter: "4.0 kW",
        arrays: ["4.0 kWp", "1.5 kWp", "0.75 kWp"],
    },
    {
        name: "House 2",
        inverter: "2.2 kW",
        arrays: ["2.4 kWp"],
    },
    {
        name: "Reactor",
        inverter: "22 kW",
        arrays: ["16.35 kWp", "16.35 kWp"],
    },
];

function App() {
    const [darkMode, setDarkMode] = useState(true);
    const [cloudy, setCloudy] = useState(false);
    const [isDay, setIsDay] = useState(true);
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState([]);
    const [error, setError] = useState("");

    async function handlePredict() {
        setLoading(true);
        setError("");

        const weather = {
            latitude: 50.75,
            longitude: 4.5,
            hour: isDay ? 12 : 0,
            day_of_year: 181,
            temperature_2m: 20.5,
            cloud_cover: cloudy ? 100 : 0,
            is_day: isDay ? 1 : 0,
            wind_speed_10m: 5.2,
            shortwave_radiation: isDay ? (cloudy ? 180 : 650) : 0,
            direct_radiation: isDay ? (cloudy ? 50 : 500) : 0,
            diffuse_radiation: isDay ? (cloudy ? 130 : 120) : 0,
        };

        try {
            const responses = await Promise.all(
                SYSTEMS.map((system) =>
                    getBestHouseOrientation({
                        ...system,
                        weather,
                    })
                )
            );

            setResults(responses);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }

    const chartData = useMemo(() => {
        return results.map((system) => {
            const total = system.arrays.reduce(
                (sum, arr) => sum + arr.predicted_energy_kw,
                0
            );

            return {
                name: system.house_id,
                energy: Number(total.toFixed(3)),
            };
        });
    }, [results]);

    const scatterData = useMemo(() => {
        return results.flatMap((system) =>
            system.arrays.map((array) => ({
                system: system.house_id,
                array: array.array_id,
                tilt: array.tilt,
                azimuth: array.azimuth,
                energy: Number(array.predicted_energy_kw.toFixed(3)),
            }))
        );
    }, [results]);

    const stats = useMemo(() => {
        const totals = chartData.map((x) => x.energy);
        const totalEnergy = totals.reduce((a, b) => a + b, 0);
        const best = chartData.reduce(
            (max, item) => (item.energy > max.energy ? item : max),
            { name: "N/A", energy: 0 }
        );

        return {
            totalEnergy: totalEnergy.toFixed(3),
            averageEnergy:
                totals.length > 0 ? (totalEnergy / totals.length).toFixed(3) : "0.000",
            bestSystem: best.name,
            bestEnergy: best.energy.toFixed(3),
        };
    }, [chartData]);

    return (
        <main className={darkMode ? "app dark" : "app"}>
          <div className="page-layout">
              <aside className="sidebar">
                  <h2>Initial Values</h2>
                  <p className="muted">Location: Belgium</p>

                  {BASIC_INFO.map((item) => (
                      <div className="info-card" key={item.name}>
                          <h3>{item.name}</h3>
                          <p>Inverter: {item.inverter}</p>
                          <p>Panels:</p>
                          <ul>
                              {item.arrays.map((array, index) => (
                                  <li key={index}>{array}</li>
                              ))}
                          </ul>
                      </div>
                  ))}
              </aside>

              <div className="main-content">
                  <nav className="navbar">
                      <div>
                          <h1>Solar Panel Optimiser</h1>
                      </div>

                      <button className="toggle-btn" onClick={() => setDarkMode(!darkMode)}>
                          {darkMode ? "Dark Mode" : "Light Mode"}
                      </button>
                  </nav>

                  <section className="panel controls">
                      <h2>Settings</h2>

                      <div className="toggles">
                          <label className="switch-row">
                              <input
                                  type="checkbox"
                                  checked={cloudy}
                                  onChange={(e) => setCloudy(e.target.checked)}
                              />
                              <span>Cloud Coverage is {cloudy ? "On" : "Off"}</span>
                          </label>

                          <label className="switch-row">
                              <input
                                  type="checkbox"
                                  checked={isDay}
                                  onChange={(e) => setIsDay(e.target.checked)}
                              />
                              <span>{isDay ? "Time: Day" : "Time: Night"}</span>
                          </label>
                      </div>

                      <button className="primary-btn" onClick={handlePredict} disabled={loading}>
                          {loading ? "Calculating..." : "Predict all systems"}
                      </button>

                      {error && <p className="error">{error}</p>}
                  </section>

                  {results.length > 0 && (
                      <>
                          <section className="stats-grid">
                              <div className="stat-card">
                                  <span>Total predicted output</span>
                                  <strong>{stats.totalEnergy} kW</strong>
                              </div>

                              <div className="stat-card">
                                  <span>Average system output</span>
                                  <strong>{stats.averageEnergy} kW</strong>
                              </div>

                              <div className="stat-card">
                                  <span>Best system</span>
                                  <strong>{stats.bestSystem}</strong>
                              </div>

                              <div className="stat-card">
                                  <span>Best system output</span>
                                  <strong>{stats.bestEnergy} kW</strong>
                              </div>
                          </section>

                          <section className="panel">
                              <h2>Energy Output by System</h2>

                              <div className="chart-box">
                                  <ResponsiveContainer width="100%" height={320}>
                                      <BarChart data={chartData}>
                                          <CartesianGrid strokeDasharray="3 3" />
                                          <XAxis dataKey="name" />
                                          <YAxis />
                                          <Tooltip />
                                          <Bar dataKey="energy" />
                                      </BarChart>
                                  </ResponsiveContainer>
                              </div>
                          </section>

                          <section className="panel">
                              <h2>Orientation vs Predicted Energy</h2>
                              <p className="muted">
                                  Each point represents an array. The graph shows whether higher energy predictions are associated with particular tilt and rotation choices.
                              </p>

                              <div className="chart-box">
                                  <ResponsiveContainer width="100%" height={320}>
                                      <ScatterChart>
                                          <CartesianGrid strokeDasharray="3 3" />
                                          <XAxis
                                              type="number"
                                              dataKey="tilt"
                                              name="Tilt"
                                              unit="°"
                                          />
                                          <YAxis
                                              type="number"
                                              dataKey="azimuth"
                                              name="Rotation"
                                              unit="°"
                                          />
                                          <ZAxis
                                              type="number"
                                              dataKey="energy"
                                              range={[80, 350]}
                                              name="Energy"
                                              unit=" kW"
                                          />
                                          <Tooltip cursor={{ strokeDasharray: "3 3" }} />
                                          <Scatter
                                              name="Predicted output"
                                              data={scatterData}
                                          />
                                      </ScatterChart>
                                  </ResponsiveContainer>
                              </div>
                          </section>

                          <section className="systems-grid">
                              {results.map((system) => (
                                  <div className="panel" key={system.house_id}>
                                      <h2>{system.house_id}</h2>

                                      <div className="array-list">
                                          {system.arrays.map((array) => (
                                              <div className="array-card" key={array.array_id}>
                                                  <h3>{array.array_id}</h3>
                                                  <p>Best tilt: {array.tilt}°</p>
                                                  <p>Best rotation: {array.azimuth}°</p>
                                                  <p>
                                                      Output:{" "}
                                                      {array.predicted_energy_kw.toFixed(3)} kW
                                                  </p>
                                              </div>
                                          ))}
                                      </div>
                                  </div>
                              ))}
                          </section>
                      </>
                    )}
                </div>
            </div>
        </main>
    );
}

export default App;