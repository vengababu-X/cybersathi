import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { Download, FileText, Info, Users, CalendarCheck, MessageSquare, Link2, TrendingUp } from 'lucide-react'
import { exportUrl, getDashboard } from '@/api/client'
import { useApp } from '@/context/AppContext'
import { EmptyState, SectionTitle, Spinner } from '@/components/ui/Bits'

const RISK_COLORS: Record<string, string> = {
  safe: '#15803d',
  suspicious: '#b45309',
  high_risk: '#b91c1c',
}

function Kpi({ label, value, Icon, accent }: {
  label: string; value: string | number; Icon: typeof Users; accent?: boolean
}) {
  return (
    <div className={`card p-4 ${accent ? 'bg-accent-50' : ''}`}>
      <div className="flex items-center gap-2 text-slate-500">
        <Icon size={15} aria-hidden />
        <span className="text-xs font-medium">{label}</span>
      </div>
      <p className={`mt-2 text-2xl font-bold ${accent ? 'text-accent-700' : 'text-brand-700'}`}>
        {value}
      </p>
    </div>
  )
}

export default function Dashboard() {
  const { t } = useTranslation()
  const { language, pick } = useApp()
  const [district, setDistrict] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['dashboard', district],
    queryFn: () => getDashboard(district ? { district } : undefined),
  })

  const ta = language === 'ta'

  if (isLoading) return <Spinner />
  if (!data) return <EmptyState message={t('dashboard.noData')} />

  const a = data.awareness
  const districts = Array.from(new Set(data.by_district.map((d) => d.group)))

  const categoryData = data.improvement_by_category.map((c) => ({
    name: c.category.replace(/_/g, ' ').slice(0, 12),
    [t('dashboard.charts.pre')]: c.pre,
    [t('dashboard.charts.post')]: c.post,
  }))

  const riskData = Object.entries(data.risk_distribution).map(([key, value]) => ({
    name: t(`risk.${key}`),
    value,
    key,
  }))

  const ageData = data.by_age_group.map((g) => ({
    name: t(`workshops.ages.${g.group}`, { defaultValue: g.group }),
    [t('dashboard.charts.pre')]: g.avg_pre,
    [t('dashboard.charts.post')]: g.avg_post,
  }))

  return (
    <div className="space-y-6">
      <SectionTitle title={t('dashboard.title')} subtitle={t('dashboard.subtitle')} />

      {/* Filters */}
      <div className="card flex flex-wrap items-end gap-4 p-4">
        <div>
          <label htmlFor="district" className="mb-1 block text-xs font-semibold text-slate-600">
            {t('dashboard.district')}
          </label>
          <select
            id="district"
            value={district}
            onChange={(e) => setDistrict(e.target.value)}
            className="input min-w-[180px]"
          >
            <option value="">{t('common.all')}</option>
            {districts.map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
        </div>

        {/* The PDF is the printable artefact for the project appendix: it carries the
            statistics and the mean-skew caveat together, so the number is never quoted bare. */}
        <div className="ml-auto flex flex-wrap gap-2">
          <a href={exportUrl('pdf', district || undefined)} className="btn-accent" download>
            <FileText size={16} aria-hidden /> {t('dashboard.exportPdf')}
          </a>
          <a href={exportUrl('csv', district || undefined)} className="btn-ghost" download>
            <Download size={16} aria-hidden /> {t('dashboard.exportCsv')}
          </a>
          <a href={exportUrl('json', district || undefined)} className="btn-ghost" download>
            <Download size={16} aria-hidden /> {t('dashboard.exportJson')}
          </a>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Kpi label={t('dashboard.kpi.workshops')} value={data.totals.workshops} Icon={CalendarCheck} />
        <Kpi label={t('dashboard.kpi.participants')} value={data.totals.participants} Icon={Users} />
        <Kpi label={t('dashboard.kpi.messages')} value={data.totals.messages_analyzed} Icon={MessageSquare} />
        <Kpi label={t('dashboard.kpi.urls')} value={data.totals.urls_checked} Icon={Link2} />
        <Kpi
          label={t('dashboard.kpi.avgImprovement')}
          value={a.median_improvement_pct !== null ? `${a.median_improvement_pct}%` : '—'}
          Icon={TrendingUp}
          accent
        />
        <Kpi
          label={t('dashboard.kpi.effectSize')}
          value={a.cohens_d ?? '—'}
          Icon={TrendingUp}
          accent
        />
        <Kpi
          label={t('dashboard.kpi.movedToAware')}
          value={a.moved_to_aware_pct !== null ? `${a.moved_to_aware_pct}%` : '—'}
          Icon={Users}
          accent
        />
        <Kpi label={t('dashboard.nPairs')} value={a.n_pairs} Icon={Users} />
      </div>

      {/*
        The mean improvement is inflated by participants with very low pre-test scores
        (1/10 -> 5/10 reads as +400%). The backend flags this; we surface the warning
        rather than letting the headline number stand alone.
      */}
      {a.interpretation_note && (
        <div className="card flex gap-3 border-l-4 border-amber-400 bg-amber-50 p-4">
          <Info size={18} className="mt-0.5 shrink-0 text-amber-700" aria-hidden />
          <div>
            <p className="text-sm font-semibold text-amber-900">{t('dashboard.interpretNote')}</p>
            <p className={`mt-1 text-sm leading-relaxed text-amber-900 ${ta ? 'font-tamil' : ''}`}>
              {pick(a.interpretation_note.en, a.interpretation_note.ta)}
            </p>
          </div>
        </div>
      )}

      {/* Formula + stats */}
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card p-5">
          <h3 className="mb-3 font-bold text-brand-800">{t('dashboard.formulaTitle')}</h3>
          <div className="rounded-xl bg-slate-50 p-4 text-center font-mono text-sm text-slate-700">
            ((post − pre) / pre) × 100
          </div>
          <dl className="mt-4 space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-slate-600">{t('assessment.preScore')}</dt>
              <dd className="font-semibold">{a.avg_pre_pct ?? '—'}%</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-600">{t('assessment.postScore')}</dt>
              <dd className="font-semibold">{a.avg_post_pct ?? '—'}%</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-600">{t('dashboard.undefinedCount')}</dt>
              <dd className="font-semibold text-amber-700">{a.undefined_improvement_count}</dd>
            </div>
          </dl>
        </div>

        <div className="card p-5">
          <h3 className="mb-3 font-bold text-brand-800">{t('dashboard.statsTitle')}</h3>
          <dl className="space-y-2 text-sm">
            {[
              [t('dashboard.tStatistic'), a.t_statistic],
              [t('dashboard.pValue'), a.p_value !== null ? (a.p_value < 0.001 ? '< 0.001' : a.p_value) : null],
              [t('dashboard.cohensD'), a.cohens_d],
              [t('dashboard.nPairs'), a.n_pairs],
            ].map(([label, value]) => (
              <div key={String(label)} className="flex justify-between border-b border-slate-100 pb-2">
                <dt className="text-slate-600">{label}</dt>
                <dd className="font-mono font-semibold text-slate-900">{value ?? '—'}</dd>
              </div>
            ))}
          </dl>
        </div>
      </div>

      {/* Charts */}
      <div className="card p-5">
        <h3 className={`mb-4 font-bold text-brand-800 ${ta ? 'font-tamil' : ''}`}>
          {t('dashboard.charts.categoryTitle')}
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={categoryData} margin={{ top: 5, right: 5, bottom: 40, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="name" angle={-35} textAnchor="end" height={70} tick={{ fontSize: 11 }} />
            <YAxis unit="%" tick={{ fontSize: 11 }} />
            <Tooltip />
            <Legend />
            <Bar dataKey={t('dashboard.charts.pre')} fill="#94a3b8" radius={[4, 4, 0, 0]} />
            <Bar dataKey={t('dashboard.charts.post')} fill="#0d9488" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card p-5">
          <h3 className={`mb-4 font-bold text-brand-800 ${ta ? 'font-tamil' : ''}`}>
            {t('dashboard.charts.ageTitle')}
          </h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={ageData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis unit="%" tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey={t('dashboard.charts.pre')} fill="#94a3b8" radius={[4, 4, 0, 0]} />
              <Bar dataKey={t('dashboard.charts.post')} fill="#2347c7" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card p-5">
          <h3 className={`mb-4 font-bold text-brand-800 ${ta ? 'font-tamil' : ''}`}>
            {t('dashboard.charts.riskTitle')}
          </h3>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={riskData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={95} paddingAngle={3}>
                {riskData.map((entry) => (
                  <Cell key={entry.key} fill={RISK_COLORS[entry.key] ?? '#94a3b8'} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card p-5">
        <h3 className={`mb-4 font-bold text-brand-800 ${ta ? 'font-tamil' : ''}`}>
          {t('dashboard.charts.scamTypesTitle')}
        </h3>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={data.top_scam_categories} layout="vertical" margin={{ left: 40 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis type="number" tick={{ fontSize: 11 }} />
            <YAxis dataKey="name" type="category" width={110} tick={{ fontSize: 11 }} />
            <Tooltip />
            <Bar dataKey="count" fill="#b45309" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="card p-5">
        <h3 className={`mb-4 font-bold text-brand-800 ${ta ? 'font-tamil' : ''}`}>
          {t('dashboard.charts.timelineTitle')}
        </h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={data.timeline}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="date" tick={{ fontSize: 10 }} minTickGap={30} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="analyses" stroke="#2347c7" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="participants" stroke="#0d9488" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
