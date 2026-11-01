import { useState } from 'react'
import { useNavigate, useSearchParams, Navigate } from 'react-router-dom'
import Steps from '../components/Steps'

const LEVELS = [
  {
    name: 'Easy',
    icon: '🌱',
    desc: 'Basic concepts, fundamental technical questions and simple resume clarifications.',
  },
  {
    name: 'Medium',
    icon: '🔥',
    desc: 'Intermediate concepts, project-based questions and practical real-world scenarios.',
  },
  {
    name: 'Hard',
    icon: '⚡',
    desc: 'Advanced concepts, system design, deep problem solving and challenging project questions.',
  },
]

export default function DifficultySelect() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const category = params.get('category')
  const [selected, setSelected] = useState(null)

  if (!category) return <Navigate to="/interview/category" replace />

  return (
    <div className="page">
      <div className="container">
        <Steps current={2} />
        <h1 className="section-title mb-8">Select difficulty</h1>
        <p className="muted mb-24">
          Role: <span className="badge">{category}</span> — difficulty directly shapes how
          challenging the AI&apos;s questions will be.
        </p>

        <div className="grid grid-3">
          {LEVELS.map((l) => (
            <button
              key={l.name}
              className={`choice ${selected === l.name ? 'selected' : ''}`}
              onClick={() => setSelected(l.name)}
              style={{ minHeight: 180 }}
            >
              <div className="choice-icon" style={{ fontSize: 26 }}>
                {l.icon}
              </div>
              <div className="choice-title">{l.name}</div>
              <div className="choice-desc">{l.desc}</div>
            </button>
          ))}
        </div>

        <div className="flex-between mt-32" style={{ flexWrap: 'wrap', gap: 12 }}>
          <button className="btn btn-ghost" onClick={() => navigate('/interview/category')}>
            ← Back
          </button>
          <button
            className="btn btn-primary btn-lg"
            disabled={!selected}
            onClick={() =>
              navigate(
                `/interview/setup?category=${encodeURIComponent(
                  category
                )}&difficulty=${encodeURIComponent(selected)}`
              )
            }
          >
            Continue →
          </button>
        </div>
      </div>
    </div>
  )
}
