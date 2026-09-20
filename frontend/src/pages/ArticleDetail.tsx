import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowLeft, Volume2, VolumeX, Printer, Phone, AlertTriangle, ShieldCheck, LifeBuoy, Quote,
} from 'lucide-react'
import { getArticle } from '@/api/client'
import { useApp } from '@/context/AppContext'
import { ErrorState, Spinner } from '@/components/ui/Bits'

type Tab = 'story' | 'flags' | 'actions' | 'victim'

const TABS: { key: Tab; Icon: typeof Quote }[] = [
  { key: 'story', Icon: Quote },
  { key: 'flags', Icon: AlertTriangle },
  { key: 'actions', Icon: ShieldCheck },
  { key: 'victim', Icon: LifeBuoy },
]

export default function ArticleDetail() {
  const { slug = '' } = useParams()
  const { t } = useTranslation()
  const { pick, language } = useApp()
  const [tab, setTab] = useState<Tab>('story')
  const [speaking, setSpeaking] = useState(false)

  const { data: article, isLoading, isError, refetch } = useQuery({
    queryKey: ['kb-article', slug],
    queryFn: () => getArticle(slug),
  })

  // Stop any narration when leaving the page — otherwise it keeps reading in the background.
  useEffect(() => () => window.speechSynthesis?.cancel(), [])

  const ta = language === 'ta'

  const toggleSpeech = () => {
    if (!('speechSynthesis' in window) || !article) return
    if (speaking) {
      window.speechSynthesis.cancel()
      setSpeaking(false)
      return
    }
    const text = ta
      ? `${article.title_ta}. ${article.summary_ta}. ${article.body_ta}`
      : `${article.title_en}. ${article.summary_en}. ${article.body_en}`
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = ta ? 'ta-IN' : 'en-IN'
    utterance.rate = 0.92
    utterance.onend = () => setSpeaking(false)
    utterance.onerror = () => setSpeaking(false)
    window.speechSynthesis.speak(utterance)
    setSpeaking(true)
  }

  if (isLoading) return <Spinner />
  if (isError || !article) return <ErrorState onRetry={refetch} message={t('common.notFound')} />

  const flags = ta ? article.red_flags.ta : article.red_flags.en
  const actions = ta ? article.safe_actions.ta : article.safe_actions.en
  const victim = ta ? article.victim_steps.ta : article.victim_steps.en
  const example = ta ? article.real_example_ta : article.real_example_en

  return (
    <article className="space-y-5">
      <Link to="/learn" className="no-print inline-flex items-center gap-1.5 text-sm font-semibold text-brand-700 hover:underline">
        <ArrowLeft size={15} aria-hidden /> {t('nav.kb')}
      </Link>

      <header className="card p-6">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <span className="chip bg-red-100 text-red-800">{article.severity}</span>
          <span className="chip bg-slate-100 text-slate-600">{article.category}</span>
        </div>

        <h1 className={`text-2xl font-bold leading-snug text-brand-800 sm:text-3xl ${ta ? 'font-tamil' : ''}`}>
          {pick(article.title_en, article.title_ta)}
        </h1>
        <p className={`mt-3 text-lg leading-relaxed text-slate-700 ${ta ? 'font-tamil' : ''}`}>
          {pick(article.summary_en, article.summary_ta)}
        </p>

        <div className="no-print mt-5 flex flex-wrap gap-2">
          <button onClick={toggleSpeech} className="btn-ghost">
            {speaking ? <VolumeX size={16} aria-hidden /> : <Volume2 size={16} aria-hidden />}
            {speaking ? t('common.stopReading') : t('common.readAloud')}
          </button>
          <button onClick={() => window.print()} className="btn-ghost">
            <Printer size={16} aria-hidden /> {t('kb.print')}
          </button>
        </div>
      </header>

      <div className="no-print flex gap-2 overflow-x-auto pb-1" role="tablist">
        {TABS.map(({ key, Icon }) => (
          <button
            key={key}
            role="tab"
            aria-selected={tab === key}
            onClick={() => setTab(key)}
            className={`chip min-h-[42px] shrink-0 border px-4 ${ta ? 'font-tamil' : ''} ${
              tab === key
                ? 'border-brand-600 bg-brand-50 text-brand-800'
                : 'border-slate-300 bg-white text-slate-600 hover:bg-slate-50'
            }`}
          >
            <Icon size={15} aria-hidden /> {t(`kb.tabs.${key}`)}
          </button>
        ))}
      </div>

      <div className="card p-6">
        {tab === 'story' && (
          <div className="animate-fade-in">
            <div className={`prose-simple ${ta ? 'font-tamil' : ''}`}>
              {pick(article.body_en, article.body_ta)
                .split('\n\n')
                .filter(Boolean)
                .map((para, i) => <p key={i}>{para}</p>)}
            </div>

            {example && (
              <blockquote className={`mt-5 rounded-xl border-l-4 border-accent-500 bg-accent-50 p-4 ${ta ? 'font-tamil' : ''}`}>
                <p className="mb-1 text-xs font-bold uppercase tracking-wide text-accent-800">
                  {t('kb.exampleTitle')}
                </p>
                <p className="text-sm leading-relaxed text-accent-900">{example}</p>
              </blockquote>
            )}
          </div>
        )}

        {tab === 'flags' && (
          <ul className="animate-fade-in space-y-3">
            {flags.map((f, i) => (
              <li key={i} className="flex gap-3">
                <AlertTriangle size={18} className="mt-0.5 shrink-0 text-amber-600" aria-hidden />
                <span className={`text-slate-700 ${ta ? 'font-tamil' : ''}`}>{f}</span>
              </li>
            ))}
          </ul>
        )}

        {tab === 'actions' && (
          <ul className="animate-fade-in space-y-3">
            {actions.map((a, i) => (
              <li key={i} className="flex gap-3">
                <ShieldCheck size={18} className="mt-0.5 shrink-0 text-green-700" aria-hidden />
                <span className={`text-slate-700 ${ta ? 'font-tamil' : ''}`}>{a}</span>
              </li>
            ))}
          </ul>
        )}

        {tab === 'victim' && (
          <div className="animate-fade-in">
            <ol className="space-y-3">
              {victim.map((v, i) => (
                <li key={i} className="flex gap-3">
                  <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-risk-high text-xs font-bold text-white">
                    {i + 1}
                  </span>
                  <span className={`text-slate-700 ${ta ? 'font-tamil' : ''}`}>{v}</span>
                </li>
              ))}
            </ol>

            <a
              href="tel:1930"
              className="btn mt-5 bg-risk-high text-white hover:bg-red-800"
            >
              <Phone size={18} aria-hidden /> {t('helpline.call')}
            </a>
          </div>
        )}
      </div>

      <div className="card flex flex-wrap items-center gap-3 p-4 text-sm">
        <Phone size={16} className="text-risk-high" aria-hidden />
        <span className="font-semibold text-slate-700">{t('kb.helplineTitle')}:</span>
        <a href="tel:1930" className="font-bold text-risk-high hover:underline">{article.helpline}</a>
        <a
          href="https://cybercrime.gov.in"
          target="_blank"
          rel="noopener noreferrer"
          className="text-brand-700 hover:underline"
        >
          cybercrime.gov.in
        </a>
      </div>
    </article>
  )
}
