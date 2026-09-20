import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import {
  Send, Bot, User as UserIcon, ThumbsUp, ThumbsDown, BookOpen, Sparkles, ShieldAlert,
  Mic, MicOff, Volume2, VolumeX, Copy, Check, Trash2, Phone, ExternalLink, ArrowRight,
  AlertTriangle, CornerDownRight,
} from 'lucide-react'
import { askAssistant, getSuggestions, sendAssistantFeedback } from '@/api/client'
import { useApp } from '@/context/AppContext'
import { useSpeechOutput, useVoiceInput } from '@/hooks/useSpeech'
import { FieldError, SectionTitle } from '@/components/ui/Bits'
import { assistantSchema, type AssistantForm } from '@/forms/validation'
import type { AssistantResponse, AssistantSource, QuickAction } from '@/types'

interface Message {
  id: string
  role: 'user' | 'assistant'
  text: string
  response?: AssistantResponse
  feedbackGiven?: boolean
}

const HISTORY_KEY = 'cybersathi.chat'
const MAX_HISTORY = 40

const SOURCE_STYLE: Record<AssistantSource, string> = {
  kb: 'bg-accent-100 text-accent-800',
  llm: 'bg-brand-100 text-brand-800',
  rule: 'bg-slate-100 text-slate-700',
  analyzer: 'bg-amber-100 text-amber-900',
  fallback: 'bg-slate-100 text-slate-600',
  refusal: 'bg-red-100 text-red-800',
}

function loadHistory(): Message[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed.slice(-MAX_HISTORY) : []
  } catch {
    // Private mode, or corrupt data — starting fresh is fine, never crash the page.
    return []
  }
}

function saveHistory(messages: Message[]) {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(messages.slice(-MAX_HISTORY)))
  } catch {
    /* quota or private mode — history simply does not persist */
  }
}

export default function Assistant() {
  const { t } = useTranslation()
  const { language } = useApp()
  const navigate = useNavigate()
  const ta = language === 'ta'

  const [simpleMode, setSimpleMode] = useState(false)
  const [messages, setMessages] = useState<Message[]>(loadHistory)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const endRef = useRef<HTMLDivElement>(null)

  const {
    register,
    handleSubmit,
    reset,
    setFocus,
    formState: { errors },
  } = useForm<AssistantForm>({
    resolver: zodResolver(assistantSchema),
    defaultValues: { question: '' },
  })

  const { speak, stop: stopSpeaking, speakingId, supported: ttsSupported } = useSpeechOutput()

  const { data: suggestions } = useQuery({
    queryKey: ['assistant-suggestions', language],
    queryFn: () => getSuggestions(language),
  })

  const mutation = useMutation({
    mutationFn: (question: string) => askAssistant(question, 'auto', simpleMode),
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        { id: `a${Date.now()}`, role: 'assistant', text: data.answer, response: data },
      ])
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        { id: `e${Date.now()}`, role: 'assistant', text: t('common.error') },
      ])
    },
  })

  const send = useCallback(
    (question: string) => {
      const q = question.trim()
      if (!q || mutation.isPending) return
      stopSpeaking()
      setMessages((prev) => [...prev, { id: `u${Date.now()}`, role: 'user', text: q }])
      reset({ question: '' })
      mutation.mutate(q)
    },
    [mutation, reset, stopSpeaking],
  )

  // Voice input fills the box and sends immediately — an extra tap is a real barrier for
  // the users this feature exists for.
  const voice = useVoiceInput(language, (transcript) => send(transcript))

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, mutation.isPending])

  useEffect(() => {
    saveHistory(messages)
  }, [messages])

  const giveFeedback = (id: string, helpful: boolean) => {
    const msg = messages.find((m) => m.id === id)
    if (!msg?.response?.log_id) return
    sendAssistantFeedback(msg.response.log_id, helpful).catch(() => {
      // Best-effort; never interrupt the conversation with a feedback failure.
    })
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, feedbackGiven: true } : m)))
  }

  const copyAnswer = async (id: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedId(id)
      setTimeout(() => setCopiedId(null), 1800)
    } catch {
      /* clipboard blocked — silently ignore */
    }
  }

  const clearChat = () => {
    if (messages.length && !window.confirm(t('assistant.clearConfirm'))) return
    stopSpeaking()
    setMessages([])
    try {
      localStorage.removeItem(HISTORY_KEY)
    } catch {
      /* ignore */
    }
    setFocus('question')
  }

  const runAction = (action: QuickAction) => {
    if (action.kind === 'call') window.location.assign(`tel:${action.value}`)
    else if (action.kind === 'link') window.open(action.value, '_blank', 'noopener,noreferrer')
    else navigate(action.value)
  }

  return (
    <div className="space-y-5">
      <SectionTitle title={t('assistant.title')} subtitle={t('assistant.subtitle')} />

      {/* Controls */}
      <div className="card flex flex-wrap items-center justify-between gap-3 p-4">
        <div className="flex items-center gap-3">
          <button
            id="simple-mode"
            role="switch"
            aria-checked={simpleMode}
            onClick={() => setSimpleMode((v) => !v)}
            className={`relative h-7 w-12 shrink-0 rounded-full transition-colors ${
              simpleMode ? 'bg-accent-600' : 'bg-slate-300'
            }`}
          >
            <span
              className={`absolute top-1 h-5 w-5 rounded-full bg-white transition-transform ${
                simpleMode ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
          <label htmlFor="simple-mode" className="cursor-pointer">
            <span className="block font-semibold text-slate-800">{t('assistant.simpleMode')}</span>
            <span className="block text-xs text-slate-500">{t('assistant.simpleModeHint')}</span>
          </label>
        </div>

        {messages.length > 0 && (
          <button onClick={clearChat} className="btn-ghost min-h-[40px] px-3 text-sm">
            <Trash2 size={15} aria-hidden /> {t('assistant.clearChat')}
          </button>
        )}
      </div>

      {/* Conversation */}
      <div className="card flex min-h-[440px] flex-col p-4">
        <div className="flex-1 space-y-4 overflow-y-auto" aria-live="polite">
          {messages.length === 0 && (
            <div className="flex items-start gap-3">
              <span className="rounded-xl bg-accent-100 p-2 text-accent-800">
                <Bot size={18} aria-hidden />
              </span>
              <p className={`rounded-2xl rounded-tl-sm bg-slate-100 px-4 py-3 text-slate-700 ${ta ? 'font-tamil' : ''}`}>
                {t('assistant.greeting')}
              </p>
            </div>
          )}

          {messages.map((m) =>
            m.role === 'user' ? (
              <div key={m.id} className="flex items-start justify-end gap-3">
                <p className={`max-w-[80%] rounded-2xl rounded-tr-sm bg-brand-700 px-4 py-3 text-white ${ta ? 'font-tamil' : ''}`}>
                  {m.text}
                </p>
                <span className="rounded-xl bg-brand-100 p-2 text-brand-800">
                  <UserIcon size={18} aria-hidden />
                </span>
              </div>
            ) : (
              <div key={m.id} className="flex items-start gap-3">
                <span
                  className={`rounded-xl p-2 ${
                    m.response?.urgent
                      ? 'bg-red-100 text-red-800'
                      : m.response?.source === 'refusal'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-accent-100 text-accent-800'
                  }`}
                >
                  {m.response?.urgent ? (
                    <AlertTriangle size={18} aria-hidden />
                  ) : m.response?.source === 'refusal' ? (
                    <ShieldAlert size={18} aria-hidden />
                  ) : (
                    <Bot size={18} aria-hidden />
                  )}
                </span>

                <div className="min-w-0 max-w-[85%] flex-1">
                  {/*
                    An urgent answer means the person has already lost money. It gets an alert
                    treatment so the golden-hour steps cannot be mistaken for general reading.
                  */}
                  {m.response?.urgent && (
                    <p className="mb-1.5 inline-flex items-center gap-1.5 rounded-full bg-risk-high px-3 py-1 text-xs font-bold text-white">
                      <AlertTriangle size={12} aria-hidden /> {t('assistant.urgentBadge')}
                    </p>
                  )}

                  <div
                    className={`whitespace-pre-line rounded-2xl rounded-tl-sm px-4 py-3 leading-relaxed ${
                      m.response?.urgent
                        ? 'border-2 border-red-300 bg-red-50 text-slate-900'
                        : 'bg-slate-100 text-slate-800'
                    } ${ta ? 'font-tamil' : ''}`}
                  >
                    {m.text}
                  </div>

                  {/* Quick actions */}
                  {m.response && m.response.quick_actions.length > 0 && (
                    <div className="mt-2.5 flex flex-wrap gap-2">
                      {m.response.quick_actions.map((action) => (
                        <button
                          key={`${action.kind}-${action.value}`}
                          onClick={() => runAction(action)}
                          className={`chip min-h-[38px] px-3.5 font-semibold ${ta ? 'font-tamil' : ''} ${
                            action.kind === 'call'
                              ? 'bg-risk-high text-white hover:bg-red-800'
                              : 'border border-brand-300 bg-white text-brand-800 hover:bg-brand-50'
                          }`}
                        >
                          {action.kind === 'call' && <Phone size={13} aria-hidden />}
                          {action.kind === 'link' && <ExternalLink size={13} aria-hidden />}
                          {action.kind === 'route' && <ArrowRight size={13} aria-hidden />}
                          {action.label}
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Meta row */}
                  {m.response && (
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <span className={`chip ${SOURCE_STYLE[m.response.source]}`}>
                        {t(`assistant.sources.${m.response.source}`)}
                      </span>

                      {ttsSupported && (
                        <button
                          onClick={() => speak(m.id, m.text, language)}
                          aria-label={speakingId === m.id ? t('assistant.stopReading') : t('assistant.readAnswer')}
                          title={speakingId === m.id ? t('assistant.stopReading') : t('assistant.readAnswer')}
                          className="rounded-lg p-1.5 text-slate-400 hover:bg-accent-50 hover:text-accent-700"
                        >
                          {speakingId === m.id ? <VolumeX size={15} aria-hidden /> : <Volume2 size={15} aria-hidden />}
                        </button>
                      )}

                      <button
                        onClick={() => copyAnswer(m.id, m.text)}
                        aria-label={t('assistant.copyAnswer')}
                        title={t('assistant.copyAnswer')}
                        className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                      >
                        {copiedId === m.id ? (
                          <Check size={15} className="text-green-600" aria-hidden />
                        ) : (
                          <Copy size={15} aria-hidden />
                        )}
                      </button>

                      {m.response.log_id && !m.feedbackGiven && (
                        <>
                          <span className="text-xs text-slate-400">{t('assistant.helpful')}</span>
                          <button
                            onClick={() => giveFeedback(m.id, true)}
                            aria-label={t('common.yes')}
                            className="rounded-lg p-1.5 text-slate-400 hover:bg-green-50 hover:text-green-700"
                          >
                            <ThumbsUp size={15} aria-hidden />
                          </button>
                          <button
                            onClick={() => giveFeedback(m.id, false)}
                            aria-label={t('common.no')}
                            className="rounded-lg p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-700"
                          >
                            <ThumbsDown size={15} aria-hidden />
                          </button>
                        </>
                      )}

                      {m.feedbackGiven && (
                        <span className="text-xs text-accent-700">{t('assistant.thanks')}</span>
                      )}
                    </div>
                  )}

                  {/* Related articles */}
                  {m.response && m.response.related_articles.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {m.response.related_articles.slice(0, 3).map((a) => (
                        <Link
                          key={a.slug}
                          to={`/learn/${a.slug}`}
                          className={`chip border border-slate-200 bg-white text-slate-600 hover:border-accent-400 ${ta ? 'font-tamil' : ''}`}
                        >
                          <BookOpen size={12} aria-hidden /> {a.title.slice(0, 40)}
                        </Link>
                      ))}
                    </div>
                  )}

                  {/* Contextual follow-ups — only on the newest answer, so the thread
                      does not fill with stale suggestion rows. */}
                  {m.response &&
                    m.id === messages[messages.length - 1]?.id &&
                    m.response.suggested_questions.length > 0 && (
                      <div className="mt-3">
                        <p className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold text-slate-400">
                          <CornerDownRight size={12} aria-hidden /> {t('assistant.followUp')}
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {m.response.suggested_questions.slice(0, 3).map((q) => (
                            <button
                              key={q}
                              onClick={() => send(q)}
                              className={`chip border border-accent-200 bg-accent-50 text-left text-accent-900 hover:border-accent-500 ${ta ? 'font-tamil' : ''}`}
                            >
                              {q}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                </div>
              </div>
            ),
          )}

          {mutation.isPending && (
            <div className="flex items-center gap-3">
              <span className="rounded-xl bg-accent-100 p-2 text-accent-800">
                <Bot size={18} aria-hidden />
              </span>
              <div className="flex gap-1 rounded-2xl bg-slate-100 px-4 py-4">
                {[0, 150, 300].map((delay) => (
                  <span
                    key={delay}
                    className="h-2 w-2 animate-bounce rounded-full bg-slate-400"
                    style={{ animationDelay: `${delay}ms` }}
                  />
                ))}
              </div>
            </div>
          )}

          <div ref={endRef} />
        </div>

        {/* Starter suggestions */}
        {messages.length === 0 && suggestions && (
          <div className="mt-4 border-t border-slate-100 pt-4">
            <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-slate-500">
              <Sparkles size={13} aria-hidden /> {t('assistant.suggestions')}
            </p>
            <div className="flex flex-wrap gap-2">
              {suggestions.slice(0, 5).map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className={`chip border border-slate-200 bg-white text-left text-slate-600 hover:border-accent-400 ${ta ? 'font-tamil' : ''}`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input. noValidate: zod supplies the messages, not the browser. */}
        <form
          onSubmit={handleSubmit((values) => send(values.question))}
          noValidate
          className="mt-4 border-t border-slate-100 pt-4"
        >
          <div className="flex gap-2">
            <label htmlFor="assistant-input" className="sr-only">
              {t('assistant.placeholder')}
            </label>
            <input
              id="assistant-input"
              placeholder={voice.listening ? t('assistant.listening') : t('assistant.placeholder')}
              className={`input flex-1 ${ta ? 'font-tamil' : ''} ${voice.listening ? 'border-accent-500 bg-accent-50' : ''}`}
              autoComplete="off"
              aria-invalid={errors.question ? true : undefined}
              aria-describedby={errors.question ? 'assistant-input-error' : undefined}
              {...register('question')}
            />

          {voice.supported && (
            <button
              type="button"
              onClick={voice.toggle}
              aria-label={t('assistant.voiceInput')}
              title={t('assistant.voiceInput')}
              aria-pressed={voice.listening}
              className={`btn px-4 ${
                voice.listening
                  ? 'animate-pulse bg-risk-high text-white'
                  : 'border border-slate-300 bg-white text-slate-600 hover:bg-slate-50'
              }`}
            >
              {voice.listening ? <MicOff size={18} aria-hidden /> : <Mic size={18} aria-hidden />}
            </button>
          )}

            <button type="submit" disabled={mutation.isPending} className="btn-primary px-4">
              <Send size={18} aria-hidden />
              <span className="hidden sm:inline">{t('assistant.send')}</span>
            </button>
          </div>
          <FieldError id="assistant-input-error" message={errors.question?.message} />
        </form>
      </div>
    </div>
  )
}
