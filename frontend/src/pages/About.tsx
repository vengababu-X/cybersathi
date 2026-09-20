import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import {
  ShieldCheck, EyeOff, AlertTriangle, Cpu, WifiOff, KeyRound, Phone, ExternalLink,
} from 'lucide-react'
import { getHelplines, getModelMetrics, getStatus } from '@/api/client'
import { useApp } from '@/context/AppContext'
import { SectionTitle } from '@/components/ui/Bits'

const TECH = [
  'FastAPI', 'SQLite', 'scikit-learn', 'React', 'TypeScript', 'Tailwind CSS', 'Recharts', 'i18next',
]

/**
 * Declared at module scope, not inside the page: a component created during render is a new
 * component type on every pass, so React unmounts and remounts it instead of updating it.
 */
function Section({
  Icon, title, body, tamil,
}: {
  Icon: typeof ShieldCheck; title: string; body: string; tamil: boolean
}) {
  return (
    <div className="card p-5">
      <h2 className="flex items-center gap-2 font-bold text-brand-800">
        <Icon size={18} aria-hidden /> {title}
      </h2>
      <p className={`mt-2 leading-relaxed text-slate-700 ${tamil ? 'font-tamil' : ''}`}>{body}</p>
    </div>
  )
}

export default function About() {
  const { t } = useTranslation()
  const { pick, language } = useApp()
  const ta = language === 'ta'

  const { data: status } = useQuery({ queryKey: ['meta-status'], queryFn: getStatus })
  const { data: metrics } = useQuery({ queryKey: ['meta-metrics'], queryFn: getModelMetrics })
  const { data: helplines } = useQuery({ queryKey: ['helplines'], queryFn: getHelplines })

  const textMeta = metrics?.text_model ?? {}
  const urlMeta = metrics?.url_model ?? {}

  return (
    <div className="space-y-5">
      <SectionTitle title={t('about.title')} />

      <Section Icon={ShieldCheck} title={t('about.whatTitle')} body={t('about.whatBody')} tamil={ta} />
      <Section Icon={EyeOff} title={t('about.privacyTitle')} body={t('about.privacyBody')} tamil={ta} />
      <Section Icon={Cpu} title={t('about.modelTitle')} body={t('about.modelBody')} tamil={ta} />

      <div className="card border-l-4 border-amber-400 bg-amber-50 p-5">
        <h2 className="flex items-center gap-2 font-bold text-amber-900">
          <AlertTriangle size={18} aria-hidden /> {t('about.limitsTitle')}
        </h2>
        <p className={`mt-2 leading-relaxed text-amber-900 ${ta ? 'font-tamil' : ''}`}>
          {t('about.limitsBody')}
        </p>
      </div>

      {/* System status — proves the offline / no-key claim rather than asserting it */}
      {status && (
        <div className="card p-5">
          <h2 className="mb-3 font-bold text-brand-800">{t('about.metricsTitle')}</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="flex items-center gap-2 rounded-xl bg-accent-50 px-4 py-3 text-sm text-accent-900">
              <KeyRound size={16} aria-hidden />
              {t('about.noApiKeys')}{' '}
              <strong>{status.api_keys_required ? t('common.no') : t('about.confirmed')}</strong>
            </div>
            <div className="flex items-center gap-2 rounded-xl bg-accent-50 px-4 py-3 text-sm text-accent-900">
              <WifiOff size={16} aria-hidden />
              {t('about.offlineCapable')}{' '}
              <strong>{status.offline_capable ? t('common.yes') : t('common.no')}</strong>
            </div>
          </div>

          <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
            {[
              [t('about.labels.scamF1'), textMeta.binary_test_macro_f1],
              [t('about.labels.scamCorpus'), textMeta.rows ? t('about.countMessages', { count: textMeta.rows }) : null],
              [t('about.labels.urlAccuracy'), urlMeta.test_accuracy],
              [t('about.labels.urlCorpus'), urlMeta.rows ? t('about.countUrls', { count: urlMeta.rows }) : null],
            ].map(([label, value]) => (
              <div key={String(label)} className="flex justify-between rounded-lg bg-slate-50 px-3 py-2">
                <dt className="text-slate-600">{label}</dt>
                <dd className="font-mono font-semibold text-slate-900">{value ?? '—'}</dd>
              </div>
            ))}
          </dl>

          {/*
            The training corpus is synthetic, which makes the classes more separable than
            real traffic. Reporting the score without that caveat would overstate it.
          */}
          {metrics?.interpretation_note && (
            <p className="mt-4 rounded-xl bg-slate-100 px-4 py-3 text-xs leading-relaxed text-slate-600">
              {metrics.interpretation_note}
            </p>
          )}
        </div>
      )}

      {helplines && (
        <div className="card p-5">
          <h2 className="mb-3 flex items-center gap-2 font-bold text-brand-800">
            <Phone size={18} aria-hidden /> {t('helpline.title')}
          </h2>
          <ul className="space-y-2">
            {helplines.map((h) => (
              <li key={h.value} className="flex items-center justify-between gap-3 rounded-lg bg-slate-50 px-4 py-2.5 text-sm">
                <span className={`text-slate-700 ${ta ? 'font-tamil' : ''}`}>
                  {pick(h.name_en, h.name_ta)}
                </span>
                {h.type === 'phone' ? (
                  <a href={`tel:${h.value}`} className="font-bold text-risk-high hover:underline">
                    {h.value}
                  </a>
                ) : (
                  <a
                    href={`https://${h.value}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 font-semibold text-brand-700 hover:underline"
                  >
                    {h.value} <ExternalLink size={12} aria-hidden />
                  </a>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="card p-5">
        <h2 className="mb-3 font-bold text-brand-800">{t('about.techTitle')}</h2>
        <div className="flex flex-wrap gap-2">
          {TECH.map((tech) => (
            <span key={tech} className="chip bg-brand-50 text-brand-700">{tech}</span>
          ))}
        </div>
      </div>
    </div>
  )
}
