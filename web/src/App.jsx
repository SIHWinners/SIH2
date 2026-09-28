import React, { useState, useEffect } from 'react';
import {
  Activity,
  AlertTriangle,
  Bot,
  CloudSun,
  Download,
  Gauge,
  Layers,
  Play,
  RefreshCw,
  Sliders,
  TrendingUp,
  Zap,
  CheckCircle2,
  FileText,
  Flame,
  Cpu
} from 'lucide-react';

import SrpSchematic from './components/SrpSchematic';
import CssSchematic from './components/CssSchematic';
import DynoCardCanvas from './components/DynoCardCanvas';
import ShapWaterfall from './components/ShapWaterfall';
import CopilotModal from './components/CopilotModal';
import ErrorBoundary from './components/ErrorBoundary';
import { apiUrl } from './api';

export default function App() {
  const [wells, setWells] = useState([]);
  const [selectedWell, setSelectedWell] = useState('SRP-001');
  const [activeTab, setActiveTab] = useState('command_center');
  
  // Dashboard & Telemetry State
  const [dashboardData, setDashboardData] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [telemetry, setTelemetry] = useState([]);
  const [dynoCard, setDynoCard] = useState(null);
  const [explainData, setExplainData] = useState(null);
  const [cssData, setCssData] = useState(null);
  const [weather, setWeather] = useState(null);
  
  // Sandbox State
  const [sandboxCasing, setSandboxCasing] = useState(205);
  const [sandboxTubing, setSandboxTubing] = useState(140);
  const [sandboxLoad, setSandboxLoad] = useState(225);
  const [sandboxSpeed, setSandboxSpeed] = useState(10.5);
  const [sandboxTemp, setSandboxTemp] = useState(65);
  const [simResult, setSimResult] = useState(null);
  const [vfdToast, setVfdToast] = useState(false);

  // Copilot Drawer & Loading indicators
  const [copilotOpen, setCopilotOpen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [loadingDetails, setLoadingDetails] = useState(false);

  // Initial Load
  useEffect(() => {
    fetchInitialData();
  }, []);

  // Fetch Well-specific data when selectedWell changes
  useEffect(() => {
    if (selectedWell) {
      fetchWellDetails(selectedWell);
    }
  }, [selectedWell]);

  const fetchInitialData = async () => {
    setIsRefreshing(true);
    try {
      const [wellsRes, dashRes, alertsRes, weatherRes] = await Promise.all([
        fetch(apiUrl('/api/v1/wells')).then(r => r.ok ? r.json() : []).catch(() => []),
        fetch(apiUrl('/api/v1/dashboard')).then(r => r.ok ? r.json() : []).catch(() => []),
        fetch(apiUrl('/api/v1/alerts')).then(r => r.ok ? r.json() : []).catch(() => []),
        fetch(apiUrl('/api/v1/weather')).then(r => r.ok ? r.json() : null).catch(() => null),
      ]);
      setWells(Array.isArray(wellsRes) ? wellsRes : []);
      setDashboardData(Array.isArray(dashRes) ? dashRes : []);
      setAlerts(Array.isArray(alertsRes) ? alertsRes : []);
      if (weatherRes) setWeather(weatherRes);
    } catch (e) {
      console.error('Error loading initial data:', e);
    } finally {
      setIsRefreshing(false);
    }
  };

  const fetchWellDetails = async (wellId) => {
    setLoadingDetails(true);
    try {
      // 1. Fetch telemetry independently
      const telPromise = fetch(apiUrl(`/api/v1/telemetry/${wellId}?minutes=360`))
        .then(r => r.ok ? r.json() : [])
        .then(telRes => {
          if (Array.isArray(telRes)) {
            setTelemetry(telRes);
            if (telRes.length > 0) {
              const last = telRes[telRes.length - 1];
              setSandboxCasing(Number(last.casing_pressure) || 205);
              setSandboxTubing(Number(last.tubing_pressure) || 140);
              setSandboxLoad(Number(last.polished_rod_load) || 225);
              setSandboxSpeed(Number(last.stroke_speed) || 10.5);
              setSandboxTemp(Number(last.motor_temp) || 65);
              runSimulation(wellId, last.casing_pressure, last.tubing_pressure, last.polished_rod_load, last.stroke_speed, last.motor_temp);
            }
          }
        })
        .catch(err => {
          console.warn('Telemetry fetch error:', err);
          setTelemetry([]);
        });

      // 2. Fetch dyno card independently
      const dynoPromise = fetch(apiUrl(`/api/v1/dyno-card/${wellId}`))
        .then(r => r.ok ? r.json() : null)
        .then(data => {
          if (data && Array.isArray(data.points)) {
            setDynoCard(data);
          } else {
            setDynoCard(null);
          }
        })
        .catch(() => setDynoCard(null));

      // 3. Fetch SHAP explainability independently
      const expPromise = fetch(apiUrl(`/api/v1/explain/${wellId}`))
        .then(r => r.ok ? r.json() : null)
        .then(data => {
          if (data && Array.isArray(data.top_drivers)) {
            setExplainData(data);
          } else {
            setExplainData(null);
          }
        })
        .catch(() => setExplainData(null));

      // 4. Fetch CSS status if applicable
      const cssPromise = wellId.startsWith('CSS')
        ? fetch(apiUrl(`/api/v1/css-status/${wellId}`))
            .then(r => r.ok ? r.json() : null)
            .then(data => setCssData(data))
            .catch(() => setCssData(null))
        : Promise.resolve(setCssData(null));

      await Promise.allSettled([telPromise, dynoPromise, expPromise, cssPromise]);
    } catch (e) {
      console.error('Error fetching well details:', e);
    } finally {
      setLoadingDetails(false);
    }
  };

  const runSimulation = async (wellId, casing, tubing, load, speed, temp) => {
    try {
      const resp = await fetch(apiUrl('/api/v1/predict/simulate'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          well_id: wellId,
          casing_pressure: parseFloat(casing) || 205,
          tubing_pressure: parseFloat(tubing) || 140,
          polished_rod_load: parseFloat(load) || 225,
          stroke_speed: parseFloat(speed) || 10.5,
          motor_temp: parseFloat(temp) || 65,
        }),
      });
      const data = await resp.json();
      setSimResult(data);
    } catch (e) {
      console.error('Simulation error:', e);
    }
  };

  const handleSimulateTick = async () => {
    try {
      await fetch(apiUrl('/api/v1/simulator/step'), { method: 'POST' });
      fetchInitialData();
      if (selectedWell) fetchWellDetails(selectedWell);
    } catch (e) {
      console.error('Tick error:', e);
    }
  };

  const handleAcknowledgeAlert = async (id) => {
    try {
      await fetch(apiUrl(`/api/v1/alerts/${id}/acknowledge`), { method: 'POST' });
      const updated = await fetch(apiUrl('/api/v1/alerts')).then(r => r.json());
      setAlerts(Array.isArray(updated) ? updated : []);
    } catch (e) {
      console.error('Ack error:', e);
    }
  };

  const handleExportReport = async () => {
    try {
      const resp = await fetch(apiUrl(`/api/v1/report/${selectedWell}`));
      const data = await resp.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${data.report_id || selectedWell}_report.json`;
      a.click();
    } catch (e) {
      alert('Error generating compliance report.');
    }
  };

  const applyPreset = (casing, tubing, load, speed, temp) => {
    setSandboxCasing(casing);
    setSandboxTubing(tubing);
    setSandboxLoad(load);
    setSandboxSpeed(speed);
    setSandboxTemp(temp);
    runSimulation(selectedWell, casing, tubing, load, speed, temp);
  };

  // Safe aggregated KPIs
  const safeDashboard = Array.isArray(dashboardData) ? dashboardData : [];
  const safeWells = Array.isArray(wells) ? wells : [];
  const safeAlerts = Array.isArray(alerts) ? alerts : [];
  const safeTelemetry = Array.isArray(telemetry) ? telemetry : [];

  const totalFlow = safeDashboard.reduce((acc, w) => acc + (Number(w?.latest_flow_rate) || 0), 0);
  const healthyCount = safeDashboard.filter(w => w?.status === 'healthy').length;
  const warningCount = safeDashboard.filter(w => w?.status === 'warning').length;
  const criticalCount = safeDashboard.filter(w => w?.status === 'critical').length;
  const isCss = selectedWell ? selectedWell.startsWith('CSS') : false;

  const currentWellLatest = safeTelemetry.length > 0 ? safeTelemetry[safeTelemetry.length - 1] : {};

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Header / SCADA Navbar */}
      <header style={{
        background: 'linear-gradient(135deg, #0b1329 0%, #0d1b3a 50%, #162a52 100%)',
        borderBottom: '1px solid rgba(245, 158, 11, 0.25)',
        padding: '16px 28px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '16px',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.5)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(14, 22, 38, 0.9) 100%)',
            border: '1.5px solid rgba(245, 158, 11, 0.5)',
            boxShadow: '0 0 15px rgba(245, 158, 11, 0.25)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L3 22h18L12 2z" />
              <path d="M12 8v14" />
              <path d="M7 16h10" />
              <circle cx="12" cy="5" r="1.5" fill="#38bdf8" stroke="#38bdf8" />
            </svg>
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h1 style={{
                fontSize: '19px',
                fontWeight: '800',
                letterSpacing: '-0.02em',
                background: 'linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}>
                OIL INDIA LIMITED
              </h1>
              <span className="badge badge-gold" style={{ fontSize: '10px', letterSpacing: '0.5px' }}>
                SIH26120 PRODUCTION TWIN
              </span>
            </div>
            <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>Baghewala Heavy Oil Asset</span>
              <span style={{ color: '#475569' }}>•</span>
              <span style={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981', display: 'inline-block' }}></span>
                SCADA PLC Link: Connected
              </span>
            </div>
          </div>
        </div>

        {/* Right Action Bar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          {/* Weather Widget */}
          {weather && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              background: 'rgba(15, 23, 42, 0.65)',
              padding: '6px 12px',
              borderRadius: '8px',
              border: '1px solid rgba(255, 255, 255, 0.06)',
              fontSize: '12px',
              color: '#cbd5e1',
            }}>
              <CloudSun size={15} style={{ color: '#f59e0b' }} />
              <span>{weather.location}: <b>{weather.temp_c}°C</b></span>
              <span style={{ color: '#64748b' }}>•</span>
              <span style={{ color: '#94a3b8' }}>{weather.condition}</span>
            </div>
          )}

          {/* Simulate Step / Tick Button */}
          <button
            onClick={handleSimulateTick}
            className="btn btn-secondary"
            title="Step simulation forward by 1 interval"
            style={{ fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <Play size={13} style={{ color: '#10b981' }} />
            <span>Live SCADA Tick</span>
          </button>

          {/* Refresh Data Button */}
          <button
            onClick={() => {
              fetchInitialData();
              if (selectedWell) fetchWellDetails(selectedWell);
            }}
            className="btn btn-secondary"
            disabled={isRefreshing}
            style={{ fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <RefreshCw size={13} className={isRefreshing ? 'spin' : ''} />
            <span>Sync</span>
          </button>

          {/* Compliance Report Export */}
          <button
            onClick={handleExportReport}
            className="btn btn-secondary"
            style={{ fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <FileText size={13} style={{ color: '#38bdf8' }} />
            <span>Audit Report</span>
          </button>

          {/* AI Copilot Trigger */}
          <button
            onClick={() => setCopilotOpen(true)}
            className="btn btn-primary"
            style={{ fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <Bot size={15} />
            <span>AI Operations Copilot</span>
          </button>
        </div>
      </header>

      {/* Sub-Header: Well Selector Bar & Tab Navigation */}
      <div style={{
        background: '#090e19',
        borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
        padding: '8px 28px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '12px',
      }}>
        {/* Wellhead Selection Pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', overflowX: 'auto', paddingBottom: '2px' }}>
          <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.5px', color: '#64748b', fontWeight: '700' }}>
            Wellhead:
          </span>
          <div style={{ display: 'flex', gap: '6px' }}>
            {safeWells.map((w) => {
              const wId = typeof w === 'string' ? w : (w?.well_id || 'SRP-001');
              const isSelected = selectedWell === wId;
              const wellDash = safeDashboard.find(d => d?.well_id === wId);
              const status = wellDash?.status || 'healthy';
              const isCssWell = wId.startsWith('CSS');

              return (
                <button
                  key={wId}
                  onClick={() => setSelectedWell(wId)}
                  style={{
                    background: isSelected ? 'rgba(245, 158, 11, 0.2)' : 'rgba(255, 255, 255, 0.03)',
                    border: isSelected ? '1px solid #f59e0b' : '1px solid rgba(255, 255, 255, 0.06)',
                    color: isSelected ? '#fbbf24' : '#cbd5e1',
                    padding: '5px 12px',
                    borderRadius: '6px',
                    fontSize: '12px',
                    fontWeight: '600',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                  }}
                >
                  <span style={{
                    width: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    background: status === 'critical' ? '#ef4444' : status === 'warning' ? '#f59e0b' : '#10b981',
                  }}></span>
                  <span>{wId}</span>
                  <span style={{ fontSize: '10px', opacity: 0.7 }}>[{isCssWell ? 'CSS' : 'SRP'}]</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Navigation Tabs */}
        <div style={{ display: 'flex', gap: '6px' }}>
          {[
            { id: 'command_center', label: 'Field Command Center', icon: Activity },
            { id: 'srp_twin', label: 'SRP Digital Twin & Dyno', icon: Gauge },
            { id: 'css_twin', label: 'CSS Thermal Recovery', icon: Flame },
            { id: 'sandbox', label: 'What-If Simulation Sandbox', icon: Sliders },
            { id: 'scada_feed', label: 'SCADA Telemetry Stream', icon: Layers },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  background: isActive ? 'rgba(245, 158, 11, 0.2)' : 'transparent',
                  border: isActive ? '1px solid rgba(245, 158, 11, 0.4)' : '1px solid transparent',
                  color: isActive ? '#fbbf24' : '#94a3b8',
                  padding: '6px 14px',
                  borderRadius: '6px',
                  fontSize: '12px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  transition: 'all 0.15s ease',
                }}
              >
                <Icon size={14} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Content Area */}
      <main style={{ flex: 1, padding: '24px 28px', maxWidth: '1700px', margin: '0 auto', width: '100%' }}>
        {/* Top 4 KPI Metrics */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '24px' }}>
          <div className="glass-panel" style={{ padding: '16px 20px' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: '700' }}>Active Wells Monitored</div>
            <div style={{ fontSize: '26px', fontWeight: '800', color: '#f8fafc', fontFamily: 'JetBrains Mono', marginTop: '4px' }}>
              {safeWells.length} <span style={{ fontSize: '14px', color: '#38bdf8' }}>Wells</span>
            </div>
            <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>4 SRP Units • 3 CSS Thermal Units</div>
          </div>

          <div className="glass-panel" style={{ padding: '16px 20px' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: '700' }}>Total Field Flow Rate</div>
            <div style={{ fontSize: '26px', fontWeight: '800', color: '#f59e0b', fontFamily: 'JetBrains Mono', marginTop: '4px' }}>
              {totalFlow.toFixed(1)} <span style={{ fontSize: '14px' }}>BPD</span>
            </div>
            <div style={{ fontSize: '12px', color: '#10b981', marginTop: '4px' }}>▲ +3.8% over daily target</div>
          </div>

          <div className="glass-panel" style={{ padding: '16px 20px' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: '700' }}>Operating Health Index</div>
            <div style={{ display: 'flex', gap: '12px', marginTop: '6px', alignItems: 'baseline' }}>
              <span style={{ fontSize: '22px', fontWeight: '800', color: '#10b981', fontFamily: 'JetBrains Mono' }}>{healthyCount}</span>
              <span style={{ fontSize: '12px', color: '#94a3b8' }}>Healthy</span>
              <span style={{ fontSize: '22px', fontWeight: '800', color: '#f59e0b', fontFamily: 'JetBrains Mono' }}>{warningCount}</span>
              <span style={{ fontSize: '12px', color: '#94a3b8' }}>Warning</span>
              <span style={{ fontSize: '22px', fontWeight: '800', color: '#f43f5e', fontFamily: 'JetBrains Mono' }}>{criticalCount}</span>
              <span style={{ fontSize: '12px', color: '#94a3b8' }}>Critical</span>
            </div>
          </div>

          <div className="glass-panel" style={{ padding: '16px 20px' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', fontWeight: '700' }}>AI Optimization Target ({selectedWell})</div>
            <div style={{ fontSize: '26px', fontWeight: '800', color: '#38bdf8', fontFamily: 'JetBrains Mono', marginTop: '4px' }}>
              {(Number(currentWellLatest?.optimal_speed) || 10.5).toFixed(1)} <span style={{ fontSize: '14px' }}>SPM</span>
            </div>
            <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>
              Current: {(Number(currentWellLatest?.stroke_speed) || 10.0).toFixed(1)} SPM
            </div>
          </div>
        </div>

        {/* TAB 1: FIELD COMMAND CENTER */}
        {activeTab === 'command_center' && (
          <ErrorBoundary title="Field Command Center Engine">
            <div>
              {/* Active Alarms Bar if any */}
              {safeAlerts.some(a => a && !a.acknowledged) && (
                <div style={{
                  background: 'rgba(239, 68, 68, 0.12)',
                  border: '1px solid rgba(239, 68, 68, 0.35)',
                  borderRadius: '10px',
                  padding: '16px 20px',
                  marginBottom: '20px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}>
                  <div>
                    <div style={{ color: '#f87171', fontWeight: '700', fontSize: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <AlertTriangle size={18} />
                      <span>ACTIVE SCADA ALERT: {safeAlerts.find(a => a && !a.acknowledged)?.well_id} — {safeAlerts.find(a => a && !a.acknowledged)?.anomaly_type}</span>
                    </div>
                    <div style={{ fontSize: '13px', color: '#cbd5e1', marginTop: '4px' }}>
                      {safeAlerts.find(a => a && !a.acknowledged)?.description} • Action: <b>{safeAlerts.find(a => a && !a.acknowledged)?.recommended_action}</b>
                    </div>
                  </div>
                  <button
                    onClick={() => handleAcknowledgeAlert(safeAlerts.find(a => a && !a.acknowledged)?.id)}
                    className="btn btn-secondary"
                    style={{ fontSize: '12px', whiteSpace: 'nowrap' }}
                  >
                    <CheckCircle2 size={15} style={{ color: '#10b981' }} />
                    <span>Acknowledge</span>
                  </button>
                </div>
              )}

              {/* Field Wellhead Cluster Matrix */}
              <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#f8fafc', marginBottom: '14px' }}>
                Field Wellhead Cluster (Baghewala Heavy Oil Reservoir)
              </h3>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '24px' }}>
                {safeDashboard.map((well) => {
                  if (!well) return null;
                  const isSelected = selectedWell === well.well_id;
                  const statusColor = well.status === 'critical' ? '#ef4444' : well.status === 'warning' ? '#f59e0b' : '#10b981';

                  return (
                    <div
                      key={well.well_id || Math.random()}
                      onClick={() => setSelectedWell(well.well_id)}
                      className="glass-panel"
                      style={{
                        padding: '18px',
                        cursor: 'pointer',
                        borderLeft: `4px solid ${statusColor}`,
                        border: isSelected ? `2px solid #f59e0b` : undefined,
                        transition: 'all 0.2s ease',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: '800', fontSize: '17px', color: '#f8fafc' }}>{well.well_id}</span>
                        <span className="badge" style={{ background: `${statusColor}20`, color: statusColor, border: `1px solid ${statusColor}50` }}>
                          ● {(well.status || 'NORMAL').toUpperCase()}
                        </span>
                      </div>
                      <div style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>{well.well_name || well.well_id}</div>

                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '14px', fontSize: '12px' }}>
                        <div><span style={{ color: '#94a3b8' }}>Type:</span> <b>{well.well_type || (well.well_id?.startsWith('CSS') ? 'CSS' : 'SRP')}</b></div>
                        <div><span style={{ color: '#94a3b8' }}>Flow:</span> <b>{(Number(well.latest_flow_rate) || 0).toFixed(1)} BPD</b></div>
                        <div><span style={{ color: '#94a3b8' }}>Speed:</span> <b>{(Number(well.latest_stroke_speed) || 0).toFixed(1)} SPM</b></div>
                        <div><span style={{ color: '#94a3b8' }}>AI Target:</span> <b style={{ color: '#38bdf8' }}>{(Number(well.average_optimal_speed) || 0).toFixed(1)} SPM</b></div>
                        <div><span style={{ color: '#94a3b8' }}>Casing P:</span> <b>{(Number(well.latest_casing_pressure) || 0).toFixed(0)} psi</b></div>
                        <div><span style={{ color: '#94a3b8' }}>Rod Load:</span> <b>{(Number(well.latest_rod_load) || 0).toFixed(0)} kN</b></div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </ErrorBoundary>
        )}

        {/* TAB 2: SRP DIGITAL TWIN & DYNO CARD */}
        {activeTab === 'srp_twin' && (
          <ErrorBoundary title="SRP Digital Twin Telemetry Engine">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Animated Physical Schematic */}
              <SrpSchematic
                spm={Number(currentWellLatest?.stroke_speed) || 10.0}
                rodLoad={Number(currentWellLatest?.polished_rod_load) || 225.0}
                casingPressure={Number(currentWellLatest?.casing_pressure) || 205.0}
                tubingPressure={Number(currentWellLatest?.tubing_pressure) || 142.0}
                motorTemp={Number(currentWellLatest?.motor_temp) || 65.0}
                dynoType={currentWellLatest?.dyno_card_type || "Normal"}
              />

              {/* SCADA Loading State Banner */}
              {loadingDetails && (
                <div className="glass-panel" style={{
                  padding: '24px',
                  textAlign: 'center',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '10px',
                  border: '1px solid rgba(245, 158, 11, 0.4)',
                  background: 'linear-gradient(135deg, rgba(14, 22, 38, 0.95) 0%, rgba(26, 36, 61, 0.85) 100%)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <RefreshCw size={20} className="spin" style={{ color: '#f59e0b' }} />
                    <span style={{ fontSize: '13px', fontWeight: '700', color: '#f8fafc', letterSpacing: '0.4px', textTransform: 'uppercase' }}>
                      Acquiring SCADA Telemetry & Synthesizing Dynamometer Vectors for {selectedWell}...
                    </span>
                  </div>
                  <p style={{ fontSize: '12px', color: '#94a3b8', margin: 0 }}>
                    Computing surface load cell data, Gibbs wave equation downhole pump loops, and SHAP attribution models...
                  </p>
                </div>
              )}

              {/* Interactive Dynamometer Card */}
              {dynoCard && (
                <ErrorBoundary title="Dynamometer Vector Render Engine">
                  <DynoCardCanvas cardData={dynoCard} />
                </ErrorBoundary>
              )}

              {/* Fallback if not loading and no dyno card */}
              {!loadingDetails && !dynoCard && (
                <div className="glass-panel" style={{ padding: '24px', textAlign: 'center', color: '#94a3b8' }}>
                  <Activity size={24} style={{ color: '#a855f7', opacity: 0.7, margin: '0 auto 8px auto' }} />
                  <div style={{ fontSize: '14px', fontWeight: '600', color: '#f8fafc' }}>Dynamometer Telemetry Ready</div>
                  <p style={{ fontSize: '12px', marginTop: '4px' }}>
                    Click <b>"Live SCADA Tick"</b> at the top to stream fresh surface/pump stroke cycles for {selectedWell}.
                  </p>
                </div>
              )}

              {/* SHAP Explainable AI Waterfall */}
              {explainData && (
                <ErrorBoundary title="SHAP Explainability TreeExplainer Engine">
                  <ShapWaterfall explainData={explainData} />
                </ErrorBoundary>
              )}
            </div>
          </ErrorBoundary>
        )}

        {/* TAB 3: CSS THERMAL RECOVERY TWIN */}
        {activeTab === 'css_twin' && (
          <ErrorBoundary title="CSS Thermal Recovery Twin Engine">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <CssSchematic
                phase={cssData?.current_phase || "PRODUCTION"}
                steamTemp={Number(cssData?.steam_temp_c) || 280}
                steamPressure={Number(cssData?.steam_pressure_psi) || 1320}
                steamQuality={Number(cssData?.steam_quality_pct) || 78.5}
                viscosityCp={Number(cssData?.reservoir_viscosity_cp) || 115}
                cycleNumber={Number(cssData?.cycle_number) || 2}
                phaseDay={Number(cssData?.phase_day) || 8}
                totalDays={Number(cssData?.total_phase_days) || 45}
              />

              {/* CSS Loading State */}
              {loadingDetails && (
                <div className="glass-panel" style={{
                  padding: '20px',
                  textAlign: 'center',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '10px',
                  border: '1px solid rgba(56, 189, 248, 0.3)',
                  background: 'linear-gradient(135deg, rgba(14, 22, 38, 0.95) 0%, rgba(14, 35, 60, 0.85) 100%)',
                }}>
                  <RefreshCw size={18} className="spin" style={{ color: '#38bdf8' }} />
                  <span style={{ fontSize: '13px', fontWeight: '600', color: '#e2e8f0' }}>
                    Synchronizing Thermodynamic Steam Inflow & ASTM D341 Viscosity Vectors for {selectedWell}...
                  </span>
                </div>
              )}

              {/* CSS Thermal Performance Metrics */}
              {cssData && (
                <div className="glass-panel" style={{ padding: '20px' }}>
                  <h4 style={{ fontSize: '15px', fontWeight: '700', color: '#f8fafc', marginBottom: '14px' }}>
                    Cumulative Thermal Metrics & Steam-Oil Ratio (SOR)
                  </h4>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
                    <div style={{ background: 'rgba(15, 23, 42, 0.7)', padding: '14px', borderRadius: '8px' }}>
                      <div style={{ fontSize: '11px', color: '#94a3b8' }}>CUMULATIVE STEAM INJECTED</div>
                      <div style={{ fontSize: '22px', fontWeight: '700', color: '#38bdf8', fontFamily: 'JetBrains Mono', marginTop: '4px' }}>
                        {(Number(cssData.cumulative_steam_injected_tons) || 0).toLocaleString()} <span style={{ fontSize: '13px' }}>Tons</span>
                      </div>
                    </div>
                    <div style={{ background: 'rgba(15, 23, 42, 0.7)', padding: '14px', borderRadius: '8px' }}>
                      <div style={{ fontSize: '11px', color: '#94a3b8' }}>STEAM-OIL RATIO (SOR)</div>
                      <div style={{ fontSize: '22px', fontWeight: '700', color: '#f59e0b', fontFamily: 'JetBrains Mono', marginTop: '4px' }}>
                        {(Number(cssData.current_sor) || 0).toFixed(2)} <span style={{ fontSize: '13px' }}>m³/m³</span>
                      </div>
                    </div>
                    <div style={{ background: 'rgba(15, 23, 42, 0.7)', padding: '14px', borderRadius: '8px' }}>
                      <div style={{ fontSize: '11px', color: '#94a3b8' }}>CASING THERMAL STRESS</div>
                      <div style={{ fontSize: '22px', fontWeight: '700', color: '#f43f5e', fontFamily: 'JetBrains Mono', marginTop: '4px' }}>
                        {(Number(cssData.casing_thermal_stress_psi) || 0).toLocaleString()} <span style={{ fontSize: '13px' }}>psi</span>
                      </div>
                    </div>
                    <div style={{ background: 'rgba(15, 23, 42, 0.7)', padding: '14px', borderRadius: '8px' }}>
                      <div style={{ fontSize: '11px', color: '#94a3b8' }}>NEXT CYCLE TRANSITION</div>
                      <div style={{ fontSize: '22px', fontWeight: '700', color: '#10b981', fontFamily: 'JetBrains Mono', marginTop: '4px' }}>
                        {Number(cssData.next_transition_estimate_days) || 0} <span style={{ fontSize: '13px' }}>Days</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </ErrorBoundary>
        )}

        {/* TAB 4: WHAT-IF OPTIMIZATION SANDBOX */}
        {activeTab === 'sandbox' && (
          <ErrorBoundary title="Simulation Sandbox Engine">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div className="glass-panel" style={{ padding: '24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <div>
                    <h3 style={{ fontSize: '17px', fontWeight: '800', color: '#f8fafc' }}>
                      Digital Twin 'What-If' Simulation Lab — {selectedWell}
                    </h3>
                    <p style={{ fontSize: '13px', color: '#94a3b8' }}>
                      Adjust wellhead sensor parameters or select standard failure scenarios to observe instant AI model reactions.
                    </p>
                  </div>
                </div>

                {/* Quick Scenario Preset Chips */}
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '20px' }}>
                  <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.6px', fontWeight: '700', color: '#64748b', alignSelf: 'center', marginRight: '6px' }}>SCADA Presets:</span>
                  <button onClick={() => applyPreset(205, 140, 225, 10.5, 65)} className="btn btn-secondary" style={{ fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <CheckCircle2 size={13} style={{ color: '#10b981' }} />
                    <span>Nominal Steady State</span>
                  </button>
                  <button onClick={() => applyPreset(90, 85, 165, 12.0, 68)} className="btn btn-secondary" style={{ fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <AlertTriangle size={13} style={{ color: '#f59e0b' }} />
                    <span>Fluid Pound Starvation</span>
                  </button>
                  <button onClick={() => applyPreset(225, 155, 340, 13.5, 92)} className="btn btn-secondary" style={{ fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Flame size={13} style={{ color: '#f43f5e' }} />
                    <span>Motor Thermal Overload</span>
                  </button>
                  <button onClick={() => applyPreset(315, 80, 210, 11.0, 72)} className="btn btn-secondary" style={{ fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Activity size={13} style={{ color: '#fb923c' }} />
                    <span>Gas Interference Slug</span>
                  </button>
                  <button onClick={() => applyPreset(240, 160, 390, 8.5, 84)} className="btn btn-secondary" style={{ fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Sliders size={13} style={{ color: '#a855f7' }} />
                    <span>Paraffinic Wax Friction</span>
                  </button>
                </div>

                {/* Parameter Sliders */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px' }}>
                  <div>
                    <label style={{ fontSize: '12px', color: '#94a3b8', display: 'flex', justifyContent: 'space-between' }}>
                      <span>Casing Pressure:</span>
                      <b style={{ color: '#38bdf8', fontFamily: 'JetBrains Mono' }}>{sandboxCasing} psi</b>
                    </label>
                    <input
                      type="range"
                      min="60"
                      max="450"
                      value={sandboxCasing}
                      onChange={(e) => {
                        setSandboxCasing(Number(e.target.value));
                        runSimulation(selectedWell, e.target.value, sandboxTubing, sandboxLoad, sandboxSpeed, sandboxTemp);
                      }}
                      style={{ width: '100%', marginTop: '6px' }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '12px', color: '#94a3b8', display: 'flex', justifyContent: 'space-between' }}>
                      <span>Tubing Backpressure:</span>
                      <b style={{ color: '#38bdf8', fontFamily: 'JetBrains Mono' }}>{sandboxTubing} psi</b>
                    </label>
                    <input
                      type="range"
                      min="40"
                      max="350"
                      value={sandboxTubing}
                      onChange={(e) => {
                        setSandboxTubing(Number(e.target.value));
                        runSimulation(selectedWell, sandboxCasing, e.target.value, sandboxLoad, sandboxSpeed, sandboxTemp);
                      }}
                      style={{ width: '100%', marginTop: '6px' }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '12px', color: '#94a3b8', display: 'flex', justifyContent: 'space-between' }}>
                      <span>Polished Rod Load:</span>
                      <b style={{ color: '#f59e0b', fontFamily: 'JetBrains Mono' }}>{sandboxLoad} kN</b>
                    </label>
                    <input
                      type="range"
                      min="80"
                      max="500"
                      value={sandboxLoad}
                      onChange={(e) => {
                        setSandboxLoad(Number(e.target.value));
                        runSimulation(selectedWell, sandboxCasing, sandboxTubing, e.target.value, sandboxSpeed, sandboxTemp);
                      }}
                      style={{ width: '100%', marginTop: '6px' }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '12px', color: '#94a3b8', display: 'flex', justifyContent: 'space-between' }}>
                      <span>Motor Temperature:</span>
                      <b style={{ color: sandboxTemp > 80 ? '#f43f5e' : '#34d399', fontFamily: 'JetBrains Mono' }}>{sandboxTemp} °C</b>
                    </label>
                    <input
                      type="range"
                      min="35"
                      max="130"
                      value={sandboxTemp}
                      onChange={(e) => {
                        setSandboxTemp(Number(e.target.value));
                        runSimulation(selectedWell, sandboxCasing, sandboxTubing, sandboxLoad, sandboxSpeed, e.target.value);
                      }}
                      style={{ width: '100%', marginTop: '6px' }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '12px', color: '#94a3b8', display: 'flex', justifyContent: 'space-between' }}>
                      <span>Current Stroke Speed:</span>
                      <b style={{ color: '#fbbf24', fontFamily: 'JetBrains Mono' }}>{sandboxSpeed} SPM</b>
                    </label>
                    <input
                      type="range"
                      min="3.0"
                      max="18.0"
                      step="0.5"
                      value={sandboxSpeed}
                      onChange={(e) => {
                        setSandboxSpeed(Number(e.target.value));
                        runSimulation(selectedWell, sandboxCasing, sandboxTubing, sandboxLoad, e.target.value, sandboxTemp);
                      }}
                      style={{ width: '100%', marginTop: '6px' }}
                    />
                  </div>
                </div>
              </div>

              {/* Instant AI Reaction Cards */}
              {simResult && (
                <div className="glass-panel" style={{ padding: '24px' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '700', color: '#f8fafc', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    <Cpu size={16} color="#38bdf8" />
                    <span>Real-Time AI Inference & Optimization Output</span>
                  </h4>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '20px' }}>
                    <div style={{ background: 'rgba(15, 23, 42, 0.7)', padding: '16px', borderRadius: '10px' }}>
                      <div style={{ fontSize: '11px', color: '#94a3b8' }}>AI OPTIMAL SPEED</div>
                      <div style={{ fontSize: '26px', fontWeight: '800', color: '#38bdf8', fontFamily: 'JetBrains Mono', marginTop: '4px' }}>
                        {(Number(simResult.optimal_speed) || 0).toFixed(1)} <span style={{ fontSize: '14px' }}>SPM</span>
                      </div>
                      <div style={{ fontSize: '12px', color: '#94a3b8' }}>Delta: {((Number(simResult.optimal_speed) || 0) - sandboxSpeed).toFixed(1)} SPM</div>
                    </div>

                    <div style={{ background: 'rgba(15, 23, 42, 0.7)', padding: '16px', borderRadius: '10px' }}>
                      <div style={{ fontSize: '11px', color: '#94a3b8' }}>EXPECTED FLOW RATE</div>
                      <div style={{ fontSize: '26px', fontWeight: '800', color: '#f59e0b', fontFamily: 'JetBrains Mono', marginTop: '4px' }}>
                        {(Number(simResult.expected_flow_rate) || 0).toFixed(1)} <span style={{ fontSize: '14px' }}>BPD</span>
                      </div>
                      <div style={{ fontSize: '12px', color: '#10b981' }}>Displacement Model</div>
                    </div>

                    <div style={{ background: 'rgba(15, 23, 42, 0.7)', padding: '16px', borderRadius: '10px' }}>
                      <div style={{ fontSize: '11px', color: '#94a3b8' }}>ENERGY EFFICIENCY GAIN</div>
                      <div style={{ fontSize: '26px', fontWeight: '800', color: '#10b981', fontFamily: 'JetBrains Mono', marginTop: '4px' }}>
                        +{(Number(simResult.energy_savings_pct) || 0).toFixed(1)}%
                      </div>
                      <div style={{ fontSize: '12px', color: '#94a3b8' }}>VFD Harmonic Optimization</div>
                    </div>

                    <div style={{ background: 'rgba(15, 23, 42, 0.7)', padding: '16px', borderRadius: '10px' }}>
                      <div style={{ fontSize: '11px', color: '#94a3b8' }}>ANOMALY RISK PROBABILITY</div>
                      <div style={{ fontSize: '26px', fontWeight: '800', color: simResult.predicted_anomaly ? '#f43f5e' : '#34d399', fontFamily: 'JetBrains Mono', marginTop: '4px' }}>
                        {((Number(simResult.anomaly_score) || 0) * 100).toFixed(1)}%
                      </div>
                      <div style={{ fontSize: '12px', color: simResult.predicted_anomaly ? '#f43f5e' : '#10b981' }}>
                        {simResult.predicted_anomaly ? '● Critical Deviation' : '● In Operating Envelope'}
                      </div>
                    </div>
                  </div>

                  {/* SCADA Action Recommendation Callout */}
                  <div style={{
                    background: 'rgba(15, 23, 42, 0.85)',
                    borderLeft: `4px solid ${simResult.predicted_anomaly ? '#f43f5e' : '#10b981'}`,
                    borderRadius: '8px',
                    padding: '16px 20px',
                    marginBottom: '16px',
                  }}>
                    <div style={{ fontWeight: '700', color: '#f8fafc', fontSize: '14px' }}>Physical Diagnostic Explanation:</div>
                    <div style={{ color: '#cbd5e1', fontSize: '13px', marginTop: '4px', lineHeight: '1.5' }}>
                      {simResult.explanation}
                    </div>
                    <hr style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.08)', margin: '10px 0' }} />
                    <div style={{ fontWeight: '700', color: '#38bdf8', fontSize: '13px' }}>SCADA Automation Advisory:</div>
                    <div style={{ color: '#94a3b8', fontSize: '13px', marginTop: '2px' }}>
                      {simResult.scada_action_recommendation}
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                    <button
                      onClick={() => {
                        setVfdToast(true);
                        setTimeout(() => setVfdToast(false), 4000);
                      }}
                      className="btn btn-primary"
                      style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                    >
                      <Zap size={15} />
                      <span>Transmit VFD Frequency Calibration ({(Number(simResult.optimal_speed) || 0).toFixed(1)} SPM) to SCADA PLC</span>
                    </button>
                    {vfdToast && (
                      <span style={{ color: '#10b981', fontSize: '12px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <CheckCircle2 size={14} /> SCADA PLC Acknowledged: Frequency Setpoint Dispatched to {selectedWell} RTU
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
          </ErrorBoundary>
        )}

        {/* TAB 5: SCADA TELEMETRY FEED */}
        {activeTab === 'scada_feed' && (
          <ErrorBoundary title="SCADA Telemetry Data Table">
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <h3 style={{ fontSize: '17px', fontWeight: '800', color: '#f8fafc' }}>
                    Live SCADA Sensor Telemetry Table ({selectedWell})
                  </h3>
                  <p style={{ fontSize: '13px', color: '#94a3b8' }}>
                    Raw sensor snapshots with calibrated timestamps, hydraulic pressures, and model decisions
                  </p>
                </div>
                <button
                  onClick={() => {
                    const csvContent = "data:text/csv;charset=utf-8," + 
                      ["timestamp,well_id,casing_p,tubing_p,rod_load,spm,temp,optimal_spm,anomaly"]
                      .concat(safeTelemetry.map(t => `${t.timestamp},${t.well_id},${t.casing_pressure},${t.tubing_pressure},${t.polished_rod_load},${t.stroke_speed},${t.motor_temp},${t.optimal_speed},${t.predicted_anomaly}`))
                      .join("\n");
                    const encodedUri = encodeURI(csvContent);
                    const link = document.createElement("a");
                    link.setAttribute("href", encodedUri);
                    link.setAttribute("download", `${selectedWell}_scada_telemetry.csv`);
                    document.body.appendChild(link);
                    link.click();
                  }}
                  className="btn btn-secondary"
                >
                  <Download size={15} />
                  <span>Export Telemetry CSV</span>
                </button>
              </div>

              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#94a3b8' }}>
                      <th style={{ padding: '10px 12px' }}>TIMESTAMP</th>
                      <th style={{ padding: '10px 12px' }}>WELL ID</th>
                      <th style={{ padding: '10px 12px' }}>CASING (PSI)</th>
                      <th style={{ padding: '10px 12px' }}>TUBING (PSI)</th>
                      <th style={{ padding: '10px 12px' }}>ROD LOAD (KN)</th>
                      <th style={{ padding: '10px 12px' }}>SPEED (SPM)</th>
                      <th style={{ padding: '10px 12px' }}>MOTOR TEMP</th>
                      <th style={{ padding: '10px 12px' }}>DYNO TYPE</th>
                      <th style={{ padding: '10px 12px' }}>AI OPTIMAL</th>
                      <th style={{ padding: '10px 12px' }}>STATUS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {safeTelemetry.slice(-15).reverse().map((row, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)', color: '#cbd5e1' }}>
                        <td style={{ padding: '10px 12px', fontFamily: 'JetBrains Mono' }}>{row.timestamp?.replace('T', ' ').substring(0, 19)}</td>
                        <td style={{ padding: '10px 12px', fontWeight: '700' }}>{row.well_id}</td>
                        <td style={{ padding: '10px 12px', fontFamily: 'JetBrains Mono' }}>{row.casing_pressure}</td>
                        <td style={{ padding: '10px 12px', fontFamily: 'JetBrains Mono' }}>{row.tubing_pressure}</td>
                        <td style={{ padding: '10px 12px', fontFamily: 'JetBrains Mono' }}>{row.polished_rod_load}</td>
                        <td style={{ padding: '10px 12px', fontFamily: 'JetBrains Mono' }}>{row.stroke_speed}</td>
                        <td style={{ padding: '10px 12px', fontFamily: 'JetBrains Mono' }}>{row.motor_temp}°C</td>
                        <td style={{ padding: '10px 12px' }}>{row.dyno_card_type}</td>
                        <td style={{ padding: '10px 12px', fontFamily: 'JetBrains Mono', color: '#38bdf8', fontWeight: '700' }}>{row.optimal_speed}</td>
                        <td style={{ padding: '10px 12px' }}>
                          <span className={`badge ${row.predicted_anomaly ? 'badge-rose' : 'badge-emerald'}`}>
                            {row.predicted_anomaly ? 'ANOMALY' : 'NORMAL'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </ErrorBoundary>
        )}
      </main>

      {/* Floating AI Operations Copilot Drawer */}
      <ErrorBoundary title="AI Copilot Agent Subsystem">
        <CopilotModal
          isOpen={copilotOpen}
          onClose={() => setCopilotOpen(false)}
          selectedWell={selectedWell}
        />
      </ErrorBoundary>
    </div>
  );
}
