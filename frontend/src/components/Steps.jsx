/** Simple 3-step progress indicator for the interview setup flow. */
export default function Steps({ current = 1 }) {
  const steps = ['Role', 'Difficulty', 'Start']
  return (
    <div className="steps">
      {steps.map((label, i) => {
        const n = i + 1
        const state = n < current ? 'done' : n === current ? 'active' : ''
        return (
          <div key={label} style={{ display: 'contents' }}>
            <div className={`step ${state}`}>
              <span className="dot">{n < current ? '✓' : n}</span>
              <span>{label}</span>
            </div>
            {i < steps.length - 1 && <span className="step-line" />}
          </div>
        )
      })}
    </div>
  )
}
