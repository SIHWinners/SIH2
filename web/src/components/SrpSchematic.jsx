import React from 'react';
import { Gauge, AlertTriangle, CheckCircle2 } from 'lucide-react';

export default function SrpSchematic({ 
  spm = 10.5, 
  rodLoad = 225, 
  casingPressure = 205, 
  tubingPressure = 142, 
  motorTemp = 65, 
  dynoType = "Normal" 
}) {
  const safeSpm = Number(spm) || 10.0;
  const safeRodLoad = Number(rodLoad) || 225.0;
  const safeCasingPressure = Number(casingPressure) || 205.0;
  const safeTubingPressure = Number(tubingPressure) || 142.0;
  const safeMotorTemp = Number(motorTemp) || 65.0;
  const safeDynoType = String(dynoType || "Normal");

  // Animation duration derived from Strokes Per Minute (SPM)
  // At 10 SPM -> 60/10 = 6 seconds per stroke cycle
  const strokeDuration = Math.max(1.8, Math.min(12, 60 / safeSpm));

  return (
    <div className="glass-panel" style={{ padding: '20px', position: 'relative', overflow: 'hidden' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <div>
          <h4 style={{ fontSize: '15px', fontWeight: '700', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Gauge size={16} color="#f59e0b" /> Sucker Rod Pump (SRP) Dynamic Physics Twin
          </h4>
          <p style={{ fontSize: '12px', color: '#94a3b8' }}>
            Reciprocating kinematic mechanical model synced with live SCADA motor speed ({safeSpm.toFixed(1)} SPM)
          </p>
        </div>
        <span className={`badge ${safeDynoType === 'Normal' ? 'badge-emerald' : 'badge-rose'}`}>
          ● {safeDynoType.toUpperCase()}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: '20px', alignItems: 'center' }}>
        {/* Animated SVG Beam Pumping Unit */}
        <div style={{ background: 'rgba(7, 11, 19, 0.7)', borderRadius: '10px', padding: '16px', border: '1px solid rgba(255,255,255,0.05)' }}>
          <svg viewBox="0 0 500 320" style={{ width: '100%', height: 'auto', maxHeight: '280px' }}>
            <defs>
              <linearGradient id="groundGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#1e293b" />
                <stop offset="100%" stopColor="#0f172a" />
              </linearGradient>
              <linearGradient id="oilStream" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f59e0b" />
                <stop offset="100%" stopColor="#d97706" />
              </linearGradient>
            </defs>

            {/* Ground / Surface Level */}
            <rect x="0" y="240" width="500" height="80" fill="url(#groundGrad)" />
            <line x1="0" y1="240" x2="500" y2="240" stroke="#475569" strokeWidth="2" strokeDasharray="6,4" />
            <text x="20" y="258" fill="#64748b" fontSize="11" fontFamily="JetBrains Mono">SURFACE GROUND LEVEL (0 m)</text>

            {/* Samson Post (A-frame tower) */}
            <polygon points="180,240 210,120 220,120 250,240" fill="#334155" stroke="#475569" strokeWidth="2" />
            <line x1="195" y1="180" x2="235" y2="180" stroke="#475569" strokeWidth="2" />
            <circle cx="215" cy="120" r="7" fill="#f59e0b" />

            {/* Gearbox & Crank Counterweight (Rotating) */}
            <rect x="290" y="195" width="45" height="45" rx="4" fill="#1e293b" stroke="#64748b" strokeWidth="2" />
            <circle cx="312" cy="217" r="14" fill="#0f172a" stroke="#f59e0b" strokeWidth="2" />
            
            {/* Animated Walking Beam & Horsehead */}
            <g style={{
              transformOrigin: '215px 120px',
              animation: `nodding-beam ${strokeDuration}s infinite ease-in-out`
            }}>
              {/* Walking Beam */}
              <polygon points="100,114 330,114 326,126 96,126" fill="#475569" stroke="#94a3b8" strokeWidth="1.5" />
              {/* Counter-bearing pivot */}
              <circle cx="215" cy="120" r="5" fill="#f8fafc" />

              {/* Horsehead (Front Curved Head) */}
              <path d="M 96,126 Q 70,120 65,80 Q 75,70 100,114 Z" fill="#d97706" stroke="#fbbf24" strokeWidth="1.5" />

              {/* Pitman Arm connecting beam back to crank */}
              <line x1="325" y1="120" x2="312" y2="205" stroke="#94a3b8" strokeWidth="3" />
            </g>

            {/* Wellhead (Stuffing Box & Christmas Tree) */}
            <rect x="65" y="200" width="30" height="40" fill="#334155" stroke="#64748b" strokeWidth="1.5" />
            <line x1="80" y1="200" x2="80" y2="160" stroke="#cbd5e1" strokeWidth="3" /> {/* Polished Rod */}
            
            {/* Casing & Tubing Below Surface */}
            <rect x="68" y="240" width="24" height="75" fill="#090d16" stroke="#475569" strokeWidth="1.5" />
            {/* Sucker Rod String moving inside tubing */}
            <line x1="80" y1="240" x2="80" y2="315" stroke="#f59e0b" strokeWidth="2.5" />

            {/* Flowline to Surface Separator */}
            <path d="M 95,215 L 140,215 L 140,238" fill="none" stroke="#f59e0b" strokeWidth="3" strokeDasharray="4,2" />
            <text x="105" y="210" fill="#fbbf24" fontSize="10" fontFamily="JetBrains Mono">CRUDE DISCHARGE</text>

            {/* Surface Drive Motor */}
            <rect x="350" y="210" width="35" height="30" rx="3" fill="#0284c7" stroke="#38bdf8" strokeWidth="1.5" />
            <text x="352" y="205" fill="#38bdf8" fontSize="10" fontFamily="JetBrains Mono">VFD MOTOR</text>
          </svg>
        </div>

        {/* Live Physical Callout Cards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ background: 'rgba(15, 23, 42, 0.8)', padding: '12px 14px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase' }}>Polished Rod Load (PRL)</div>
            <div style={{ fontSize: '20px', fontWeight: '700', color: '#f59e0b', fontFamily: 'JetBrains Mono' }}>
              {safeRodLoad.toFixed(1)} <span style={{ fontSize: '13px' }}>kN</span>
            </div>
            <div style={{ fontSize: '11px', color: safeRodLoad > 300 ? '#f43f5e' : '#10b981' }}>
              {safeRodLoad > 300 ? '▲ High rod fatigue stress' : '● Within rod tensile limits'}
            </div>
          </div>

          <div style={{ background: 'rgba(15, 23, 42, 0.8)', padding: '12px 14px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase' }}>Casing / Tubing Head Pressure</div>
            <div style={{ fontSize: '16px', fontWeight: '700', color: '#38bdf8', fontFamily: 'JetBrains Mono' }}>
              {safeCasingPressure.toFixed(0)} <span style={{ fontSize: '12px', color: '#94a3b8' }}>psi</span> / {safeTubingPressure.toFixed(0)} <span style={{ fontSize: '12px', color: '#94a3b8' }}>psi</span>
            </div>
            <div style={{ fontSize: '11px', color: '#94a3b8' }}>
              ΔP: {(safeCasingPressure - safeTubingPressure).toFixed(0)} psi Inflow Drive
            </div>
          </div>

          <div style={{ background: 'rgba(15, 23, 42, 0.8)', padding: '12px 14px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase' }}>Drive Motor Temperature</div>
            <div style={{ fontSize: '18px', fontWeight: '700', color: safeMotorTemp > 80 ? '#f43f5e' : '#34d399', fontFamily: 'JetBrains Mono' }}>
              {safeMotorTemp.toFixed(1)} <span style={{ fontSize: '13px' }}>°C</span>
            </div>
            <div style={{ fontSize: '11px', color: safeMotorTemp > 80 ? '#f43f5e' : '#94a3b8' }}>
              {safeMotorTemp > 80 ? '[CRITICAL] Thermal Derating Imminent' : '● Thermal Dissipation Steady'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
