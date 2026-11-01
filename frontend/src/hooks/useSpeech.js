import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Text-to-Speech hook using the browser Web Speech API (window.speechSynthesis).
 * The AI interviewer uses this to SPEAK each question aloud.
 */
// Deterministic preference order so the AI interviewer ALWAYS uses the same
// voice (avoids the male/female flip when voices load at different times).
// Listed best-first; we lock onto the first one that exists on the device.
const PREFERRED_VOICES = [
  'Google US English',
  'Samantha',
  'Microsoft Aria Online (Natural) - English (United States)',
  'Microsoft Jenny Online (Natural) - English (United States)',
  'Microsoft Zira - English (United States)',
  'Karen',
  'Moira',
  'Tessa',
]

export function useSpeech() {
  const [speaking, setSpeaking] = useState(false)
  const [supported, setSupported] = useState(true)
  const voiceRef = useRef(null)

  const pickVoice = () => {
    if (voiceRef.current) return voiceRef.current // lock: never change once chosen
    const voices = window.speechSynthesis ? window.speechSynthesis.getVoices() : []
    if (!voices.length) return null
    let chosen = null
    // 1) Exact match against our preferred list (best, consistent voices).
    for (const name of PREFERRED_VOICES) {
      chosen = voices.find((v) => v.name === name)
      if (chosen) break
    }
    // 2) Any English voice whose name hints it is a natural/female voice.
    if (!chosen) {
      chosen = voices.find(
        (v) => /^en(-|_|$)/i.test(v.lang) && /female|aria|jenny|samantha|zira|natural/i.test(v.name)
      )
    }
    // 3) Any US English, then any English, then the first available.
    if (!chosen) chosen = voices.find((v) => /en-US/i.test(v.lang))
    if (!chosen) chosen = voices.find((v) => /^en(-|_|$)/i.test(v.lang))
    if (!chosen) chosen = voices[0]
    voiceRef.current = chosen || null
    return voiceRef.current
  }

  useEffect(() => {
    if (typeof window === 'undefined' || !window.speechSynthesis) {
      setSupported(false)
      return
    }
    pickVoice()
    window.speechSynthesis.onvoiceschanged = pickVoice
    return () => {
      window.speechSynthesis.onvoiceschanged = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const speak = useCallback(
    (text, { onEnd } = {}) => {
      if (!window.speechSynthesis || !text) {
        if (onEnd) onEnd()
        return
      }
      // Cancel anything in progress.
      window.speechSynthesis.cancel()

      const utterance = new SpeechSynthesisUtterance(text)
      utterance.rate = 0.95
      utterance.pitch = 1
      utterance.volume = 1
      utterance.lang = 'en-US'
      // Ensure a voice is chosen even on the very first question (voices may
      // have loaded only just now) — same voice for every question thereafter.
      const v = voiceRef.current || pickVoice()
      if (v) utterance.voice = v

      utterance.onstart = () => setSpeaking(true)
      utterance.onend = () => {
        setSpeaking(false)
        if (onEnd) onEnd()
      }
      utterance.onerror = () => {
        setSpeaking(false)
        if (onEnd) onEnd()
      }

      // Small timeout works around a Chrome bug where speak() is dropped
      // if called immediately after cancel().
      setTimeout(() => window.speechSynthesis.speak(utterance), 60)
    },
    []
  )

  const stop = useCallback(() => {
    if (window.speechSynthesis) window.speechSynthesis.cancel()
    setSpeaking(false)
  }, [])

  return { speak, stop, speaking, supported }
}
