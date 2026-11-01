import { scoreColor, scoreLabel } from '../utils/format'

/** Circular score gauge (0-100) drawn with a conic-gradient. */
export default function ScoreRing({ score = 0, size = 150, showLabel = true }) {
  const s = Math.max(0, Math.min(100, Number(score) || 0))
  const color = scoreColor(s)
  const style = {
    width: size,
    height: size,
    background: `conic-gradient(${color} ${s * 3.6}deg, rgba(255,255,255,0.08) 0deg)`,
  }
  return (
    <div className="ring-wrap">
      <div className="ring" style={style}>
        <div className="ring-label">
          <div className="n" style={{ color }}>
            {Math.round(s)}
          </div>
          <div className="u">/ 100</div>
        </div>
      </div>
      {showLabel && (
        <div className="badge" style={{ color, borderColor: color + '55' }}>
          {scoreLabel(s)}
        </div>
      )}
    </div>
  )
}
