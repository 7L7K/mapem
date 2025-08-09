import React from 'react';
import { Button, ErrorBox } from '@components/ui';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      lastReqId: null,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    const reqId = window?.lastRequestId ?? null;
    this.setState({
      lastReqId: reqId,
      error,
      errorInfo: info
    });
    console.error('💥 ErrorBoundary caught:', {
      error,
      stack: info.componentStack,
      props: this.props,
      reqId
    });
  }

  handleReload = () => window.location.reload();

  handleRetry = () => {
    this.setState({
      hasError: false,
      lastReqId: null,
      error: null,
      errorInfo: null
    });
  };

  render() {
    if (this.state.hasError) {
      const isDevelopment = import.meta.env.DEV;

      return (
        <div className="min-h-screen bg-background flex items-center justify-center p-8">
          <div className="max-w-md w-full space-y-6">
            <div className="text-center">
              <div className="text-6xl mb-4">💥</div>
              <h1 className="text-3xl font-bold text-text mb-2">
                Something went wrong, King!
              </h1>
              <p className="text-dim">
                Check the console for details. Let's get you back on track.
              </p>
            </div>

            {this.state.lastReqId && (
              <div className="text-center">
                <div className="text-sm text-dim">Request ID:</div>
                <code className="text-primary">{this.state.lastReqId}</code>
              </div>
            )}

            {isDevelopment && this.state.error && (
              <ErrorBox className="text-left">
                <div className="font-mono text-sm">
                  <strong>Error:</strong> {this.state.error.message}
                  {this.state.errorInfo?.componentStack && (
                    <details className="mt-2">
                      <summary className="cursor-pointer text-dim">Stack trace</summary>
                      <pre className="mt-2 text-xs overflow-auto max-h-40">
                        {this.state.errorInfo.componentStack}
                      </pre>
                    </details>
                  )}
                </div>
              </ErrorBox>
            )}

            <div className="flex gap-3">
              <Button
                variant="primary"
                onClick={this.handleRetry}
                className="flex-1"
              >
                Try Again
              </Button>
              <Button
                variant="secondary"
                onClick={this.handleReload}
                className="flex-1"
              >
                Reload Page
              </Button>
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
