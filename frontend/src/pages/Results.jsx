import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { interviewApi, apiError } from '../services/api'
import Loader from '../components/Loader'
import ScoreRing from '../components/ScoreRing'
import ScoreBar from '../components/ScoreBar'
import { difficultyClass, formatDate, asArray } from '../utils/format'

export default function Results() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    interviewApi
      .results(id)
      .then((res) => setData(res.data))
      .catch((err) => setError(apiError(err, 'Could not load results.')))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <Loader full large label="Compiling your interview report..." />

  if (error || !data) {
    return (
      <div className="page">
        <div className="container">
          <div className="alert alert-error">{error || 'No results found.'}</div>
          <Link to="/dashboard" className="btn btn-ghost">
            ← Back to Dashboard
          </Link>
        </div>
      </div>
    )
  }

  const { interview, feedback, qa, aggregate } = data
  const overall = interview.overall_score ?? aggregate.overall ?? 0

  const feedbackSections = [
    { title: 'Strengths', icon: '💪', key: 'strengths', tone: 'success' },
    { title: 'Weaknesses', icon: '🎯', key: 'weaknesses', tone: 'warn' },
    { title: 'Technical Improvements', icon: '🧠', key: 'technical_improvements' },
    { title: 'Communication Improvements', icon: '🗣️', key: 'communication_improvements' },
    { title: 'Non-Verbal Improvements', icon: '🎥', key: 'nonverbal_improvements' },
    { title: 'Recommendations', icon: '🚀', key: 'recommendations' },
    { title: 'Suggested Practice Topics', icon: '📚', key: 'practice_topics' },
  ]

  return (
    <div className="page">
      <div className="container">
        <div className="flex-between mb-24" style={{ flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h1 className="section-title">Interview Report</h1>
            <div className="meta-row mt-8">
              <span className="badge">{interview.category}</span>
              <span className={`badge ${difficultyClass(interview.difficulty)}`}>
                {interview.difficulty}
              </span>
              <span className="badge badge-completed">{interview.status}</span>
              <span className="faint">{formatDate(interview.completed_at || interview.created_at)}</span>
            </div>
          </div>
          <div className="flex gap-12">
            <button className="btn btn-ghost" onClick={() => navigate('/history')}>
              History
            </button>
            <button className="btn btn-primary" onClick={() => navigate('/interview/category')}>
              New Interview
            </button>
          </div>
        </div>

        {/* Overall + breakdown */}
        <div className="grid" style={{ gridTemplateColumns: '340px 1fr', gap: 20 }}>
          <div className="card card-pad flex-center" style={{ flexDirection: 'column' }}>
            <h3 className="mb-16">Overall Score</h3>
            <ScoreRing score={overall} size={170} />
            {feedback?.summary && (
              <p className="muted center mt-16" style={{ fontSize: '0.9rem' }}>
                {feedback.summary}
              </p>
            )}
          </div>

          <div className="card card-pad">
            <h3 className="mb-24">Score Breakdown</h3>
            <ScoreBar name="Answer Quality" value={aggregate.answer_quality} icon="🧠" />
            <ScoreBar name="Communication" value={aggregate.communication} icon="🗣️" />
            <ScoreBar name="Eye Contact" value={aggregate.eye_contact} icon="👁️" />
            <ScoreBar name="Posture" value={aggregate.posture} icon="🧍" />
            <ScoreBar name="Gestures" value={aggregate.gesture} icon="✋" />
          </div>
        </div>

        {/* Feedback sections */}
        {feedback && (
          <div className="grid grid-2 mt-24">
            {feedbackSections.map((s) => {
              const items = asArray(feedback[s.key]).filter(Boolean)
              if (!items.length) return null
              return (
                <div key={s.key} className="card card-pad">
                  <h3 className="mb-16">
                    {s.icon} {s.title}
                  </h3>
                  <ul style={{ paddingLeft: 4, listStyle: 'none' }}>
                    {items.map((it, i) => (
                      <li
                        key={i}
                        className="muted"
                        style={{
                          marginBottom: 10,
                          paddingLeft: 22,
                          position: 'relative',
                        }}
                      >
                        <span
                          style={{
                            position: 'absolute',
                            left: 0,
                            color:
                              s.tone === 'success'
                                ? 'var(--success)'
                                : s.tone === 'warn'
                                ? 'var(--warning)'
                                : 'var(--primary-2)',
                          }}
                        >
                          {s.tone === 'warn' ? '▹' : '✓'}
                        </span>
                        {String(it)}
                      </li>
                    ))}
                  </ul>
                </div>
              )
            })}
          </div>
        )}

        {/* Per-question transcript */}
        <div className="card card-pad mt-24">
          <h3 className="mb-16">Question-by-Question</h3>
          {qa.length === 0 ? (
            <p className="faint">No answered questions were recorded.</p>
          ) : (
            <div className="grid" style={{ gap: 14 }}>
              {qa.map((item, i) => (
                <div key={i} className="glass card-pad" style={{ padding: 18 }}>
                  <div className="flex-between" style={{ flexWrap: 'wrap', gap: 8 }}>
                    <div style={{ fontWeight: 700 }}>
                      Q{i + 1}. {item.question}
                    </div>
                    {item.evaluation && (
                      <span className="badge badge-status">
                        Overall {Math.round(item.evaluation.overall_score)}
                      </span>
                    )}
                  </div>
                  <p className="muted mt-8" style={{ fontSize: '0.92rem' }}>
                    <strong>Your answer:</strong>{' '}
                    {item.transcript ? item.transcript : <em className="faint">No transcript captured.</em>}
                  </p>
                  {item.evaluation && (
                    <div className="meta-row mt-16">
                      <span className="badge">Technical {item.evaluation.technical_score}/10</span>
                      <span className="badge">Relevance {item.evaluation.relevance_score}/10</span>
                      <span className="badge">Completeness {item.evaluation.completeness_score}/10</span>
                      <span className="badge">Clarity {item.evaluation.clarity_score}/10</span>
                    </div>
                  )}
                  {item.speech_metrics && (
                    <div className="meta-row mt-8">
                      <span className="badge">🗣️ {item.speech_metrics.words_per_minute} WPM</span>
                      <span className="badge">📝 {item.speech_metrics.word_count} words</span>
                      <span className="badge">😬 {item.speech_metrics.filler_word_count} fillers</span>
                    </div>
                  )}
                  {item.vision_metrics && item.vision_metrics.available ? (
                    <div className="meta-row mt-8">
                      <span className="badge">👁️ {Math.round(item.vision_metrics.eye_contact_percentage)}% eye contact</span>
                      <span className="badge">🧍 {Math.round(item.vision_metrics.posture_score)} posture</span>
                    </div>
                  ) : item.vision_metrics ? (
                    <div className="meta-row mt-8">
                      <span className="badge">🎥 Vision metrics unavailable</span>
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
