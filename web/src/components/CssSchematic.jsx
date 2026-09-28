import React from 'react';
import { Flame } from 'lucide-react';

export default function CssSchematic({
  phase = "PRODUCTION",
  steamTemp = 280,
  steamPressure = 1320,
  steamQuality = 78.5,
  viscosityCp = 115,
  cycleNumber = 2,
  phaseDay = 8,
  totalDays = 45,
}) {
  const safePhase = String(phase || "PRODUCTION").toUpperCase();
  const safeTemp = Number(steamTemp) || 280.0;
  const safePressure = Number(steamPressure) || 1320.0;
  const safeQuality = Number(steamQuality) || 78.5;
  const safeViscosity = Number(viscosityCp) || 115.0;
  const safeCycle = Number(cycleNumber) || 1;
  const safeDay = Number(phaseDay) || 1;
  const safeTotalDays = Number(totalDays) || 45;

  const isInjection = safePhase === "INJECTION";
  const isSoaking = safePhase === "SOAKING";
  const isProduction = safePhase === "PRODUCTION";

  const phaseColor = isInjection ? "#ef4444" : isSoaking ? "#f59e0b" : "#10b981";

  return (
    <div className="glass-panel" style={{ padding: '20px', position: 'relative' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
        <div>
          <h4 style={{ fontSize: '15px', fontWeight: '700', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Flame size={16} color="#f59e0b" /> Cyclic Steam Stimulation (CSS) Thermal Reservoir Model
          </h4>
          <p style={{ fontSize: '12px', color: '#94a3b8' }}>
            Downhole steam heat diffusion and ASTM D341 heavy oil viscosity collapse model
          </p>
        </div>
        <span className="badge" style={{ background: `${phaseColor}25`, color: phaseColor, border: `1px solid ${phaseColor}60` }}>
          ● {safePhase} PHASE (DAY {safeDay}/{safeTotalDays})
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', alignItems: 'center' }}>
        {/* Animated Wellbore & Reservoir Sand SVG */}
        <div style={{ background: 'rgba(7, 11, 19, 0.7)', borderRadius: '10px', padding: '16px', border: '1px solid rgba(255,255,255,0.05)' }}>
          <svg viewBox="0 0 500 300" style={{ width: '100%', height: 'auto', maxHeight: '270px' }}>
            <defs>
              <radialGradient id="steamHeatDiffusion" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor={isInjection ? "#ef4444" : isSoaking ? "#f59e0b" : "#38bdf8"} stopOpacity="0.8" />
                <stop offset="60%" stopColor="#f59e0b" stopOpacity="0.4" />
                <stop offset="100%" stopColor="#0f172a" stopOpacity="0.0" />
              </radialGradient>
              <pattern id="sandPatt" width="10" height="10" patternUnits="userSpaceOnUse">
                <circle cx="2" cy="2" r="1" fill="#475569" opacity="0.3" />
                <circle cx="7" cy="7" r="1.2" fill="#334155" opacity="0.4" />
              </pattern>
            </defs>

            {/* Caprock Impermeable Shale Layer */}
            <rect x="0" y="0" width="500" height="80" fill="#1e293b" />
            <text x="20" y="30" fill="#64748b" fontSize="11" fontFamily="JetBrains Mono">IMPERMEABLE CAPROCK SHALE (1,050 m)</text>

            {/* Heavy Oil Reservoir Formation (Baghewala Sand) */}
            <rect x="0" y="80" width="500" height="220" fill="#090d16" />
            <rect x="0" y="80" width="500" height="220" fill="url(#sandPatt)" />
            <text x="20" y="105" fill="#94a3b8" fontSize="11" fontFamily="JetBrains Mono">
              HEAVY OIL RESERVOIR MATRIX (18° API • 15,000 cP @ 25°C)
            </text>

            {/* Thermal Heat Front Glow around perforations */}
            <ellipse cx="250" cy="210" rx="140" ry="75" fill="url(#steamHeatDiffusion)" style={{
              animation: isInjection ? 'steam-puff 2s infinite ease-in-out' : 'none'
            }} />

            {/* Vertical Casing & Wellbore */}
            <rect x="238" y="0" width="24" height="230" fill="#334155" stroke="#64748b" strokeWidth="1.5" />
            <rect x="244" y="0" width="12" height="210" fill={isInjection ? "#ef4444" : "#f59e0b"} opacity="0.85" />

            {/* Well Perforations into Sand */}
            {[-30, -15, 0, 15, 30].map((offset, i) => (
              <g key={i}>
                <line x1="230" y1={190 + offset} x2="238" y2={190 + offset} stroke="#fbbf24" strokeWidth="2.5" />
                <line x1="262" y1={190 + offset} x2="270" y2={190 + offset} stroke="#fbbf24" strokeWidth="2.5" />
              </g>
            ))}

            {/* Phase Arrows / Indicators */}
            {isInjection && (
              <g>
                <text x="200" y="60" fill="#ef4444" fontSize="11" fontWeight="bold" fontFamily="JetBrains Mono">
                  ▼ HIGH PRESSURE STEAM (285°C)
                </text>
              </g>
            )}
            {isSoaking && (
              <g>
                <text x="180" y="60" fill="#f59e0b" fontSize="11" fontWeight="bold" fontFamily="JetBrains Mono">
                  ⇌ CONDUCTIVE HEAT SOAKING
                </text>
              </g>
            )}
            {isProduction && (
              <g>
                <text x="190" y="60" fill="#10b981" fontSize="11" fontWeight="bold" fontFamily="JetBrains Mono">
                  ▲ MOBILIZED OIL LIFT (110°C)
                </text>
              </g>
            )}
          </svg>
        </div>

        {/* Live CSS Parameter Cards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ background: 'rgba(15, 23, 42, 0.8)', padding: '12px 14px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase' }}>Downhole Thermal Front</div>
            <div style={{ fontSize: '20px', fontWeight: '700', color: '#ef4444', fontFamily: 'JetBrains Mono' }}>
              {safeTemp.toFixed(1)} <span style={{ fontSize: '13px' }}>°C</span>
            </div>
            <div style={{ fontSize: '11px', color: '#94a3b8' }}>
              Pressure: {safePressure.toFixed(0)} psi • Quality: {safeQuality.toFixed(1)}%
            </div>
          </div>

          <div style={{ background: 'rgba(15, 23, 42, 0.8)', padding: '12px 14px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase' }}>Heavy Oil Viscosity (In Situ)</div>
            <div style={{ fontSize: '20px', fontWeight: '700', color: '#f59e0b', fontFamily: 'JetBrains Mono' }}>
              {safeViscosity.toFixed(0)} <span style={{ fontSize: '13px' }}>cP</span>
            </div>
            <div style={{ fontSize: '11px', color: '#34d399' }}>
              ▼ Reduced from 15,000 cP baseline (99.2% mobility gain)
            </div>
          </div>

          <div style={{ background: 'rgba(15, 23, 42, 0.8)', padding: '12px 14px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase' }}>Cycle History</div>
            <div style={{ fontSize: '16px', fontWeight: '700', color: '#38bdf8', fontFamily: 'JetBrains Mono' }}>
              Cycle #{safeCycle} • {Math.max(0, safeTotalDays - safeDay)} Days Remain
            </div>
            <div style={{ fontSize: '11px', color: '#94a3b8' }}>
              Optimal workover window predicted
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
