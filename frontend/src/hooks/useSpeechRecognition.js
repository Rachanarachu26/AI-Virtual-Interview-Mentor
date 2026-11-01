import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Live browser speech-to-text using the Web Speech API (SpeechRecognition).
 *
 * This runs IN THE BROWSER while the candidate answers and captures a reliable
 * transcript in real time. Whisper (on the backend) is still the primary
 * transcriber for metrics, but this transcript is sent along as a FALLBACK so
 * that a real spoken answer is never scored as empty when Whisper cannot decode
 * the recorded audio. Gracefully no-ops in browsers without support (e.g. some
 * Firefox builds) — the interview still works via Whisper only.
 */
export function useSpeechRecognition() {
  const SpeechRecognition =
    typeof window !== 'undefined'
      ? window.SpeechRecognition || window.webkitSpeechRecognition
      : null

  const supported = !!SpeechRecognition
  const [interim, setInterim] = useState('')
  const recognitionRef = useRef(null)
  const finalRef = useRef('')
  const listeningRef = useRef(false)

  const start = useCallback(() => {
    if (!SpeechRecognition) return
    // Reset transcript for this answer.
    finalRef.current = ''
    setInterim('')

    try {
      const rec = new SpeechRecognition()
      rec.lang = 'en-US'
      rec.continuous = true
      rec.interimResults = true

      rec.onresult = (event) => {
        let interimText = ''
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const res = event.results[i]
          const txt = res[0]?.transcript || ''
          if (res.isFinal) {
            finalRef.current = (finalRef.current + ' ' + txt).trim()
          } else {
            interimText += txt
          }
        }
        setInterim(interimText)
      }

      rec.onerror = () => {
        /* ignore: no-speech / audio-capture errors shouldn't break the flow */
      }

      rec.onend = () => {
        // Auto-restart if we're still supposed to be listening (recognition
        // stops on its own after pauses in some browsers).
        if (listeningRef.current) {
          try {
            rec.start()
          } catch {
            /* already started / not allowed */
          }
        }
      }

      recognitionRef.current = rec
      listeningRef.current = true
      rec.start()
    } catch {
      recognitionRef.current = null
      listeningRef.current = false
    }
  }, [SpeechRecognition])

  /** Stop listening and return the full recognized transcript. */
  const stop = useCallback(() => {
    listeningRef.current = false
    const rec = recognitionRef.current
    if (rec) {
      try {
        rec.stop()
      } catch {
        /* ignore */
      }
    }
    recognitionRef.current = null
    const merged = (finalRef.current + ' ' + interim).trim()
    setInterim('')
    return merged
  }, [interim])

  useEffect(() => {
    return () => {
      listeningRef.current = false
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop()
        } catch {
          /* ignore */
        }
      }
    }
  }, [])

  return { supported, interim, start, stop }
}
