import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import {
  BookOpen, CheckCircle2, Circle, GraduationCap, Printer, AlertTriangle, ArrowRight,
} from 'lucide-react'
import { getCategories } from '@/api/client'
import { useApp } from '@/context/AppContext'

/** Category slug -> knowledge-base article, so each topic links to what to actually teach. */
const CATEGORY_ARTICLE: Record<string, string> = {
  otp: 'otp-scams',
  kyc: 'kyc-scams',
  job: 'job-scams',
  investment: 'investment-scams',
  banking: 'banking-scams',
  loan: 'loan-scams',
  impersonation: 'impersonation-scams',
  social_media: 'social-media-scams',
  digital_arrest: 'digital-arrest-scams',
  courier_parcel: 'courier-parcel-scams',
  lottery: 'lottery-prize-scams',
  phishing: 'kyc-scams',
  general: 'otp-scams',
}

interface Props {
  /** Categories the participant answered poorly on — taught first. */
  weakCategories: string[]
  onStartPostTest: () => void
}

/**
 * The awareness campaign: the intervention that sits between the pre-test and the post-test.
 *
 * Without this step the app measures a change it never helped cause. The pre-test already
 * says which topics this participant does not know, so the weak ones are pulled to the top
 * and marked — a facilitator with fifteen minutes should spend them where they count.
 */
export default function CampaignChecklist({ weakCategories, onStartPostTest }: Props) {
  const { t } = useTranslation()
  const { pick, language } = useApp()
  const ta = language === 'ta'

  const { data: categories } = useQuery({ queryKey: ['kb-categories'], queryFn: getCategories })
  const [covered, setCovered] = useState<Set<string>>(new Set())

  const ordered = useMemo(() => {
    if (!categories) return []
    const weak = new Set(weakCategories)
    // Weak topics first, then the rest in their usual order.
    return [...categories].sort((a, b) => {
      const aw = weak.has(a.category) ? 0 : 1
      const bw = weak.has(b.category) ? 0 : 1
      return aw - bw || a.category.localeCompare(b.category)
    })
  }, [categories, weakCategories])

  const toggle = (category: string) => {
    setCovered((prev) => {
      const next = new Set(prev)
      if (next.has(category)) next.delete(category)
      else next.add(category)
      return next
    })
  }

  const weakSet = new Set(weakCategories)
  const progress = ordered.length ? Math.round((covered.size / ordered.length) * 100) : 0

  return (
    <div className="space-y-5">
      <div className="card p-6">
        <h2 className={`flex items-center gap-2 text-xl font-bold text-brand-800 ${ta ? 'font-tamil' : ''}`}>
          <GraduationCap size={22} aria-hidden /> {t('campaign.title')}
        </h2>
        <p className={`mt-1.5 text-slate-600 ${ta ? 'font-tamil' : ''}`}>{t('campaign.subtitle')}</p>

        {weakCategories.length > 0 && (
          <div className="mt-4 flex gap-3 rounded-xl bg-amber-50 p-4">
            <AlertTriangle size={18} className="mt-0.5 shrink-0 text-amber-700" aria-hidden />
            <p className={`text-sm leading-relaxed text-amber-900 ${ta ? 'font-tamil' : ''}`}>
              {t('campaign.weakNote', { count: weakCategories.length })}
            </p>
          </div>
        )}

        <div className="mt-5">
          <div className="mb-1.5 flex items-center justify-between text-xs font-semibold text-slate-500">
            <span className={ta ? 'font-tamil' : ''}>{t('campaign.progress')}</span>
            <span>{covered.size} / {ordered.length}</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-slate-200">
            <div
              className="h-full rounded-full bg-accent-600 transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      <ul className="space-y-2">
        {ordered.map((c) => {
          const done = covered.has(c.category)
          const isWeak = weakSet.has(c.category)
          const slug = CATEGORY_ARTICLE[c.category]

          return (
            <li
              key={c.category}
              className={`card flex items-center gap-3 p-4 transition-colors ${
                done ? 'bg-accent-50' : isWeak ? 'border-amber-300' : ''
              }`}
            >
              <button
                onClick={() => toggle(c.category)}
                aria-pressed={done}
                aria-label={t('campaign.markCovered')}
                className="shrink-0 rounded-lg p-1"
              >
                {done
                  ? <CheckCircle2 size={24} className="text-accent-600" aria-hidden />
                  : <Circle size={24} className="text-slate-300" aria-hidden />}
              </button>

              <div className="min-w-0 flex-1">
                <p className={`font-semibold text-slate-800 ${done ? 'line-through opacity-60' : ''} ${ta ? 'font-tamil' : ''}`}>
                  {pick(c.label_en, c.label_ta)}
                </p>
                {isWeak && (
                  <span className={`chip mt-1 bg-amber-100 text-amber-900 ${ta ? 'font-tamil' : ''}`}>
                    {t('campaign.priority')}
                  </span>
                )}
              </div>

              {slug && (
                <Link
                  to={`/learn/${slug}`}
                  className={`chip shrink-0 border border-brand-200 bg-white text-brand-800 hover:bg-brand-50 ${ta ? 'font-tamil' : ''}`}
                >
                  <BookOpen size={13} aria-hidden /> {t('campaign.teachThis')}
                </Link>
              )}
            </li>
          )
        })}
      </ul>

      <div className="card p-5">
        <h3 className={`font-bold text-brand-800 ${ta ? 'font-tamil' : ''}`}>{t('campaign.remember')}</h3>
        <ul className={`mt-2 list-disc space-y-1.5 pl-5 text-sm text-slate-700 ${ta ? 'font-tamil' : ''}`}>
          <li>{t('campaign.tipDemo')}</li>
          <li>{t('campaign.tipAsk')}</li>
          <li>{t('campaign.tipShame')}</li>
          <li>{t('campaign.tipHelpline')}</li>
        </ul>

        <div className="mt-5 flex flex-wrap gap-3">
          <button onClick={onStartPostTest} className="btn-accent">
            <ArrowRight size={18} aria-hidden /> {t('campaign.startPost')}
          </button>
          <button onClick={() => window.print()} className="btn-ghost no-print">
            <Printer size={16} aria-hidden /> {t('campaign.print')}
          </button>
        </div>

        {covered.size < ordered.length && (
          <p className={`mt-3 text-xs text-slate-500 ${ta ? 'font-tamil' : ''}`}>
            {t('campaign.canProceed')}
          </p>
        )}
      </div>
    </div>
  )
}
