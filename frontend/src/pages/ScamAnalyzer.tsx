import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useForm, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import {
  Search, Sparkles, ShieldCheck, ChevronDown, EyeOff, BookOpen, Languages,
} from 'lucide-react'
import { analyzeScam, getScamExamples } from '@/api/client'
import { useApp } from '@/context/AppContext'
import RiskMeter from '@/components/RiskMeter'
import { RISK_STYLES } from '@/components/riskStyles'
import { Disclaimer, ErrorState, FieldError, SectionTitle } from '@/components/ui/Bits'
import { scamTextSchema, type ScamTextForm } from '@/forms/validation'
import type { Channel } from '@/types'

const CHANNELS: Channel[] = ['sms', 'whatsapp', 'email', 'call_transcript']

export default function ScamAnalyzer() {
  const { t } = useTranslation()
  const { pick, language } = useApp()
  const [showSignals, setShowSignals] = useState(true)
  const [showExamples, setShowExamples] = useState(false)

  const { data: examples } = useQuery({
    queryKey: ['scam-examples', language],
    queryFn: () => getScamExamples({ language }),
    enabled: showExamples,
  })

  const {
    control,
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<ScamTextForm>({
    resolver: zodResolver(scamTextSchema),
    defaultValues: { text: '', channel: 'sms' },
  })
  // useWatch rather than watch(): a subscription a hook can reason about, which keeps this
  // file compatible with the React compiler.
  const channel = useWatch({ control, name: 'channel' })

  const mutation = useMutation({
    mutationFn: (values: ScamTextForm) => analyzeScam(values.text, values.channel, 'auto'),
  })

  const result = mutation.data
  const style = result ? RISK_STYLES[result.risk_label] : null

  return (
    <div className="space-y-6">
      <SectionTitle title={t('analyzer.title')} subtitle={t('analyzer.subtitle')} />

      {/* Input. noValidate: zod supplies the messages, not the browser. */}
      <form
        onSubmit={handleSubmit((values) => mutation.mutate(values))}
        noValidate
        className="card p-5"
      >
        <label htmlFor="scam-text" className="mb-2 block text-sm font-semibold text-slate-700">
          {t('analyzer.inputLabel')}
        </label>
        <textarea
          id="scam-text"
          rows={6}
          maxLength={5000}
          placeholder={t('analyzer.placeholder')}
          className="input resize-y font-normal"
          aria-invalid={errors.text ? true : undefined}
          aria-describedby={errors.text ? 'scam-text-error' : undefined}
          {...register('text')}
        />
        <FieldError id="scam-text-error" message={errors.text?.message} />

        <fieldset className="mt-4">
          <legend className="mb-2 text-sm font-semibold text-slate-700">{t('analyzer.channel')}</legend>
          <div className="flex flex-wrap gap-2">
            {CHANNELS.map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => setValue('channel', c, { shouldValidate: true })}
                aria-pressed={channel === c}
                className={`chip min-h-[40px] border px-4 ${
                  channel === c
                    ? 'border-brand-600 bg-brand-50 text-brand-800'
                    : 'border-slate-300 bg-white text-slate-600 hover:bg-slate-50'
                }`}
              >
                {t(`analyzer.channels.${c}`)}
              </button>
            ))}
          </div>
        </fieldset>

        <div className="mt-5 flex flex-wrap items-center gap-3">
          <button type="submit" disabled={mutation.isPending} className="btn-primary">
            <Search size={18} aria-hidden />
            {mutation.isPending ? t('analyzer.analyzing') : t('analyzer.analyze')}
          </button>

          <button type="button" onClick={() => setShowExamples((v) => !v)} className="btn-ghost">
            <Sparkles size={16} aria-hidden /> {t('analyzer.tryExample')}
          </button>
        </div>

        <p className="mt-4 flex items-start gap-2 rounded-xl bg-accent-50 px-4 py-3 text-xs leading-relaxed text-accent-900">
          <EyeOff size={15} className="mt-0.5 shrink-0" aria-hidden />
          {t('analyzer.privacyNote')}
        </p>

        {showExamples && (
          <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
            <p className="mb-2 text-sm font-semibold text-slate-700">{t('analyzer.examplesTitle')}</p>
            <div className="grid max-h-64 gap-2 overflow-y-auto">
              {(examples ?? []).slice(0, 14).map((ex) => (
                <button
                  key={ex.id}
                  type="button"
                  onClick={() => {
                    setValue('text', ex.text, { shouldValidate: true, shouldDirty: true })
                    setShowExamples(false)
                  }}
                  className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-left text-xs text-slate-700 hover:border-brand-400"
                >
                  <span className="mr-2 font-semibold uppercase text-brand-600">{ex.category}</span>
                  <span className={ex.language === 'ta' ? 'font-tamil' : ''}>{ex.text.slice(0, 110)}…</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </form>

      {mutation.isError && mutation.variables && (
        <ErrorState onRetry={() => mutation.mutate(mutation.variables!)} />
      )}

      {/* Result */}
      {result && style && (
        <div className="animate-fade-in space-y-5">
          <div className={`card border-2 p-6 ${style.border} ${style.bg}`}>
            <div className="flex flex-col items-center gap-6 md:flex-row md:items-start">
              <RiskMeter score={result.risk_score} label={result.risk_label} />

              <div className="flex-1">
                <h2 className="text-lg font-bold text-slate-900">{t('analyzer.resultTitle')}</h2>
                <p className={`mt-2 leading-relaxed text-slate-800 ${language === 'ta' ? 'font-tamil' : ''}`}>
                  {pick(result.explanation.en, result.explanation.ta)}
                </p>

                <div className="mt-4 flex flex-wrap gap-2 text-xs">
                  <span className="chip bg-white/70 text-slate-700">
                    {t('common.category')}: <strong>{result.primary_category}</strong>
                  </span>
                  <span className="chip bg-white/70 text-slate-700">
                    <Languages size={12} aria-hidden /> {t('analyzer.detectedLanguage')}:{' '}
                    <strong>{result.language_detected.toUpperCase()}</strong>
                  </span>
                  {result.pii_found.length > 0 && (
                    <span className="chip bg-accent-100 text-accent-900">
                      <EyeOff size={12} aria-hidden /> {t('analyzer.piiRemoved')}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* What to do */}
          <div className="card p-5">
            <h3 className="mb-3 flex items-center gap-2 font-bold text-brand-800">
              <ShieldCheck size={18} aria-hidden /> {t('analyzer.whatToDo')}
            </h3>
            <ul className="space-y-2">
              {pick(result.safe_actions.en.join('|'), result.safe_actions.ta.join('|'))
                .split('|')
                .filter(Boolean)
                .map((action, i) => (
                  <li key={i} className="flex gap-3 text-sm text-slate-700">
                    <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-accent-100 text-[11px] font-bold text-accent-800">
                      {i + 1}
                    </span>
                    <span className={language === 'ta' ? 'font-tamil' : ''}>{action}</span>
                  </li>
                ))}
            </ul>
          </div>

          {/* Why */}
          {result.signals.length > 0 && (
            <div className="card overflow-hidden">
              <button
                onClick={() => setShowSignals((v) => !v)}
                className="flex w-full items-center justify-between px-5 py-4 text-left font-bold text-brand-800 hover:bg-slate-50"
                aria-expanded={showSignals}
              >
                <span>{t('analyzer.whyTitle')}</span>
                <ChevronDown
                  size={18}
                  className={`transition-transform ${showSignals ? 'rotate-180' : ''}`}
                  aria-hidden
                />
              </button>

              {showSignals && (
                <ul className="divide-y divide-slate-100 border-t border-slate-100">
                  {result.signals.map((s) => (
                    <li key={s.rule_id} className="px-5 py-4">
                      <div className="flex items-start gap-3">
                        <span
                          className={`chip shrink-0 ${
                            s.weight < 0 ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-900'
                          }`}
                        >
                          {s.weight < 0 ? '−' : '+'}
                          {Math.abs(Math.round(s.weight * 100))}
                        </span>
                        <div>
                          <p className={`text-sm text-slate-700 ${language === 'ta' ? 'font-tamil' : ''}`}>
                            {pick(s.why_en, s.why_ta)}
                          </p>
                          {s.matched_snippet && (
                            <p className="mt-1.5 rounded bg-slate-100 px-2 py-1 font-mono text-xs text-slate-600">
                              “{s.matched_snippet}”
                            </p>
                          )}
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {/* Terms + related */}
          <div className="grid gap-5 md:grid-cols-2">
            {result.top_terms.length > 0 && (
              <div className="card p-5">
                <h3 className="mb-3 text-sm font-bold text-brand-800">{t('analyzer.termsTitle')}</h3>
                <div className="flex flex-wrap gap-2">
                  {result.top_terms.map((term) => (
                    <span key={term.term} className="chip bg-brand-50 text-brand-800">
                      {term.term}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {result.related_kb_slugs.length > 0 && (
              <div className="card p-5">
                <h3 className="mb-3 text-sm font-bold text-brand-800">{t('analyzer.relatedTitle')}</h3>
                {result.related_kb_slugs.map((slug) => (
                  <Link
                    key={slug}
                    to={`/learn/${slug}`}
                    className="inline-flex items-center gap-2 text-sm font-semibold text-accent-700 hover:underline"
                  >
                    <BookOpen size={15} aria-hidden /> {slug.replace(/-/g, ' ')}
                  </Link>
                ))}
              </div>
            )}
          </div>

          <Disclaimer text={pick(result.disclaimer.en, result.disclaimer.ta)} />
        </div>
      )}
    </div>
  )
}
