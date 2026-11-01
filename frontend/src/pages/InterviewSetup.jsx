import { useEffect, useState } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import Steps from '../components/Steps'
import Loader from '../components/Loader'
import { interviewApi, resumeApi, apiError } from '../services/api'
import { difficultyClass } from '../utils/format'

export default function InterviewSetup() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const category = params.get('category')
  const difficulty = params.get('difficulty')

  const [resume, setResume] = useState(null)
  const [loadingResume, setLoadingResume] = useState(true)
  const [numQuestions, setNumQuestions] = useState(5)
  const [error, setError] = useState('')
  const [starting, setStarting] = useState(false)

  useEffect(() => {
    resumeApi
      .latest()
      .then((res) => setResume(res.data))
      .catch(() => setResume(null))
      .finally(() => setLoadingResume(false))
  }, [])

  if (!category || !difficulty) return <Navigate to="/interview/category" replace />

  const start = async () => {
    setStarting(true)
    setError('')
    try {
      const res = await interviewApi.create({
        category,
        difficulty,
        total_questions: numQuestions,
        resume_id: resume?.id || null,
      })
      navigate(`/interview/${res.data.id}/live`)
    } catch (err) {
      setError(apiError(err, 'Could not start the interview.'))
      setStarting(false)
    }
  }

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 820 }}>
        <Steps current={3} />
        <h1 className="section-title mb-8">Review & start</h1>
        <p className="muted mb-24">Confirm your setup, then begin your spoken AI interview.</p>

        {error && <div className="alert alert-error">{error}</div>}

        <div className="grid grid-2 mb-24">
          <div className="card card-pad">
            <div className="stat-label">Role</div>
            <div style={{ fontSize: '1.3rem', fontWeight: 700, marginTop: 6 }}>
              {category}
            </div>
          </div>
          <div className="card card-pad">
            <div className="stat-label">Difficulty</div>
            <div style={{ marginTop: 10 }}>
              <span className={`badge ${difficultyClass(difficulty)}`} style={{ fontSize: '0.95rem', padding: '6px 16px' }}>
                {difficulty}
              </span>
            </div>
          </div>
        </div>

        <div className="card card-pad mb-24">
          <label className="label" htmlFor="numQuestions">Number of questions</label>
          <select
            id="numQuestions"
            className="select"
            value={numQuestions}
            onChange={(e) => setNumQuestions(Number(e.target.value))}
            style={{ maxWidth: 260 }}
          >
            {[5, 10, 15, 20, 25].map((n) => (
              <option key={n} value={n}>
                {n} questions
              </option>
            ))}
          </select>
          <p className="faint mt-8" style={{ fontSize: '0.82rem' }}>
            The interviewer will ask this many questions, adapting each one to your answers.
          </p>
        </div>

        <div className="card card-pad mb-24">
          <div className="flex-between" style={{ flexWrap: 'wrap', gap: 10 }}>
            <div>
              <div style={{ fontWeight: 700 }}>Resume context</div>
              {loadingResume ? (
                <div className="faint">Checking...</div>
              ) : resume ? (
                <div className="muted">
                  Using <strong>{resume.name || resume.file_name}</strong> to personalize
                  questions.
                </div>
              ) : (
                <div className="muted">
                  No resume found — questions will use the role & difficulty only.
                </div>
              )}
            </div>
            <Link to="/resume" className="btn btn-ghost btn-sm">
              {resume ? 'Change' : 'Upload'}
            </Link>
          </div>
        </div>

        <div className="alert alert-info">
          🎧 Make sure your <strong>microphone and camera</strong> are ready. The AI
          interviewer will speak each question aloud — please use speakers or headphones.
        </div>

        <div className="flex-between mt-24" style={{ flexWrap: 'wrap', gap: 12 }}>
          <button
            className="btn btn-ghost"
            onClick={() =>
              navigate(`/interview/difficulty?category=${encodeURIComponent(category)}`)
            }
          >
            ← Back
          </button>
          <button className="btn btn-primary btn-lg" onClick={start} disabled={starting}>
            {starting ? (
              <>
                <span className="spinner" /> Starting...
              </>
            ) : (
              '🎙️ Begin Interview'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
