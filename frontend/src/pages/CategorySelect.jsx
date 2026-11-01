import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Steps from '../components/Steps'

const CATEGORIES = [
  { name: 'Software Developer', icon: '💻', desc: 'General SWE fundamentals & coding.' },
  { name: 'Frontend Developer', icon: '🎨', desc: 'UI, React, CSS, browser & UX topics.' },
  { name: 'Backend Developer', icon: '🗄️', desc: 'APIs, databases, servers & scaling.' },
  { name: 'Full Stack Developer', icon: '🧩', desc: 'End-to-end web app engineering.' },
  { name: 'Data Science', icon: '📊', desc: 'Statistics, analysis & data pipelines.' },
  { name: 'Machine Learning', icon: '🤖', desc: 'Models, training & ML system design.' },
  { name: 'General Technical', icon: '🧠', desc: 'Broad CS & problem-solving questions.' },
  { name: 'HR / Behavioral', icon: '💬', desc: 'Behavioral, STAR & culture-fit rounds.' },
]

export default function CategorySelect() {
  const navigate = useNavigate()
  const [selected, setSelected] = useState(null)

  return (
    <div className="page">
      <div className="container">
        <Steps current={1} />
        <h1 className="section-title mb-8">Choose an interview role</h1>
        <p className="muted mb-24">
          The AI interviewer will focus its questions around the role you pick.
        </p>

        <div className="choice-grid">
          {CATEGORIES.map((c) => (
            <button
              key={c.name}
              className={`choice ${selected === c.name ? 'selected' : ''}`}
              onClick={() => setSelected(c.name)}
            >
              <div className="choice-icon">{c.icon}</div>
              <div className="choice-title">{c.name}</div>
              <div className="choice-desc">{c.desc}</div>
            </button>
          ))}
        </div>

        <div className="flex-between mt-32" style={{ flexWrap: 'wrap', gap: 12 }}>
          <button className="btn btn-ghost" onClick={() => navigate('/dashboard')}>
            ← Back
          </button>
          <button
            className="btn btn-primary btn-lg"
            disabled={!selected}
            onClick={() =>
              navigate(`/interview/difficulty?category=${encodeURIComponent(selected)}`)
            }
          >
            Continue →
          </button>
        </div>
      </div>
    </div>
  )
}
