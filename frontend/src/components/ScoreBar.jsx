import { scoreColor } from '../utils/format'

/** Horizontal labelled score bar (0-100). */
export default function ScoreBar({ name, value = 0, icon }) {
  const v = Math.max(0, Math.min(100, Number(value) || 0))
  const color = scoreColor(v)
  return (
    <div className="score-row">
      <div className="flex-between">
        <span className="name">
          {icon ? <span style={{ marginRight: 6 }}>{icon}</span> : null}
          {name}
        </span>
        <span className="val" style={{ color }}>
          {Math.round(v)}
        </span>
      </div>
      <div className="bar">
        <span style={{ width: `${v}%`, background: color }} />
      </div>
    </div>
  )
}
