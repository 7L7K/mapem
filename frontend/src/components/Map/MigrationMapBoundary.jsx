// MigrationMapBoundary.jsx
import React from 'react';

class MigrationMapBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(_) {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return <div style={{ color: 'red', padding: '1rem' }}>🧨 Map failed to load. Please try refreshing.</div>;
    }
    return this.props.children;
  }
}

export default MigrationMapBoundary;
