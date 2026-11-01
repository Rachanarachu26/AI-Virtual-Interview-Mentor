import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { interviewApi, apiError } from '../services/api'
import Loader from '../components/Loader'
import { difficultyClass, formatDate, scoreColor } from '../utils/format'

export default function History() {
  const navigate = useNavigate()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    interviewApi
      .history()
      .then((res) => setItems(res.data))
      .catch((err) => setError(apiError(err)))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Loader full label="Loading your history..." />

  return (
    <div className="page">
      <div className="container">
        <div className="flex-between mb-24" style={{ flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h1 className="section-title">Interview History</h1>
            <p className="muted">Review and revisit every practice session.</p>
          </div>
          <button className="btn btn-primary" onClick={() => navigate('/interview/category')}>
            🎙️ New Interview
          </button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {items.length === 0 ? (
          <div className="card card-pad">
            <div className="empty">
              <div className="empty-icon">🗂️</div>
              <p>You haven&apos;t completed any interviews yet.</p>
              <Link to="/interview/category" className="btn btn-primary mt-16">
                Start your first interview
              </Link>
            </div>
          </div>
        ) : (
          <div className="grid" style={{ gap: 12 }}>
            {items.map((h) => (
              <div
                key={h.id}
                className="hist-row"
                style={{ cursor: 'pointer' }}
                onClick={() => navigate(`/interview/${h.id}/results`)}
              >
                <div>
                  <div style={{ fontWeight: 700 }}>{h.category}</div>
                  <div className="faint" style={{ fontSize: '0.8rem' }}>
                    {formatDate(h.created_at)}
                  </div>
                </div>
                <span className={`badge ${difficultyClass(h.difficulty)}`}>{h.difficulty}</span>
                <span
                  className={`badge ${
                    h.status === 'completed' ? 'badge-completed' : 'badge-status'
                  }`}
                >
                  {h.status}
                </span>
                <div
                  style={{
                    fontWeight: 800,
                    fontSize: '1.15rem',
                    color: scoreColor(h.overall_score),
                  }}
                >
                  {h.overall_score != null ? Math.round(h.overall_score) : '—'}
                </div>
                <span className="btn btn-ghost btn-sm">View report →</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
