"use client";

import React from "react";
import { Button } from "@/components/ui/button";

interface Props {
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export default class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[400px] flex-col items-center justify-center gap-4">
          <h2 className="text-xl font-semibold">Une erreur est survenue</h2>
          <p className="text-muted-foreground">
            {this.state.error?.message || "Erreur inattendue"}
          </p>
          <Button onClick={() => this.setState({ hasError: false })}>
            Réessayer
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}
