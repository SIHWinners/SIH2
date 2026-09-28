import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('SCADA Telemetry Component Error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          className="glass-panel"
          style={{
            padding: '24px',
            margin: '16px 0',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(15, 23, 42, 0.95) 100%)',
            borderRadius: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
            <AlertTriangle size={22} style={{ color: '#ef4444' }} />
            <div>
              <h4 style={{ fontSize: '15px', fontWeight: '700', color: '#f87171', margin: 0 }}>
                {this.props.title || 'SCADA Component Telemetry Stream Error'}
              </h4>
              <p style={{ fontSize: '12px', color: '#94a3b8', margin: '4px 0 0 0' }}>
                The digital twin subsystem encountered a rendering exception while evaluating live sensor telemetry.
              </p>
            </div>
          </div>

          <div
            style={{
              background: 'rgba(0, 0, 0, 0.4)',
              padding: '12px 14px',
              borderRadius: '8px',
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '11px',
              color: '#fca5a5',
              overflowX: 'auto',
              marginBottom: '16px',
            }}
          >
            {this.state.error?.toString() || 'Unknown runtime telemetry error'}
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              onClick={this.handleReset}
              className="btn btn-secondary"
              style={{ fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <RefreshCw size={14} />
              <span>Retry Component Stream</span>
            </button>
            <button
              onClick={() => window.location.reload()}
              className="btn btn-primary"
              style={{ fontSize: '12px' }}
            >
              Reload SCADA Console
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
