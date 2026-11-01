import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { interviewApi, resumeApi } from '../services/api'
import { useAuth } from '../context/AuthContext'
import Loader from '../components/Loader'
import { difficultyClass, formatDate, scoreColor } from '../utils/format'

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [history, setHistory] = useState([])
  const [resume, setResume] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true
    Promise.allSettled([interviewApi.history(), resumeApi.latest()]).then((res) => {
      if (!mounted) return
      if (res[0].status === 'fulfilled') setHistory(res[0].value.data)
      if (res[1].status === 'fulfilled') setResume(res[1].value.data)
      setLoading(false)
    })
    return () => {
      mounted = false
    }
  }, [])

  const stats = useMemo(() => {
    const completed = history.filter((h) => h.overall_score != null)
    const scores = completed.map((h) => h.overall_score)
    const avg = scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : 0
    const best = scores.length ? Math.max(...scores) : 0
    // Improvement: last score vs previous (history is newest-first).
    let improvement = null
    if (completed.length >= 2) {
      improvement = completed[0].overall_score - completed[1].overall_score
    }
    return {
      count: history.length,
      avg: Math.round(avg),
      best: Math.round(best),
      improvement,
    }
  }, [history])

  if (loading) return <Loader full label="Loading dashboard..." />

  const recent = history.slice(0, 5)

  return (
    <div className="page">
      <div className="container">
        <div className="flex-between mb-24" style={{ flexWrap: 'wrap', gap: 16 }}>
          <div>
            <h1 className="section-title">
              Welcome back, {user?.full_name?.split(' ')[0] || 'there'} 👋
            </h1>
            <p className="muted">Here&apos;s your interview practice at a glance.</p>
          </div>
          <button
            className="btn btn-primary btn-lg"
            onClick={() => navigate('/interview/category')}
          >
            🎙️ Start New Interview
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-4 mb-24">
          <StatCard label="Interviews" value={stats.count} sub="total sessions" icon="📋" />
          <StatCard
            label="Average Score"
            value={stats.count ? stats.avg : '—'}
            sub="across completed"
            icon="📊"
            color={scoreColor(stats.avg)}
          />
          <StatCard
            label="Best Score"
            value={stats.count ? stats.best : '—'}
            sub="personal best"
            icon="🏆"
            color={scoreColor(stats.best)}
          />
          <StatCard
            label="Trend"
            value={
              stats.improvement == null
                ? '—'
                : `${stats.improvement >= 0 ? '+' : ''}${Math.round(stats.improvement)}`
            }
            sub="vs previous"
            icon={stats.improvement >= 0 ? '📈' : '📉'}
            color={stats.improvement >= 0 ? '#34d399' : '#fb7185'}
          />
        </div>

        <div className="grid" style={{ gridTemplateColumns: '1.6fr 1fr', gap: 20 }}>
          {/* Recent interviews */}
          <div className="card card-pad">
            <div className="flex-between mb-16">
              <h2 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Recent Interviews</h2>
              <Link to="/history" className="nav-link">
                View all →
              </Link>
            </div>

            {recent.length === 0 ? (
              <div className="empty">
                <div className="empty-icon">🗂️</div>
                <p>No interviews yet. Start your first one to see results here.</p>
                <button
                  className="btn btn-primary mt-16"
                  onClick={() => navigate('/interview/category')}
                >
                  Start Interview
                </button>
              </div>
            ) : (
              <div className="grid" style={{ gap: 12 }}>
                {recent.map((h) => (
                  <div
                    key={h.id}
                    className="hist-row"
                    style={{ cursor: 'pointer' }}
                    onClick={() => navigate(`/interview/${h.id}/results`)}
                  >
                    <div>
                      <div style={{ fontWeight: 600 }}>{h.category}</div>
                      <div className="faint" style={{ fontSize: '0.8rem' }}>
                        {formatDate(h.created_at)}
                      </div>
                    </div>
                    <span className={`badge ${difficultyClass(h.difficulty)}`}>
                      {h.difficulty}
                    </span>
                    <span
                      className={`badge ${
                        h.status === 'completed' ? 'badge-completed' : 'badge-status'
                      }`}
                    >
                      {h.status}
                    </span>
                    <div style={{ fontWeight: 800, color: scoreColor(h.overall_score) }}>
                      {h.overall_score != null ? Math.round(h.overall_score) : '—'}
                    </div>
                    <span className="faint">→</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Resume card */}
          <div className="card card-pad">
            <h2 style={{ fontSize: '1.15rem', fontWeight: 700 }} className="mb-16">
              Your Resume
            </h2>
            {resume ? (
              <>
                <div className="glass card-pad" style={{ padding: 18 }}>
                  <div style={{ fontWeight: 700 }}>{resume.name || resume.file_name}</div>
                  {resume.email && <div className="faint">{resume.email}</div>}
                  <div className="meta-row mt-16">
                    {(resume.skills || []).slice(0, 6).map((s) => (
                      <span key={s} className="badge">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="flex gap-12 mt-16">
                  <Link to="/profile" className="btn btn-ghost btn-block">
                    View Profile
                  </Link>
                  <Link to="/resume" className="btn btn-ghost btn-block">
                    Replace
                  </Link>
                </div>
              </>
            ) : (
              <div className="empty">
                <div className="empty-icon">📄</div>
                <p>No resume uploaded yet.</p>
                <Link to="/resume" className="btn btn-primary mt-16">
                  Upload Resume
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value, sub, icon, color }) {
  return (
    <div className="stat-card">
      <div className="flex-between">
        <span className="stat-label">{label}</span>
        <span style={{ fontSize: 20 }}>{icon}</span>
      </div>
      <div className="stat-value" style={color ? { color } : undefined}>
        {value}
      </div>
      <div className="stat-sub">{sub}</div>
    </div>
  )
}
