import { useCallback, useRef, useState } from 'react'

/**
 * Manages the webcam + microphone stream, audio recording (MediaRecorder),
 * and periodic webcam frame capture (for computer-vision analysis).
 */
export function useMediaCapture() {
  const [ready, setReady] = useState(false)
  const [error, setError] = useState('')
  const [recording, setRecording] = useState(false)

  const streamRef = useRef(null)
  const videoRef = useRef(null)
  const recorderRef = useRef(null)
  const chunksRef = useRef([])
  const framesRef = useRef([])
  const frameTimerRef = useRef(null)
  const startTimeRef = useRef(0)

  const init = useCallback(async () => {
    setError('')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' },
        audio: true,
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play().catch(() => {})
      }
      setReady(true)
      return true
    } catch (err) {
      let msg = 'Could not access camera/microphone.'
      if (err && (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError')) {
        msg = 'Camera/microphone permission was denied. Please allow access and refresh.'
      } else if (err && err.name === 'NotFoundError') {
        msg = 'No camera or microphone was found on this device.'
      }
      setError(msg)
      setReady(false)
      return false
    }
  }, [])

  const captureFrame = useCallback(() => {
    const video = videoRef.current
    if (!video || video.videoWidth === 0) return
    const canvas = document.createElement('canvas')
    canvas.width = 320
    canvas.height = 240
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    try {
      const dataUrl = canvas.toDataURL('image/jpeg', 0.6)
      if (framesRef.current.length < 15) {
        framesRef.current.push(dataUrl)
      }
    } catch {
      /* ignore capture errors */
    }
  }, [])

  const startRecording = useCallback(() => {
    if (!streamRef.current) return
    chunksRef.current = []
    framesRef.current = []

    // Audio recorder.
    let mimeType = ''
    const candidates = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4']
    for (const c of candidates) {
      if (window.MediaRecorder && MediaRecorder.isTypeSupported(c)) {
        mimeType = c
        break
      }
    }
    try {
      const recorder = new MediaRecorder(
        streamRef.current,
        mimeType ? { mimeType } : undefined
      )
      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data)
      }
      // Use a 1s timeslice so audio chunks flush during recording — some
      // browsers otherwise deliver nothing for short answers, which would
      // make Whisper receive an empty/broken file.
      recorder.start(1000)
      recorderRef.current = recorder
    } catch {
      recorderRef.current = null
    }

    startTimeRef.current = Date.now()

    // Capture webcam frames every 800ms for CV analysis.
    captureFrame()
    frameTimerRef.current = setInterval(captureFrame, 800)

    setRecording(true)
  }, [captureFrame])

  const stopRecording = useCallback(() => {
    return new Promise((resolve) => {
      if (frameTimerRef.current) {
        clearInterval(frameTimerRef.current)
        frameTimerRef.current = null
      }
      const frames = [...framesRef.current]
      const recorder = recorderRef.current
      const durationSec = startTimeRef.current
        ? Math.round((Date.now() - startTimeRef.current) / 100) / 10
        : 0

      const finish = () => {
        setRecording(false)
        const blob = new Blob(chunksRef.current, {
          type: chunksRef.current[0]?.type || 'audio/webm',
        })
        resolve({ audioBlob: blob, frames, durationSec })
      }

      if (recorder && recorder.state !== 'inactive') {
        recorder.onstop = finish
        recorder.stop()
      } else {
        finish()
      }
    })
  }, [])

  const cleanup = useCallback(() => {
    if (frameTimerRef.current) clearInterval(frameTimerRef.current)
    if (recorderRef.current && recorderRef.current.state !== 'inactive') {
      try {
        recorderRef.current.stop()
      } catch {
        /* ignore */
      }
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
    setReady(false)
    setRecording(false)
  }, [])

  return {
    ready,
    error,
    recording,
    videoRef,
    init,
    startRecording,
    stopRecording,
    cleanup,
  }
}
