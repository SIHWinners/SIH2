import React, { useState } from 'react';
import { Activity } from 'lucide-react';

export default function DynoCardCanvas({ cardData }) {
  const [hoverPoint, setHoverPoint] = useState(null);

  if (!cardData || !Array.isArray(cardData.points) || cardData.points.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '24px', textAlign: 'center', color: '#94a3b8' }}>
        No dynamometer card telemetry available for this wellhead.
      </div>
    );
  }

  const {
    points = [],
    card_type = "Normal",
    pprl_lbs = 35000,
    mprl_lbs = 25000,
    stroke_length_in = 120,
    indicated_pump_hp = 0,
    pump_fillage_pct = 90,
    diagnostic_message = "Normal operation envelope.",
  } = cardData;

  const safePprl = Number(pprl_lbs) || 35000;
  const safeMprl = Number(mprl_lbs) || 25000;
  const safeStrokeLength = Number(stroke_length_in) || 120;
  const safeCardType = String(card_type || "Normal");

  const width = 540;
  const height = 300;
  const padding = 50;

  // Compute scales
  const maxPos = safeStrokeLength;
  const maxLoad = Math.max(safePprl * 1.12, 35000);
  const minLoad = Math.max(0, safeMprl * 0.85);
  const rangeY = Math.max(maxLoad - minLoad, 1000);

  const scaleX = (pos) => padding + ((Number(pos) || 0) / maxPos) * (width - 2 * padding);
  const scaleY = (load) => height - padding - (((Number(load) || minLoad) - minLoad) / rangeY) * (height - 2 * padding);

  // SVG paths
  const surfacePath = points.reduce((acc, pt, idx) => {
    const x = scaleX(pt.position_in);
    const y = scaleY(pt.surface_load_lbs);
    return idx === 0 ? `M ${x},${y}` : `${acc} L ${x},${y}`;
  }, "") + " Z";

  const downholePath = points.reduce((acc, pt, idx) => {
    const x = scaleX(pt.position_in);
    const y = scaleY(pt.downhole_load_lbs);
    return idx === 0 ? `M ${x},${y}` : `${acc} L ${x},${y}`;
  }, "") + " Z";

  const isNormal = safeCardType === "Normal";

  return (
    <div className="glass-panel" style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <div>
          <h4 style={{ fontSize: '15px', fontWeight: '700', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={16} color="#a855f7" /> Dynamometer Card (Polished Rod Load vs Position)
          </h4>
          <p style={{ fontSize: '12px', color: '#94a3b8' }}>
            Surface card (elastic rod string) vs Downhole pump card (valve action)
          </p>
        </div>
        <span className={`badge ${isNormal ? 'badge-emerald' : 'badge-rose'}`}>
          {card_type.toUpperCase()}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 240px', gap: '18px', alignItems: 'center' }}>
        {/* Interactive SVG Dyno Chart */}
        <div style={{ background: '#090e17', borderRadius: '10px', padding: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
          <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto' }}>
            {/* Grid Lines */}
            {[0, 0.25, 0.5, 0.75, 1.0].map((frac, i) => {
              const yVal = minLoad + frac * (maxLoad - minLoad);
              const y = scaleY(yVal);
              return (
                <g key={i}>
                  <line x1={padding} y1={y} x2={width - padding} y2={y} stroke="rgba(255,255,255,0.08)" strokeDasharray="3,3" />
                  <text x={padding - 8} y={y + 4} fill="#64748b" fontSize="9" textAnchor="end" fontFamily="JetBrains Mono">
                    {(yVal / 1000).toFixed(0)}k
                  </text>
                </g>
              );
            })}
            {[0, 0.25, 0.5, 0.75, 1.0].map((frac, i) => {
              const xVal = frac * maxPos;
              const x = scaleX(xVal);
              return (
                <g key={i}>
                  <line x1={x} y1={padding} x2={x} y2={height - padding} stroke="rgba(255,255,255,0.08)" strokeDasharray="3,3" />
                  <text x={x} y={height - padding + 16} fill="#64748b" fontSize="9" textAnchor="middle" fontFamily="JetBrains Mono">
                    {xVal.toFixed(0)}"
                  </text>
                </g>
              );
            })}

            {/* Downhole Card Area (Shaded) */}
            <path d={downholePath} fill="rgba(6, 182, 212, 0.12)" stroke="#06b6d4" strokeWidth="2" strokeDasharray="4,3" />

            {/* Surface Card Area */}
            <path d={surfacePath} fill="rgba(245, 158, 11, 0.14)" stroke="#f59e0b" strokeWidth="2.5" />

            {/* Hover Points */}
            {points.map((pt, idx) => {
              const x = scaleX(pt.position_in);
              const y = scaleY(pt.surface_load_lbs);
              return (
                <circle
                  key={idx}
                  cx={x}
                  cy={y}
                  r="3.5"
                  fill="#f59e0b"
                  style={{ cursor: 'pointer', transition: 'r 0.15s ease' }}
                  onMouseEnter={() => setHoverPoint(pt)}
                  onMouseLeave={() => setHoverPoint(null)}
                />
              );
            })}

            {/* Axis Titles */}
            <text x={width / 2} y={height - 10} fill="#94a3b8" fontSize="10" textAnchor="middle" fontFamily="JetBrains Mono">
              STROKE POSITION (INCHES)
            </text>
            <text x="14" y={height / 2} fill="#94a3b8" fontSize="10" textAnchor="middle" transform={`rotate(-90 14 ${height/2})`} fontFamily="JetBrains Mono">
              ROD LOAD (LBS)
            </text>
          </svg>

          {/* Legend */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: '20px', fontSize: '11px', marginTop: '6px', color: '#94a3b8' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '12px', height: '3px', background: '#f59e0b', borderRadius: '2px' }}></span>
              Surface Card (Polished Rod)
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '12px', height: '2px', background: '#06b6d4', borderTop: '2px dashed #06b6d4' }}></span>
              Downhole Pump Card
            </span>
          </div>
        </div>

        {/* Dyno Diagnostic Summary Card */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ background: 'rgba(15, 23, 42, 0.85)', padding: '14px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase' }}>Pump Fillage Efficiency</div>
            <div style={{ fontSize: '24px', fontWeight: '800', color: isNormal ? '#10b981' : '#f59e0b', fontFamily: 'JetBrains Mono' }}>
              {pump_fillage_pct.toFixed(1)}%
            </div>
            <div style={{ fontSize: '12px', color: '#cbd5e1', marginTop: '4px', lineHeight: '1.4' }}>
              {diagnostic_message}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px' }}>
            <div style={{ background: 'rgba(15, 23, 42, 0.7)', padding: '8px 10px', borderRadius: '6px' }}>
              <span style={{ color: '#94a3b8', fontSize: '10px' }}>PPRL (PEAK):</span>
              <div style={{ fontWeight: '700', color: '#f8fafc', fontFamily: 'JetBrains Mono' }}>{pprl_lbs.toLocaleString()} lbs</div>
            </div>
            <div style={{ background: 'rgba(15, 23, 42, 0.7)', padding: '8px 10px', borderRadius: '6px' }}>
              <span style={{ color: '#94a3b8', fontSize: '10px' }}>MPRL (MIN):</span>
              <div style={{ fontWeight: '700', color: '#f8fafc', fontFamily: 'JetBrains Mono' }}>{mprl_lbs.toLocaleString()} lbs</div>
            </div>
            <div style={{ background: 'rgba(15, 23, 42, 0.7)', padding: '8px 10px', borderRadius: '6px' }}>
              <span style={{ color: '#94a3b8', fontSize: '10px' }}>INDICATED HP:</span>
              <div style={{ fontWeight: '700', color: '#38bdf8', fontFamily: 'JetBrains Mono' }}>{indicated_pump_hp.toFixed(2)} HP</div>
            </div>
            <div style={{ background: 'rgba(15, 23, 42, 0.7)', padding: '8px 10px', borderRadius: '6px' }}>
              <span style={{ color: '#94a3b8', fontSize: '10px' }}>STROKE LEN:</span>
              <div style={{ fontWeight: '700', color: '#fbbf24', fontFamily: 'JetBrains Mono' }}>{stroke_length_in}"</div>
            </div>
          </div>

          {hoverPoint && (
            <div style={{ background: 'rgba(30, 41, 59, 0.95)', padding: '8px', borderRadius: '6px', fontSize: '11px', color: '#38bdf8', textAlign: 'center', fontFamily: 'JetBrains Mono' }}>
              Pos: {hoverPoint.position_in.toFixed(1)}" | Load: {hoverPoint.surface_load_lbs.toLocaleString()} lbs
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
