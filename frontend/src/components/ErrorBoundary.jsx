import React from 'react';
import { AlertOctagon, RotateCcw } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Unhandled React Render Error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          className="card"
          style={{
            margin: '2rem 0',
            padding: '2rem',
            background: 'rgba(239, 68, 68, 0.08)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            borderRadius: '12px',
            color: '#f8fafc',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <AlertOctagon size={28} color="#f43f5e" />
            <div>
              <h3 style={{ margin: 0, fontSize: '1.2rem', color: '#fb7185', fontWeight: 800 }}>
                Display Rendering Diagnostic
              </h3>
              <p style={{ margin: '0.2rem 0 0 0', color: '#94a3b8', fontSize: '0.85rem' }}>
                The analysis data was returned successfully by the backend, but a visual component encountered a display issue.
              </p>
            </div>
          </div>

          <div
            style={{
              background: '#0d0e14',
              padding: '1rem',
              borderRadius: '8px',
              border: '1px solid #23242e',
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '0.8rem',
              color: '#fca5a5',
              marginBottom: '1.25rem',
              maxHeight: '180px',
              overflowY: 'auto',
            }}
          >
            {this.state.error?.toString() || 'Unknown render exception'}
          </div>

          <button
            type="button"
            className="btn-primary"
            onClick={this.handleReset}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}
          >
            <RotateCcw size={15} />
            <span>Reset View & Re-Analyze</span>
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
