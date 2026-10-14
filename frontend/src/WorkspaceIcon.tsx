export type WorkspaceIconName = 'today' | 'care' | 'growth' | 'twin' | 'family' | 'history' | 'settings' | 'arrow'

const shapes: Record<WorkspaceIconName, React.ReactNode> = {
  today: <><path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1Z" /><path d="M9 7h6" /></>,
  care: <><path d="M12 21S3 15.7 3 9.5A4.5 4.5 0 0 1 12 8a4.5 4.5 0 0 1 9 1.5C21 15.7 12 21 12 21Z" /></>,
  growth: <><path d="M4 3v17h17M7 15l5-5 4 2 5-7M17 5h4v4" /></>,
  twin: <><path d="m12 3 2.3 6.7L21 12l-6.7 2.3L12 21l-2.3-6.7L3 12l6.7-2.3Z" /></>,
  family: <><circle cx="9" cy="8" r="3" /><path d="M3 21v-3a6 6 0 0 1 12 0v3M16 5a3 3 0 0 1 0 6M17 15a5 5 0 0 1 4 5v1" /></>,
  history: <><path d="M3 4v5h5M3.5 9a9 9 0 1 1-.1 6M12 7v5l3 2" /></>,
  settings: <><path d="M4 7h16M4 17h16" /><circle cx="8" cy="7" r="3" /><circle cx="16" cy="17" r="3" /></>,
  arrow: <><path d="M5 12h14m-5-5 5 5-5 5" /></>,
}

export default function WorkspaceIcon({ name, className = '' }: { name: WorkspaceIconName; className?: string }) {
  return <svg className={`ws-icon ${className}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">{shapes[name]}</svg>
}
