import React from 'react';

export default function ShapWaterfall({ explainData }) {
  if (!explainData || !explainData.top_drivers) {
    return null;
  }

  const { top_drivers, natural_language_summary, anomaly_score, predicted_anomaly, base_value } = explainData;
  const maxAbs = Math.max(...top_drivers.map(d => Math.abs(d.shap_value)), 0.2);

  return (
    <div className="glass-panel" style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <div>
          <h4 style={{ fontSize: '15px', fontWeight: '700', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>🧠</span> Explainable AI (SHAP TreeExplainer Attribution)
          </h4>
          <p style={{ fontSize: '12px', color: '#94a3b8' }}>
            Local Shapley additive values isolating the exact physical drivers of the anomaly alert
          </p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <span style={{ fontSize: '12px', color: '#94a3b8' }}>Model Risk Score: </span>
          <b style={{ color: predicted_anomaly ? '#f43f5e' : '#10b981', fontFamily: 'JetBrains Mono', fontSize: '14px' }}>
            {(anomaly_score * 100).toFixed(1)}%
          </b>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '20px', alignItems: 'center' }}>
        {/* Horizontal SHAP Impact Bars */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {top_drivers.slice(0, 6).map((driver, idx) => {
            const isPositive = driver.shap_value >= 0;
            const barWidth = Math.min(100, (Math.abs(driver.shap_value) / maxAbs) * 100);
            const color = isPositive ? '#f43f5e' : '#10b981';

            return (
              <div key={idx} style={{ display: 'grid', gridTemplateColumns: '160px 1fr 60px', alignItems: 'center', gap: '10px', fontSize: '12px' }}>
                <span style={{ color: '#cbd5e1', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={driver.label}>
                  {driver.label}
                </span>

                {/* Centered zero-line bar */}
                <div style={{ height: '14px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', position: 'relative', overflow: 'hidden' }}>
                  <div
                    style={{
                      position: 'absolute',
                      left: isPositive ? '50%' : `${50 - barWidth / 2}%`,
                      width: `${barWidth / 2}%`,
                      height: '100%',
                      background: color,
                      borderRadius: '2px',
                      transition: 'width 0.3s ease',
                    }}
                  />
                  <div style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: '1px', background: 'rgba(255,255,255,0.2)' }} />
                </div>

                <span style={{ color, fontFamily: 'JetBrains Mono', fontWeight: '600', fontSize: '11px', textAlign: 'right' }}>
                  {driver.shap_value > 0 ? `+${driver.shap_value.toFixed(3)}` : driver.shap_value.toFixed(3)}
                </span>
              </div>
            );
          })}
        </div>

        {/* Natural Language Diagnostic Insight Card */}
        <div style={{ background: 'rgba(15, 23, 42, 0.85)', padding: '16px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)' }}>
          <div style={{ fontSize: '11px', color: '#38bdf8', textTransform: 'uppercase', fontWeight: '700', letterSpacing: '0.6px' }}>
            Automated Physical Diagnostic Synthesis
          </div>
          <div style={{ fontSize: '13px', color: '#f1f5f9', marginTop: '8px', lineHeight: '1.5' }}>
            {natural_language_summary}
          </div>
          <hr style="border: none; border-top: 1px solid rgba(255,255,255,0.08); margin: 12px 0;" />
          <div style={{ fontSize: '11px', color: '#94a3b8' }}>
            <b>Baseline Envelope:</b> {base_value.toFixed(3)} | <b>Explainability Protocol:</b> SHAP TreeExplainer v0.52
          </div>
        </div>
      </div>
    </div>
  );
}
