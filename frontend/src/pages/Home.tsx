import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import {
  MessageSquareWarning, Link2, QrCode, BookOpen, MessagesSquare,
  ShieldCheck, WifiOff, ArrowRight, TrendingUp,
} from 'lucide-react'
import { getCategories, getDashboard } from '@/api/client'
import { useApp } from '@/context/AppContext'
import { Skeleton } from '@/components/ui/Bits'

export default function Home() {
  const { t } = useTranslation()
  const { pick, language } = useApp()

  const { data: categories } = useQuery({ queryKey: ['kb-categories'], queryFn: getCategories })
  const { data: dash, isLoading: dashLoading } = useQuery({
    queryKey: ['dashboard-home'],
    queryFn: () => getDashboard(),
  })

  const stats = [
    { key: 'statWorkshops', value: dash?.totals.workshops },
    { key: 'statParticipants', value: dash?.totals.participants },
    { key: 'statMessages', value: dash?.totals.messages_analyzed },
    {
      key: 'statImprovement',
      // The median, not the mean — the mean is inflated by low pre-test denominators.
      value: dash?.awareness.median_improvement_pct,
      suffix: '%',
    },
  ]

  return (
    <div className="space-y-10">
      {/* Hero */}
      <section className="rounded-3xl bg-gradient-to-br from-brand-800 to-brand-600 px-6 py-10 text-white sm:px-10 sm:py-14">
        <div className="max-w-2xl">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold">
            <ShieldCheck size={14} aria-hidden /> {t('app.tagline')}
          </div>
          <h1 className="text-3xl font-bold leading-tight sm:text-4xl">{t('home.heroTitle')}</h1>
          <p className="mt-3 text-base leading-relaxed text-white/90 sm:text-lg">
            {t('home.heroBody')}
          </p>

          <div className="mt-6 flex flex-wrap gap-3">
            <Link to="/analyzer" className="btn bg-white text-brand-800 hover:bg-slate-100">
              <MessageSquareWarning size={18} aria-hidden /> {t('home.checkMessage')}
            </Link>
            <Link to="/url" className="btn border border-white/40 text-white hover:bg-white/10">
              <Link2 size={18} aria-hidden /> {t('home.checkLink')}
            </Link>
          </div>

          <p className="mt-5 inline-flex items-center gap-2 text-sm text-white/80">
            <WifiOff size={14} aria-hidden /> {t('home.offlineNote')}
          </p>
        </div>
      </section>

      {/* Quick tools */}
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { to: '/analyzer', Icon: MessageSquareWarning, key: 'analyzer' },
          { to: '/url', Icon: Link2, key: 'url' },
          { to: '/qr', Icon: QrCode, key: 'qr' },
          { to: '/ask', Icon: MessagesSquare, key: 'assistant' },
        ].map(({ to, Icon, key }) => (
          <Link
            key={to}
            to={to}
            className="card group flex items-center gap-3 p-5 transition-shadow hover:shadow-md"
          >
            <span className="rounded-xl bg-brand-50 p-2.5 text-brand-700">
              <Icon size={22} aria-hidden />
            </span>
            <span className="font-semibold text-slate-800">{t(`nav.${key}`)}</span>
            <ArrowRight
              size={16}
              className="ml-auto text-slate-300 transition-transform group-hover:translate-x-1"
              aria-hidden
            />
          </Link>
        ))}
      </section>

      {/* Categories */}
      <section>
        <div className="mb-4 flex items-end justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-brand-800">{t('home.exploreTitle')}</h2>
            <p className="mt-1 text-sm text-slate-600">{t('home.exploreBody')}</p>
          </div>
          <Link to="/learn" className="hidden whitespace-nowrap text-sm font-semibold text-brand-700 hover:underline sm:block">
            {t('common.readMore')} →
          </Link>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {(categories ?? []).slice(0, 8).map((c) => (
            <Link
              key={c.category}
              to={`/learn?category=${c.category}`}
              className="card flex items-center gap-3 p-4 transition-shadow hover:shadow-md"
            >
              <BookOpen size={18} className="shrink-0 text-accent-700" aria-hidden />
              <span className={`text-sm font-medium text-slate-800 ${language === 'ta' ? 'font-tamil' : ''}`}>
                {pick(c.label_en, c.label_ta)}
              </span>
            </Link>
          ))}
          {!categories && Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-16" />)}
        </div>
      </section>

      {/* Impact */}
      <section className="card p-6">
        <h2 className="mb-1 flex items-center gap-2 text-xl font-bold text-brand-800">
          <TrendingUp size={20} aria-hidden /> {t('home.statsTitle')}
        </h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map(({ key, value, suffix }) => (
            <div key={key} className="rounded-2xl bg-slate-50 p-4 text-center">
              {dashLoading ? (
                <Skeleton className="mx-auto h-9 w-20" />
              ) : (
                <p className="text-3xl font-bold text-brand-700">
                  {value ?? 0}
                  {suffix ?? ''}
                </p>
              )}
              <p className="mt-1 text-xs font-medium text-slate-600">{t(`home.${key}`)}</p>
            </div>
          ))}
        </div>
        <Link to="/dashboard" className="mt-5 inline-block text-sm font-semibold text-brand-700 hover:underline">
          {t('nav.dashboard')} →
        </Link>
      </section>

      {/* Ask */}
      <section className="rounded-3xl bg-accent-700 px-6 py-8 text-white sm:px-10">
        <h2 className="text-xl font-bold">{t('home.askTitle')}</h2>
        <p className="mt-1.5 text-white/90">{t('home.askBody')}</p>
        <Link to="/ask" className="btn mt-4 bg-white text-accent-800 hover:bg-slate-100">
          <MessagesSquare size={18} aria-hidden /> {t('nav.assistant')}
        </Link>
      </section>
    </div>
  )
}
