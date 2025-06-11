import React from "react";

/**
 * Reusable error boundary.
 * Wrap any subtree to catch React render errors.
 */
export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error("💥 Caught by ErrorBoundary:", error, info);
  }

  render() {
    const { hasError, error } = this.state;
    if (hasError) {
      return (
        <div className="m-4 rounded bg-red-900/80 p-4 text-white">
          <h2 className="text-lg font-bold">Something went wrong.</h2>
          <pre className="mt-2 whitespace-pre-wrap text-xs">{String(error)}</pre>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
