import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { resumeApi, apiError } from '../services/api'

export default function ResumeUpload() {
  const navigate = useNavigate()
  const inputRef = useRef(null)
  const [file, setFile] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // Accept common resume formats (and let the backend try its best on others).
  const ALLOWED_EXT = ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt']

  const pickFile = (f) => {
    setError('')
    if (!f) return
    const name = f.name.toLowerCase()
    if (!ALLOWED_EXT.some((ext) => name.endsWith(ext))) {
      setError('Please upload a PDF, Word (.doc/.docx), or text (.txt/.rtf) resume.')
      return
    }
    if (f.size > 10 * 1024 * 1024) {
      setError('File is too large (max 10 MB).')
      return
    }
    setFile(f)
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    pickFile(e.dataTransfer.files?.[0])
  }

  const onUpload = async () => {
    if (!file) return
    setLoading(true)
    setError('')
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await resumeApi.upload(formData)
      navigate('/profile', { state: { resume: res.data, justUploaded: true } })
    } catch (err) {
      setError(apiError(err, 'Could not process this resume.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 720 }}>
        <h1 className="section-title mb-8">Upload your resume</h1>
        <p className="muted mb-24">
          We&apos;ll parse it and tailor the interview questions to your background.
          PDF, Word (.doc/.docx) or text (.txt/.rtf) &mdash; up to 10 MB.
        </p>

        {error && <div className="alert alert-error">{error}</div>}

        {/*
          Drop zone: a REAL, transparent <input type="file"> is laid over the
          entire card. Every click anywhere on the zone is therefore a genuine
          native click on the file input — which reliably opens the OS file
          dialog in every browser (no programmatic .click(), no label proxy).
          A file input also natively accepts a dropped file, so drag & drop
          works without any custom drop handler.
        */}
        <div
          className="card"
          style={{
            position: 'relative',
            padding: 40,
            textAlign: 'center',
            borderStyle: 'dashed',
            borderColor: dragOver ? 'var(--primary)' : 'var(--border-strong)',
            transition: 'all 0.15s ease',
          }}
        >
          <div className="flex-center" style={{ marginBottom: 14 }}>
            {file ? (
              <svg width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            ) : (
              <svg width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            )}
          </div>
          {file ? (
            <>
              <div style={{ fontWeight: 700, fontSize: '1.05rem' }}>{file.name}</div>
              <div className="faint">{(file.size / 1024).toFixed(0)} KB · ready to upload</div>
            </>
          ) : (
            <>
              <div style={{ fontWeight: 700, fontSize: '1.05rem' }}>
                Drop your resume here or click to browse
              </div>
              <div className="faint">Your data stays private and secure.</div>
              <div style={{ marginTop: 16 }}>
                <span className="btn btn-ghost btn-sm" style={{ pointerEvents: 'none' }}>
                  📁 Browse files
                </span>
              </div>
            </>
          )}
          {/* NOTE: no `accept` filter — some macOS setups grey out valid PDFs
              when it's set. We validate the .pdf extension in pickFile instead. */}
          <input
            id="resume-file-input"
            ref={inputRef}
            type="file"
            style={{
              position: 'absolute',
              inset: 0,
              width: '100%',
              height: '100%',
              opacity: 0,
              cursor: 'pointer',
            }}
            onDragEnter={() => setDragOver(true)}
            onDragOver={(e) => {
              e.preventDefault()
              setDragOver(true)
            }}
            onDragLeave={() => setDragOver(false)}
            onChange={(e) => {
              setDragOver(false)
              pickFile(e.target.files?.[0])
              // Allow re-selecting the same file to fire onChange again.
              e.target.value = ''
            }}
          />
        </div>

        <div className="flex gap-12 mt-24">
          <button
            className="btn btn-primary btn-lg"
            disabled={!file || loading}
            onClick={onUpload}
          >
            {loading ? (
              <>
                <span className="spinner" /> Parsing resume...
              </>
            ) : (
              'Upload & Parse'
            )}
          </button>
          {file && !loading && (
            <button className="btn btn-ghost btn-lg" onClick={() => setFile(null)}>
              Choose another
            </button>
          )}
        </div>

        {!file && !loading && (
          <p className="faint mt-8" style={{ fontSize: '0.84rem' }}>
            Pick a file above, then this button will turn on.
          </p>
        )}

        {loading && (
          <div className="alert alert-info mt-16">
            🤖 Reading your resume and extracting your skills, projects and experience
            with AI. This usually takes <strong>20–30 seconds</strong> — please don&apos;t
            close this tab.
          </div>
        )}
      </div>
    </div>
  )
}
