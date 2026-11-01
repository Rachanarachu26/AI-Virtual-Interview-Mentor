import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { interviewApi, speechApi, visionApi, apiError } from '../services/api'
import { useSpeech } from '../hooks/useSpeech'
import { useMediaCapture } from '../hooks/useMediaCapture'
import { useSpeechRecognition } from '../hooks/useSpeechRecognition'

// Interview state machine.
const S = {
  SETUP: 'SETUP',
  GENERATING_QUESTION: 'GENERATING_QUESTION',
  AI_SPEAKING: 'AI_SPEAKING',
  WAITING_FOR_USER: 'WAITING_FOR_USER',
  USER_RECORDING: 'USER_RECORDING',
  ANALYZING_RESPONSE: 'ANALYZING_RESPONSE',
  GENERATING_FOLLOW_UP: 'GENERATING_FOLLOW_UP',
  INTERVIEW_COMPLETED: 'INTERVIEW_COMPLETED',
}

const STATE_META = {
  [S.GENERATING_QUESTION]: { cls: 'state-analyzing', ico: '🧠', label: 'Preparing your question...' },
  [S.GENERATING_FOLLOW_UP]: { cls: 'state-analyzing', ico: '🧠', label: 'Preparing your next question...' },
  [S.AI_SPEAKING]: { cls: 'state-speaking', ico: '🔊', label: 'AI Interviewer is speaking...' },
  [S.WAITING_FOR_USER]: { cls: 'state-waiting', ico: '🎤', label: 'Your turn to answer' },
  [S.USER_RECORDING]: { cls: 'state-recording', ico: '🔴', label: 'Listening...' },
  [S.ANALYZING_RESPONSE]: { cls: 'state-analyzing', ico: '⚙️', label: 'Analyzing your response...' },
  [S.INTERVIEW_COMPLETED]: { cls: 'state-waiting', ico: '✅', label: 'Interview complete!' },
}

export default function LiveInterview() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { speak, stop: stopSpeak, speaking, supported: ttsSupported } = useSpeech()
  const media = useMediaCapture()
  const recognition = useSpeechRecognition()

  const [state, setState] = useState(S.SETUP)
  const [question, setQuestion] = useState(null) // {id, text, number, total, is_last, type}
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [elapsed, setElapsed] = useState(0)
  const timerRef = useRef(null)
  const startedRef = useRef(false)

  // ---- Recording timer ----
  useEffect(() => {
    if (state === S.USER_RECORDING) {
      setElapsed(0)
      timerRef.current = setInterval(() => setElapsed((e) => e + 1), 1000)
    } else if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    return () => timerRef.current && clearInterval(timerRef.current)
  }, [state])

  // ---- Speak a question aloud, then hand control to the user ----
  const speakQuestion = useCallback(
    (text) => {
      setState(S.AI_SPEAKING)
      speak(text, { onEnd: () => setState(S.WAITING_FOR_USER) })
    },
    [speak]
  )

  // ---- Fetch (generate) the next question from the backend ----
  const fetchQuestion = useCallback(
    async (isFollowUp) => {
      setState(isFollowUp ? S.GENERATING_FOLLOW_UP : S.GENERATING_QUESTION)
      setError('')
      try {
        const res = await interviewApi.nextQuestion(id)
        const q = res.data
        setQuestion({
          id: q.question.id,
          text: q.question.question_text,
          type: q.question.question_type,
          number: q.question_number,
          total: q.total_questions,
          is_last: q.is_last,
        })
        speakQuestion(q.question.question_text)
      } catch (err) {
        setError(apiError(err, 'Could not generate the next question.'))
        setState(S.WAITING_FOR_USER)
      }
    },
    [id, speakQuestion]
  )

  // ---- Initialise camera/mic and begin ----
  const begin = useCallback(async () => {
    const ok = await media.init()
    if (!ok) return
    if (!ttsSupported) {
      setNotice(
        'Your browser does not support speech synthesis, so questions will be shown as text only.'
      )
    }
    await fetchQuestion(false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetchQuestion, ttsSupported])

  useEffect(() => {
    if (!startedRef.current) {
      startedRef.current = true
      begin()
    }
    return () => {
      stopSpeak()
      media.cleanup()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // ---- Recording controls ----
  const startAnswer = () => {
    if (state !== S.WAITING_FOR_USER) return
    media.startRecording()
    recognition.start() // live browser transcript (fallback for Whisper)
    setState(S.USER_RECORDING)
  }

  const stopAnswer = async () => {
    if (state !== S.USER_RECORDING) return
    setState(S.ANALYZING_RESPONSE)

    // Grab the browser's live transcript immediately (reliable fallback).
    const browserTranscript = recognition.stop()

    let audioBlob = null
    let frames = []
    let durationSec = 0
    try {
      const result = await media.stopRecording()
      audioBlob = result.audioBlob
      frames = result.frames
      durationSec = result.durationSec || 0
    } catch {
      /* ignore */
    }

    // 1) Transcribe audio (Whisper primary, browser transcript as fallback).
    let speechMetrics = null
    let transcript = ''
    try {
      const fd = new FormData()
      // Send audio if we have it; Whisper is the primary transcriber.
      if (audioBlob && audioBlob.size > 0) {
        fd.append('file', audioBlob, 'answer.webm')
      } else {
        // No audio captured — still send an (empty) file field so the endpoint
        // accepts the request and uses the browser transcript.
        fd.append('file', new Blob([], { type: 'audio/webm' }), 'answer.webm')
      }
      fd.append('fallback_transcript', browserTranscript || '')
      fd.append('duration_seconds', String(durationSec || 0))
      const res = await speechApi.transcribe(fd)
      speechMetrics = res.data
      transcript = res.data.transcript || browserTranscript || ''
    } catch {
      // Backend/transcription unreachable — fall back entirely to the browser
      // transcript so the answer is still scored.
      transcript = browserTranscript || ''
      if (!transcript) setNotice('Transcription was unavailable for this answer.')
    }

    // 2) Analyze webcam frames (MediaPipe). Failures => vision unavailable.
    let visionMetrics = null
    try {
      if (frames.length > 0) {
        const res = await visionApi.analyze(frames)
        visionMetrics = res.data
      }
    } catch {
      /* vision optional */
    }

    // 3) Submit answer + metrics for evaluation.
    const wasLast = question?.is_last
    try {
      await interviewApi.submitAnswer(id, {
        question_id: question.id,
        transcript,
        speech_metrics: speechMetrics,
        vision_metrics: visionMetrics,
      })
    } catch (err) {
      setError(apiError(err, 'Could not save your answer.'))
    }

    // 4) Next question or finish.
    if (wasLast) {
      await finishInterview()
    } else {
      await fetchQuestion(true)
    }
  }

  const finishInterview = async () => {
    setState(S.INTERVIEW_COMPLETED)
    stopSpeak()
    try {
      await interviewApi.complete(id)
    } catch {
      /* results endpoint will finalize anyway */
    }
    media.cleanup()
    setTimeout(() => navigate(`/interview/${id}/results`), 900)
  }

  const endEarly = async () => {
    if (!window.confirm('End the interview now? Answered questions will still be scored.')) {
      return
    }
    stopSpeak()
    if (state === S.USER_RECORDING) {
      try {
        recognition.stop()
        await media.stopRecording()
      } catch {
        /* ignore */
      }
    }
    await finishInterview()
  }

  const replayQuestion = () => {
    if (question?.text) speakQuestion(question.text)
  }

  const meta = STATE_META[state] || STATE_META[S.GENERATING_QUESTION]
  const progressPct = question ? (question.number / question.total) * 100 : 0

  // ---- Media permission error screen ----
  if (media.error) {
    return (
      <div className="page">
        <div className="container" style={{ maxWidth: 620 }}>
          <div className="card card-pad center">
            <div style={{ fontSize: 48, marginBottom: 12 }}>🎥🚫</div>
            <h2 className="section-title mb-8">Camera / Microphone needed</h2>
            <p className="muted mb-24">{media.error}</p>
            <div className="flex-center gap-12">
              <button className="btn btn-primary" onClick={begin}>
                Retry
              </button>
              <button className="btn btn-ghost" onClick={() => navigate('/dashboard')}>
                Back to Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="container">
        <div className="flex-between mb-16" style={{ flexWrap: 'wrap', gap: 10 }}>
          <h1 className="section-title">Live Interview</h1>
          <button className="btn btn-danger btn-sm" onClick={endEarly}>
            End Interview
          </button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {notice && <div className="alert alert-info">{notice}</div>}

        {/* Progress */}
        {question && (
          <div className="mb-16">
            <div className="flex-between mb-8">
              <span className="muted" style={{ fontSize: '0.86rem' }}>
                Question {question.number} of {question.total}
              </span>
              <span className="muted" style={{ fontSize: '0.86rem' }}>
                {Math.round(progressPct)}%
              </span>
            </div>
            <div className="progress-track">
              <span style={{ width: `${progressPct}%` }} />
            </div>
          </div>
        )}

        <div className="live-grid">
          {/* Left: AI interviewer + question */}
          <div className="interviewer-card">
            <div className="flex gap-16" style={{ alignItems: 'center' }}>
              <div className={`ai-avatar ${speaking ? 'speaking' : ''}`}>🤖</div>
              <div>
                <div style={{ fontWeight: 700, fontSize: '1.05rem' }}>AI Interviewer</div>
              </div>
            </div>

            <div className="question-text">
              {question ? `“${question.text}”` : 'Getting ready...'}
            </div>

            <div style={{ marginTop: 'auto', paddingTop: 20 }}>
              <div className={`state-chip ${meta.cls}`}>
                <span className="ico">{meta.ico}</span>
                <span>{meta.label}</span>
                {state === S.USER_RECORDING && (
                  <span className="equalizer" style={{ marginLeft: 4 }}>
                    <i /><i /><i /><i />
                  </span>
                )}
                {(state === S.GENERATING_QUESTION ||
                  state === S.GENERATING_FOLLOW_UP ||
                  state === S.ANALYZING_RESPONSE) && (
                  <span className="dots" style={{ marginLeft: 2 }}>
                    <span>.</span><span>.</span><span>.</span>
                  </span>
                )}
              </div>

              {question && state === S.WAITING_FOR_USER && ttsSupported && (
                <button className="btn btn-ghost btn-sm" style={{ marginLeft: 10 }} onClick={replayQuestion}>
                  🔁 Replay
                </button>
              )}
            </div>
          </div>

          {/* Right: webcam + controls */}
          <div>
            <div className="webcam-shell">
              <video ref={media.videoRef} autoPlay playsInline muted />
              <div className="webcam-overlay">
                <span className="cam-badge">
                  {media.recording ? (
                    <>
                      <span className="rec-dot" /> REC {formatTime(elapsed)}
                    </>
                  ) : (
                    <>🎥 Camera on</>
                  )}
                </span>
                <span className="cam-badge">
                  {state === S.USER_RECORDING ? '🎤 Mic live' : '🎤 Ready'}
                </span>
              </div>
            </div>

            <div className="controls-row">
              <button
                className="btn btn-success"
                disabled={state !== S.WAITING_FOR_USER}
                onClick={startAnswer}
              >
                ▶ Start Answer
              </button>
              <button
                className="btn btn-danger"
                disabled={state !== S.USER_RECORDING}
                onClick={stopAnswer}
              >
                ■ Stop & Submit
              </button>
            </div>

            {/* Live transcript — shows the candidate their speech is heard. */}
            {state === S.USER_RECORDING && recognition.supported && (
              <div className="card card-pad mt-16" style={{ padding: 16 }}>
                <div className="stat-label" style={{ marginBottom: 6 }}>
                  🎙️ Live transcript
                </div>
                <p style={{ margin: 0, minHeight: 24, color: recognition.interim ? 'inherit' : 'var(--muted, #888)' }}>
                  {recognition.interim || 'Listening… start speaking your answer.'}
                </p>
              </div>
            )}

            <div className="card card-pad mt-16" style={{ padding: 18 }}>
              <div className="meta-row">
                <span className="badge">📋 {question?.total || '—'} questions</span>
                {question?.type && (
                  <span className="badge badge-status">
                    {question.type === 'follow_up' ? 'Follow-up' : 'Question'}
                  </span>
                )}
              </div>
              <p className="faint mt-16" style={{ fontSize: '0.84rem' }}>
                Wait for the interviewer to finish speaking, then press{' '}
                <strong>Start Answer</strong> and speak naturally. Press{' '}
                <strong>Stop &amp; Submit</strong> when you&apos;re done.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function formatTime(sec) {
  const m = String(Math.floor(sec / 60)).padStart(2, '0')
  const s = String(sec % 60).padStart(2, '0')
  return `${m}:${s}`
}
