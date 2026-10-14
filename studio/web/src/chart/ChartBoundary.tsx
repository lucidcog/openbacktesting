import { Component, type ReactNode } from 'react'
export class ChartBoundary extends Component<{ children: ReactNode }, { error: string }> {
  state = { error: '' }
  static getDerivedStateFromError(error: Error) { return { error: error.message } }
  render() { return this.state.error ? <div role="alert" className="grid h-full place-content-center p-6 text-center text-sm text-muted-foreground">Chart unavailable: {this.state.error}. The saved report remains available.</div> : this.props.children }
}
