import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Link2, ShieldOff, Search, Layers, AlertOctagon } from 'lucide-react'
import { bulkCheckUrls, checkUrl } from '@/api/client'
import { useApp } from '@/context/AppContext'
import RiskMeter from '@/components/RiskMeter'
import { RISK_STYLES } from '@/components/riskStyles'
import { Disclaimer, ErrorState, FieldError, SectionTitle } from '@/components/ui/Bits'
import {
  bulkUrlSchema, urlCheckSchema, type BulkUrlForm, type UrlCheckForm,
} from '@/forms/validation'
import type { UrlResult } from '@/types'

/** Features worth showing a non-technical user, with readable labels. */
const SHOWN_FEATURES: Record<string, { en: string; ta: string }> = {
  is_https: { en: 'Uses https', ta: 'https பயன்படுத்துகிறது' },
  has_ip_host: { en: 'Address is an IP number', ta: 'முகவரி IP எண்' },
  suspicious_tld: { en: 'Unusual domain ending', ta: 'அசாதாரண டொமைன் முடிவு' },
  shortener_flag: { en: 'Shortened link', ta: 'சுருக்கப்பட்ட இணைப்பு' },
  is_typosquat: { en: 'Imitates a known brand', ta: 'அறியப்பட்ட பெயரை நகலெடுக்கிறது' },
  has_at_symbol: { en: 'Contains @ trick', ta: '@ தந்திரம் உள்ளது' },
  has_punycode: { en: 'Look-alike characters', ta: 'ஒத்த எழுத்துக்கள்' },
  num_hyphens: { en: 'Number of hyphens', ta: 'ஹைஃபன்களின் எண்ணிக்கை' },
  num_subdomains: { en: 'Sub-parts before domain', ta: 'டொமைனுக்கு முன் பகுதிகள்' },
  url_length: { en: 'Address length', ta: 'முகவரியின் நீளம்' },
  sensitive_word_hit: { en: 'Words like login / verify / KYC', ta: 'login / verify / KYC சொற்கள்' },
}

function ResultCard({ result }: { result: UrlResult }) {
  const { t } = useTranslation()
  const { pick, language } = useApp()
  const style = RISK_STYLES[result.risk_label]

  return (
    <div className="animate-fade-in space-y-5">
      <div className={`card border-2 p-6 ${style.border} ${style.bg}`}>
        <div className="flex flex-col items-center gap-6 md:flex-row md:items-start">
          <RiskMeter score={result.risk_score} label={result.risk_label} />
          <div className="flex-1">
            <p className="break-all rounded-lg bg-white/70 px-3 py-2 font-mono text-xs text-slate-700">
              {result.url_defanged}
            </p>

            {result.lookalike_brand && (
              <p className="mt-3 flex items-center gap-2 rounded-lg bg-red-100 px-3 py-2 text-sm font-semibold text-red-900">
                <AlertOctagon size={16} aria-hidden />
                {t('url.lookalike', { brand: result.lookalike_brand })}
              </p>
            )}

            <h3 className="mt-4 text-sm font-bold text-slate-800">{t('url.adviceTitle')}</h3>
            <p className={`mt-1 leading-relaxed text-slate-800 ${language === 'ta' ? 'font-tamil' : ''}`}>
              {pick(result.advice.en, result.advice.ta)}
            </p>
          </div>
        </div>
      </div>

      {result.top_reasons.length > 0 && (
        <div className="card p-5">
          <h3 className="mb-3 font-bold text-brand-800">{t('url.reasonsTitle')}</h3>
          <ul className="space-y-3">
            {result.top_reasons.map((r, i) => (
              <li key={`${r.feature}-${i}`} className="flex gap-3 text-sm text-slate-700">
                <ShieldOff size={16} className="mt-0.5 shrink-0 text-amber-600" aria-hidden />
                <span className={language === 'ta' ? 'font-tamil' : ''}>{pick(r.why_en, r.why_ta)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="card p-5">
        <h3 className="mb-3 font-bold text-brand-800">{t('url.featuresTitle')}</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs uppercase text-slate-500">
                <th className="pb-2 pr-4 font-semibold">{t('url.feature')}</th>
                <th className="pb-2 font-semibold">{t('url.value')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {Object.entries(SHOWN_FEATURES).map(([key, label]) => (
                <tr key={key}>
                  <td className={`py-2 pr-4 text-slate-700 ${language === 'ta' ? 'font-tamil' : ''}`}>
                    {pick(label.en, label.ta)}
                  </td>
                  <td className="py-2 font-mono text-slate-900">
                    {result.features[key] === 1 && ['is_https', 'has_ip_host', 'suspicious_tld', 'shortener_flag', 'is_typosquat', 'has_at_symbol', 'has_punycode'].includes(key)
                      ? t('common.yes')
                      : result.features[key] === 0 && ['is_https', 'has_ip_host', 'suspicious_tld', 'shortener_flag', 'is_typosquat', 'has_at_symbol', 'has_punycode'].includes(key)
                        ? t('common.no')
                        : Math.round(result.features[key] ?? 0)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <Disclaimer text={pick(result.disclaimer.en, result.disclaimer.ta)} />
    </div>
  )
}

export default function UrlChecker() {
  const { t } = useTranslation()
  const { language } = useApp()
  const [mode, setMode] = useState<'single' | 'bulk'>('single')

  const singleForm = useForm<UrlCheckForm>({
    resolver: zodResolver(urlCheckSchema),
    defaultValues: { url: '' },
  })
  const bulkForm = useForm<BulkUrlForm>({
    resolver: zodResolver(bulkUrlSchema),
    defaultValues: { urls: '' },
  })

  const single = useMutation({ mutationFn: (values: UrlCheckForm) => checkUrl(values.url) })
  const bulk = useMutation({
    mutationFn: (values: BulkUrlForm) =>
      bulkCheckUrls(
        values.urls
          .split(/\r?\n/)
          .map((line) => line.trim())
          .filter(Boolean)
          // The schema already caps this at 20; the slice keeps the API contract explicit.
          .slice(0, 20),
      ),
  })

  return (
    <div className="space-y-6">
      <SectionTitle title={t('url.title')} subtitle={t('url.subtitle')} />

      <div className="card p-5">
        <div className="mb-4 flex gap-2" role="tablist">
          {(['single', 'bulk'] as const).map((m) => (
            <button
              key={m}
              role="tab"
              aria-selected={mode === m}
              onClick={() => setMode(m)}
              className={`chip min-h-[40px] border px-4 ${
                mode === m
                  ? 'border-brand-600 bg-brand-50 text-brand-800'
                  : 'border-slate-300 bg-white text-slate-600'
              }`}
            >
              {m === 'single' ? <Link2 size={14} aria-hidden /> : <Layers size={14} aria-hidden />}
              {m === 'single' ? t('url.check') : t('url.bulk')}
            </button>
          ))}
        </div>

        {/* noValidate: zod supplies the messages, so the browser must not pre-empt them. */}
        {mode === 'single' ? (
          <form onSubmit={singleForm.handleSubmit((values) => single.mutate(values))} noValidate>
            <label htmlFor="url-input" className="sr-only">{t('url.title')}</label>
            <input
              id="url-input"
              placeholder={t('url.placeholder')}
              className="input font-mono text-sm"
              autoComplete="off"
              spellCheck={false}
              aria-invalid={singleForm.formState.errors.url ? true : undefined}
              aria-describedby={singleForm.formState.errors.url ? 'url-error' : undefined}
              {...singleForm.register('url')}
            />
            <FieldError id="url-error" message={singleForm.formState.errors.url?.message} />
            <button type="submit" disabled={single.isPending} className="btn-primary mt-4">
              <Search size={18} aria-hidden />
              {single.isPending ? t('url.checking') : t('url.check')}
            </button>
          </form>
        ) : (
          <form onSubmit={bulkForm.handleSubmit((values) => bulk.mutate(values))} noValidate>
            <label htmlFor="bulk-input" className="sr-only">{t('url.bulk')}</label>
            <textarea
              id="bulk-input"
              rows={6}
              placeholder={t('url.bulkPlaceholder')}
              className="input resize-y font-mono text-sm"
              spellCheck={false}
              aria-invalid={bulkForm.formState.errors.urls ? true : undefined}
              aria-describedby={bulkForm.formState.errors.urls ? 'bulk-error' : undefined}
              {...bulkForm.register('urls')}
            />
            <FieldError id="bulk-error" message={bulkForm.formState.errors.urls?.message} />
            <button type="submit" disabled={bulk.isPending} className="btn-primary mt-4">
              <Layers size={18} aria-hidden />
              {bulk.isPending ? t('url.checking') : t('url.bulk')}
            </button>
          </form>
        )}

        <p className="mt-4 flex items-start gap-2 rounded-xl bg-accent-50 px-4 py-3 text-xs leading-relaxed text-accent-900">
          <ShieldOff size={15} className="mt-0.5 shrink-0" aria-hidden />
          {t('url.neverOpens')}
        </p>
      </div>

      {/* Retry replays the last submitted values, which TanStack Query keeps for us. */}
      {single.isError && single.variables && (
        <ErrorState onRetry={() => single.mutate(single.variables!)} />
      )}
      {bulk.isError && bulk.variables && (
        <ErrorState onRetry={() => bulk.mutate(bulk.variables!)} />
      )}

      {mode === 'single' && single.data && <ResultCard result={single.data} />}

      {mode === 'bulk' && bulk.data && (
        <div className="card overflow-hidden">
          <ul className="divide-y divide-slate-100">
            {bulk.data.map((r, i) => {
              const style = RISK_STYLES[r.risk_label]
              const { Icon } = style
              return (
                <li key={i} className="flex items-center gap-3 px-5 py-3">
                  <Icon size={18} className={style.text} aria-hidden />
                  <span className={`chip ${style.bg} ${style.text}`}>{Math.round(r.risk_score)}</span>
                  <span className="truncate font-mono text-xs text-slate-600">{r.url_defanged}</span>
                  <span className={`ml-auto shrink-0 text-xs font-semibold ${style.text} ${language === 'ta' ? 'font-tamil' : ''}`}>
                    {t(`risk.${r.risk_label}`)}
                  </span>
                </li>
              )
            })}
          </ul>
        </div>
      )}
    </div>
  )
}
