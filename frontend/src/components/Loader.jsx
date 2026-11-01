export default function Loader({ full = false, label = 'Loading...', large = false }) {
  const content = (
    <div className="flex-center" style={{ flexDirection: 'column', gap: 14 }}>
      <div className={large ? 'spinner spinner-lg' : 'spinner'} />
      {label && <div className="muted" style={{ fontSize: '0.92rem' }}>{label}</div>}
    </div>
  )

  if (full) {
    return (
      <div className="flex-center" style={{ minHeight: '100vh' }}>
        {content}
      </div>
    )
  }
  return <div style={{ padding: '40px 0' }}>{content}</div>
}
