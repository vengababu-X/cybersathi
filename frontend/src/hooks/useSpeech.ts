import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Browser speech input and output.
 *
 * Both matter more here than in a typical app: the target audience includes elderly and
 * low-literacy users for whom typing a question in Tamil is the main barrier to using the
 * assistant at all. Everything runs in the browser — nothing is sent to a speech service.
 *
 * Recognition support is uneven (Chrome/Edge yes, Firefox no), so callers must handle
 * `supported === false` rather than assuming a microphone is available.
 */

type SpeechRecognitionLike = {
  lang: string
  continuous: boolean
  interimResults: boolean
  start: () => void
  stop: () => void
  onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null
  onerror: (() => void) | null
  onend: (() => void) | null
}

function getRecognition(): SpeechRecognitionLike | null {
  const w = window as unknown as {
    SpeechRecognition?: new () => SpeechRecognitionLike
    webkitSpeechRecognition?: new () => SpeechRecognitionLike
  }
  const Ctor = w.SpeechRecognition ?? w.webkitSpeechRecognition
  return Ctor ? new Ctor() : null
}

export function useVoiceInput(language: 'en' | 'ta', onResult: (text: string) => void) {
  const [listening, setListening] = useState(false)
  const [supported] = useState(() => {
    const w = window as unknown as Record<string, unknown>
    return Boolean(w.SpeechRecognition ?? w.webkitSpeechRecognition)
  })
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null)
  // Kept in a ref so the recognition callbacks never go stale, but written in an effect:
  // mutating a ref during render is what the React compiler rules forbid.
  const onResultRef = useRef(onResult)
  useEffect(() => {
    onResultRef.current = onResult
  }, [onResult])

  const stop = useCallback(() => {
    try {
      recognitionRef.current?.stop()
    } catch {
      /* already stopped */
    }
    setListening(false)
  }, [])

  const start = useCallback(() => {
    if (!supported) return
    const recognition = getRecognition()
    if (!recognition) return

    recognitionRef.current = recognition
    recognition.lang = language === 'ta' ? 'ta-IN' : 'en-IN'
    recognition.continuous = false
    recognition.interimResults = false

    recognition.onresult = (e) => {
      const transcript = e.results?.[0]?.[0]?.transcript
      if (transcript) onResultRef.current(transcript)
    }
    recognition.onerror = () => setListening(false)
    recognition.onend = () => setListening(false)

    try {
      recognition.start()
      setListening(true)
    } catch {
      setListening(false)
    }
  }, [language, supported])

  // Never leave the microphone open when the user navigates away.
  useEffect(() => () => {
    try {
      recognitionRef.current?.stop()
    } catch {
      /* ignore */
    }
  }, [])

  return { listening, supported, start, stop, toggle: () => (listening ? stop() : start()) }
}

export function useSpeechOutput() {
  const [speakingId, setSpeakingId] = useState<string | null>(null)
  const supported = typeof window !== 'undefined' && 'speechSynthesis' in window

  const stop = useCallback(() => {
    if (!supported) return
    window.speechSynthesis.cancel()
    setSpeakingId(null)
  }, [supported])

  const speak = useCallback(
    (id: string, text: string, language: 'en' | 'ta') => {
      if (!supported) return
      if (speakingId === id) {
        stop()
        return
      }
      window.speechSynthesis.cancel()

      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = language === 'ta' ? 'ta-IN' : 'en-IN'
      utterance.rate = 0.92
      utterance.onend = () => setSpeakingId(null)
      utterance.onerror = () => setSpeakingId(null)

      window.speechSynthesis.speak(utterance)
      setSpeakingId(id)
    },
    [speakingId, stop, supported],
  )

  useEffect(() => () => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel()
    }
  }, [])

  return { speak, stop, speakingId, supported }
}
