import { useState } from 'react';
import './AnalysisCard.css';

const VERDICT_MAP = {
  GO:      { cls: 'verdict-go',      icon: '✅', border: '#10B981' },
  CAUTION: { cls: 'verdict-caution', icon: '⚠️', border: '#F59E0B' },
  DECLINE: { cls: 'verdict-decline', icon: '❌', border: '#EF4444' },
};

function profitColor(v)  { return v > 0 ? '#10B981' : '#EF4444'; }
function roiColor(v)     { return v > 1 ? '#10B981' : v > 0.8 ? '#F59E0B' : '#EF4444'; }
function riskColor(r)    { return ({ LOW: '#10B981', MEDIUM: '#F59E0B', HIGH: '#EF4444' })[r] || '#7F7F7F'; }

function Expandable({ title, children, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="expandable">
      <button className="expandable-header" onClick={() => setOpen(o => !o)}>
        <span>{title}</span>
        <span className="expandable-arrow">{open ? '▾' : '▸'}</span>
      </button>
      {open && <div className="expandable-body">{children}</div>}
    </div>
  );
}

export default function AnalysisCard({ rec, debugInfo }) {
  const verdict = (rec.verdict || 'CAUTION').toUpperCase();
  const v = VERDICT_MAP[verdict] || VERDICT_MAP.CAUTION;

  return (
    <div className="analysis-card">
      {/* Verdict Banner */}
      <div className={v.cls} style={{ borderLeftColor: v.border }}>
        <h3>{v.icon} {verdict}</h3>
        <p>{rec.verdict_summary}</p>
      </div>

      {/* Metric Cards */}
      <div className="metrics-row">
        <div className="metric-card">
          <span className="metric-label">Projected Lift</span>
          <span className="metric-value">+{(rec.projected_lift_pct || 0).toFixed(1)}%</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Net Profit</span>
          <span className="metric-value" style={{ color: profitColor(rec.net_incremental_profit || 0) }}>
            ${(rec.net_incremental_profit || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        </div>
        <div className="metric-card">
          <span className="metric-label">ROI</span>
          <span className="metric-value" style={{ color: roiColor(rec.roi || 0) }}>
            {(rec.roi || 0).toFixed(2)}x
          </span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Cannib. Risk</span>
          <span className="metric-value" style={{ color: riskColor(rec.cannibalization_risk) }}>
            {rec.cannibalization_risk || 'UNKNOWN'}
          </span>
        </div>
      </div>

      {/* Expandable Sections */}
      <Expandable title="Profit Breakdown">
        <div className="breakdown-grid">
          <div><span className="bd-label">Gross Profit</span><span className="bd-value">${(rec.gross_profit || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span></div>
          <div><span className="bd-label">Revenue</span><span className="bd-value">${(rec.projected_revenue || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span></div>
          <div><span className="bd-label">Cannib. Cost</span><span className="bd-value">-${Math.abs(rec.cannibalization_cost || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span></div>
          <div><span className="bd-label">Margin/Unit</span><span className="bd-value">${(rec.margin_per_unit || 0).toFixed(2)}</span></div>
          <div><span className="bd-label">Post-Promo Dip</span><span className="bd-value">-${Math.abs(rec.post_promo_dip_cost || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span></div>
          <div><span className="bd-label">Units</span><span className="bd-value">{rec.projected_units || 0} vs {rec.baseline_units || 0}</span></div>
        </div>
      </Expandable>

      <Expandable title="Cannibalization & Risk">
        <p><strong>Cannibalization:</strong> {rec.cannibalization_details || 'N/A'}</p>
        {rec.risk_factors && rec.risk_factors.length > 0 && (
          <ul className="risk-list">
            {rec.risk_factors.map((f, i) => <li key={i}>{f}</li>)}
          </ul>
        )}
        <p><strong>Timing:</strong> {rec.timing_assessment || 'N/A'}</p>
      </Expandable>

      {rec.alternative_suggestion && (
        <Expandable title="Alternative Suggestion">
          <p className="alt-suggestion">{rec.alternative_suggestion}</p>
        </Expandable>
      )}

      <Expandable title="Full Reasoning">
        <p className="reasoning">{rec.reasoning || ''}</p>
      </Expandable>

      {/* Debug Info */}
      {debugInfo && debugInfo.matchedProduct && (
        <details className="debug-info">
          <summary>i</summary>
          <div className="debug-panel">
            <span className="debug-title">Technical Details</span>
            <p><strong>Matched:</strong> {debugInfo.matchedProduct.product_name || debugInfo.matchedProduct.name}</p>
            {debugInfo.matchedProduct.confidence != null && <p><strong>Confidence:</strong> {debugInfo.matchedProduct.confidence}</p>}
            {debugInfo.contextTokens && <p><strong>Context tokens:</strong> ~{debugInfo.contextTokens}</p>}
          </div>
        </details>
      )}
    </div>
  );
}
