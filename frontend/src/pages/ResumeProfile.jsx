import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { resumeApi } from '../services/api'
import Loader from '../components/Loader'
import { asArray } from '../utils/format'

export default function ResumeProfile() {
  const location = useLocation()
  const [resume, setResume] = useState(location.state?.resume || null)
  const [loading, setLoading] = useState(!location.state?.resume)
  const [error, setError] = useState('')

  useEffect(() => {
    if (resume) return
    resumeApi
      .latest()
      .then((res) => setResume(res.data))
      .catch(() => setError('No resume found. Please upload one first.'))
      .finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (loading) return <Loader full label="Loading resume..." />

  if (error || !resume) {
    return (
      <div className="page">
        <div className="container">
          <div className="empty">
            <div className="empty-icon">📄</div>
            <p>{error || 'No resume available.'}</p>
            <Link to="/resume" className="btn btn-primary mt-16">
              Upload Resume
            </Link>
          </div>
        </div>
      </div>
    )
  }

  const chipSections = [
    { title: 'Skills', key: 'skills', icon: '🛠️' },
    { title: 'Programming Languages', key: 'programming_languages', icon: '💻' },
    { title: 'Frameworks', key: 'frameworks', icon: '📦' },
    { title: 'Technologies', key: 'technologies', icon: '⚙️' },
  ]
  const listSections = [
    { title: 'Education', key: 'education', icon: '🎓' },
    { title: 'Experience', key: 'experience', icon: '💼' },
    { title: 'Projects', key: 'projects', icon: '🚀' },
    { title: 'Internships', key: 'internships', icon: '🧑‍💻' },
    { title: 'Certifications', key: 'certifications', icon: '📜' },
  ]

  return (
    <div className="page">
      <div className="container">
        {location.state?.justUploaded && (
          <div className="alert alert-success">
            ✅ Resume parsed successfully! Review the extracted details below.
          </div>
        )}

        <div className="flex-between mb-24" style={{ flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h1 className="section-title">{resume.name || 'Your Profile'}</h1>
            <p className="muted">
              {resume.email || resume.file_name} · Parsed from your resume
            </p>
          </div>
          <Link to="/interview/category" className="btn btn-primary">
            Start Interview →
          </Link>
        </div>

        {resume.summary && (
          <div className="card card-pad mb-24">
            <h3 className="mb-8">Summary</h3>
            <p className="muted">{resume.summary}</p>
          </div>
        )}

        <div className="grid grid-2 mb-24">
          {chipSections.map((s) => {
            const items = asArray(resume[s.key]).filter(Boolean)
            return (
              <div key={s.key} className="card card-pad">
                <h3 className="mb-16">
                  {s.icon} {s.title}
                </h3>
                {items.length ? (
                  <div className="meta-row">
                    {items.map((it, i) => (
                      <span key={i} className="badge">
                        {String(it)}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="faint">Not detected.</p>
                )}
              </div>
            )
          })}
        </div>

        <div className="grid grid-2">
          {listSections.map((s) => {
            const items = asArray(resume[s.key]).filter(Boolean)
            return (
              <div key={s.key} className="card card-pad">
                <h3 className="mb-16">
                  {s.icon} {s.title}
                </h3>
                {items.length ? (
                  <ul style={{ paddingLeft: 18, color: 'var(--text-dim)' }}>
                    {items.map((it, i) => (
                      <li key={i} style={{ marginBottom: 6 }}>
                        {String(it)}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="faint">Not detected.</p>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
