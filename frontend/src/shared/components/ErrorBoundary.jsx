import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, lastReqId: null };
  }

  static getDerivedStateFromError() { return { hasError: true }; }

  componentDidCatch(error, info) {
    const reqId = window?.lastRequestId ?? null;
    this.setState({ lastReqId: reqId });
    console.error('💥 ErrorBoundary caught:', { error, stack: info.componentStack, props: this.props, reqId });
  }

  handleReload = () => window.location.reload();

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 bg-red-900/90 text-white text-center rounded-2xl shadow-lg max-w-lg mx-auto mt-12">
          <div className="text-xl font-bold mb-2">🔥 Something went wrong, King!</div>
          <div className="mb-4">Peep the console for more info.</div>
          {this.state.lastReqId && (
            <div className="mb-4 text-sm">Request ID: <code>{this.state.lastReqId}</code></div>
          )}
          <button className="px-4 py-2 bg-black text-white rounded shadow hover:bg-gray-800" onClick={this.handleReload}>
            Reload Page
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
