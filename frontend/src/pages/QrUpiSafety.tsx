import { useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import {
  Camera,
  QrCode, Upload, ShieldAlert, CheckCircle2, XCircle, Gamepad2, RotateCcw, Trophy,
} from 'lucide-react'
import { analyzeQr, getScenarios } from '@/api/client'
import { decodeQrFromFile } from '@/lib/decodeQr'
import { useApp } from '@/context/AppContext'
import { RISK_STYLES } from '@/components/riskStyles'
import { Disclaimer, FieldError, SectionTitle, Spinner } from '@/components/ui/Bits'
import { qrPayloadSchema, type QrPayloadForm } from '@/forms/validation'

/**
 * A UPI deep link is machine syntax, not prose — it reads the same in every language, so it
 * stays a constant rather than a translation. Same convention as the tech list on the About page.
 */
const PAYLOAD_EXAMPLE = 'upi://pay?pa=someone@bank&pn=Name&am=0'

function ScenarioGame() {
  const { t } = useTranslation()
  const { pick, language } = useApp()
  const { data: scenarios, isLoading } = useQuery({ queryKey: ['scenarios'], queryFn: getScenarios })

  const [index, setIndex] = useState(0)
  const [chosen, setChosen] = useState<number | null>(null)
  const [score, setScore] = useState(0)
  const [done, setDone] = useState(false)

  if (isLoading) return <Spinner />
  if (!scenarios?.length) return null

  const scenario = scenarios[index]
  const ta = language === 'ta'

  const choose = (i: number) => {
    if (chosen !== null) return
    setChosen(i)
    if (scenario.choices[i].is_safe) setScore((s) => s + 1)
  }

  const next = () => {
    if (index + 1 >= scenarios.length) { setDone(true); return }
    setIndex((i) => i + 1)
    setChosen(null)
  }

  const restart = () => { setIndex(0); setChosen(null); setScore(0); setDone(false) }

  if (done) {
    return (
      <div className="card p-8 text-center">
        <Trophy size={40} className="mx-auto text-accent-600" aria-hidden />
        <h3 className="mt-3 text-xl font-bold text-brand-800">{t('qr.gameComplete')}</h3>
        <p className="mt-2 text-3xl font-bold text-accent-700">
          {score} / {scenarios.length}
        </p>
        <p className="mt-1 text-sm text-slate-600">{t('qr.yourScore')}</p>
        <button onClick={restart} className="btn-primary mt-5">
          <RotateCcw size={16} aria-hidden /> {t('qr.restart')}
        </button>
      </div>
    )
  }

  return (
    <div className="card p-6">
      <div className="mb-4 flex items-center justify-between text-sm">
        <span className="chip bg-brand-50 text-brand-800">
          {t('qr.scenario')} {index + 1} / {scenarios.length}
        </span>
        <span className="font-semibold text-accent-700">
          {t('qr.yourScore')}: {score}
        </span>
      </div>

      <div className="mb-4 h-1.5 overflow-hidden rounded-full bg-slate-200">
        <div
          className="h-full rounded-full bg-accent-600 transition-all"
          style={{ width: `${((index + 1) / scenarios.length) * 100}%` }}
        />
      </div>

      <h3 className={`text-lg font-bold text-brand-800 ${ta ? 'font-tamil' : ''}`}>
        {pick(scenario.title_en, scenario.title_ta)}
      </h3>
      <p className={`mt-2 leading-relaxed text-slate-700 ${ta ? 'font-tamil' : ''}`}>
        {pick(scenario.situation_en, scenario.situation_ta)}
      </p>

      <div className="mt-5 space-y-3">
        {scenario.choices.map((c, i) => {
          const picked = chosen === i
          const reveal = chosen !== null
          return (
            <button
              key={i}
              onClick={() => choose(i)}
              disabled={reveal}
              className={`w-full rounded-xl border-2 p-4 text-left transition-colors ${
                reveal && c.is_safe
                  ? 'border-green-400 bg-green-50'
                  : picked && !c.is_safe
                    ? 'border-red-400 bg-red-50'
                    : 'border-slate-200 bg-white hover:border-brand-400 disabled:opacity-60'
              }`}
            >
              <div className="flex items-start gap-3">
                {reveal &&
                  (c.is_safe ? (
                    <CheckCircle2 size={18} className="mt-0.5 shrink-0 text-green-700" aria-hidden />
                  ) : picked ? (
                    <XCircle size={18} className="mt-0.5 shrink-0 text-red-700" aria-hidden />
                  ) : (
                    <span className="w-[18px]" />
                  ))}
                <span className={`text-sm text-slate-800 ${ta ? 'font-tamil' : ''}`}>
                  {pick(c.text_en, c.text_ta)}
                </span>
              </div>

              {reveal && (picked || c.is_safe) && (
                <p className={`mt-2 pl-7 text-xs leading-relaxed text-slate-600 ${ta ? 'font-tamil' : ''}`}>
                  {pick(c.feedback_en, c.feedback_ta)}
                </p>
              )}
            </button>
          )
        })}
      </div>

      {chosen !== null && (
        <div className="mt-5 animate-fade-in">
          <div className="rounded-xl bg-accent-50 p-4">
            <p className="text-xs font-bold uppercase tracking-wide text-accent-800">{t('qr.lesson')}</p>
            <p className={`mt-1 text-sm leading-relaxed text-accent-900 ${ta ? 'font-tamil' : ''}`}>
              {pick(scenario.lesson_en, scenario.lesson_ta)}
            </p>
          </div>
          <button onClick={next} className="btn-primary mt-4">
            {index + 1 >= scenarios.length ? t('assessment.finish') : t('qr.nextScenario')}
          </button>
        </div>
      )}
    </div>
  )
}

export default function QrUpiSafety() {
  const { t } = useTranslation()
  const { pick, language } = useApp()
  const [decodeError, setDecodeError] = useState(false)
  const [decoding, setDecoding] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)
  const cameraRef = useRef<HTMLInputElement>(null)

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<QrPayloadForm>({
    resolver: zodResolver(qrPayloadSchema),
    defaultValues: { payload: '' },
  })

  const mutation = useMutation({
    mutationFn: (values: QrPayloadForm) => analyzeQr(values.payload),
  })
  const result = mutation.data
  const ta = language === 'ta'

  /**
   * QR decoding happens entirely in the browser — the image is never uploaded.
   *
   * `decodeQrFromFile` runs a ladder of strategies (downscale, upscale, centre crop, contrast
   * stretch, inverted) because one naive pass fails on most real photographs: a 12MP phone
   * photo is too large, a printed code has too little contrast, and a code photographed on a
   * poster occupies too little of the frame.
   */
  const handleFile = async (file: File) => {
    setDecodeError(false)
    setDecoding(true)
    try {
      const { data } = await decodeQrFromFile(file)
      if (data) {
        // Feed the decoded text into the form so the user can check it before submitting.
        setValue('payload', data, { shouldValidate: true, shouldDirty: true })
      } else {
        setDecodeError(true)
      }
    } catch {
      setDecodeError(true)
    } finally {
      setDecoding(false)
      // Allow re-picking the same file after a failed attempt.
      if (fileRef.current) fileRef.current.value = ''
      if (cameraRef.current) cameraRef.current.value = ''
    }
  }

  return (
    <div className="space-y-6">
      <SectionTitle title={t('qr.title')} subtitle={t('qr.subtitle')} />

      {/* Golden rule — the single highest-impact message of the whole project */}
      <div className="rounded-3xl bg-gradient-to-br from-accent-700 to-accent-800 p-6 text-white sm:p-8">
        <p className="mb-2 text-xs font-bold uppercase tracking-wider text-white/80">
          {t('qr.goldenRule')}
        </p>
        <p className={`text-lg font-bold leading-relaxed sm:text-xl ${ta ? 'font-tamil' : ''}`}>
          {t('qr.goldenRuleBody')}
        </p>
      </div>

      {/* Checker */}
      <div className="card p-5">
        <h2 className="flex items-center gap-2 font-bold text-brand-800">
          <QrCode size={18} aria-hidden /> {t('qr.scanTitle')}
        </h2>
        <p className="mt-1 text-sm text-slate-600">{t('qr.scanBody')}</p>

        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f) }}
        />
        {/* `capture` opens the camera directly on a phone, which is how this is used in the
            field — a facilitator holding a participant's handset in front of a poster. */}
        <input
          ref={cameraRef}
          type="file"
          accept="image/*"
          capture="environment"
          className="hidden"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f) }}
        />

        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            disabled={decoding}
            className="btn-ghost"
          >
            <Upload size={16} aria-hidden /> {decoding ? t('qr.decoding') : t('qr.upload')}
          </button>
          <button
            type="button"
            onClick={() => cameraRef.current?.click()}
            disabled={decoding}
            className="btn-ghost"
          >
            <Camera size={16} aria-hidden /> {t('qr.takePhoto')}
          </button>
        </div>

        {decodeError && (
          <div className="mt-3 rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-900">
            <p className="font-semibold">{t('qr.decodeFailed')}</p>
            {/* A bare "try a clearer photo" leaves the user with nothing to change. These are
                the four things that actually fix it. */}
            <ul className="mt-2 list-disc space-y-1 pl-5 text-xs">
              <li>{t('qr.tipFill')}</li>
              <li>{t('qr.tipGlare')}</li>
              <li>{t('qr.tipFlat')}</li>
              <li>{t('qr.tipPaste')}</li>
            </ul>
          </div>
        )}

        <form onSubmit={handleSubmit((values) => mutation.mutate(values))} noValidate>
          <label htmlFor="qr-payload" className="mt-5 block text-sm font-semibold text-slate-700">
            {t('qr.pastePayload')}
          </label>
          <textarea
            id="qr-payload"
            rows={3}
            placeholder={PAYLOAD_EXAMPLE}
            className="input mt-2 resize-y font-mono text-xs"
            spellCheck={false}
            aria-invalid={errors.payload ? true : undefined}
            aria-describedby={errors.payload ? 'qr-payload-error' : undefined}
            {...register('payload')}
          />
          <FieldError id="qr-payload-error" message={errors.payload?.message} />

          <button type="submit" disabled={mutation.isPending} className="btn-primary mt-4">
            <QrCode size={18} aria-hidden /> {t('qr.analyze')}
          </button>
        </form>
      </div>

      {result && (
        <div className="animate-fade-in space-y-4">
          <div className={`card border-2 p-5 ${RISK_STYLES[result.risk_label].border} ${RISK_STYLES[result.risk_label].bg}`}>
            <div className="flex items-center gap-3">
              <span className={`chip px-4 py-2 text-sm ${RISK_STYLES[result.risk_label].bg} ${RISK_STYLES[result.risk_label].text}`}>
                <ShieldAlert size={16} aria-hidden />
                {t(`risk.${result.risk_label}`)} · {Math.round(result.risk_score)}
              </span>
            </div>
            <p className={`mt-3 leading-relaxed text-slate-800 ${ta ? 'font-tamil' : ''}`}>
              {pick(result.advice.en, result.advice.ta)}
            </p>
          </div>

          {Object.keys(result.parsed).length > 0 && (
            <div className="card p-5">
              <h3 className="mb-3 font-bold text-brand-800">{t('qr.parsedTitle')}</h3>
              <dl className="grid gap-2 text-sm sm:grid-cols-2">
                {Object.entries(result.parsed)
                  .filter(([, v]) => v)
                  .map(([k, v]) => (
                    <div key={k} className="rounded-lg bg-slate-50 px-3 py-2">
                      <dt className={`text-xs font-semibold text-slate-500 ${ta ? 'font-tamil' : ''}`}>
                        {t(`qr.fields.${k}`, { defaultValue: k })}
                      </dt>
                      <dd className="break-all font-mono text-slate-800">{v}</dd>
                    </div>
                  ))}
              </dl>
            </div>
          )}

          {result.signals.length > 0 && (
            <div className="card p-5">
              <h3 className="mb-3 font-bold text-brand-800">{t('analyzer.whyTitle')}</h3>
              <ul className="space-y-3">
                {result.signals.map((s) => (
                  <li key={s.rule_id} className="flex gap-3 text-sm text-slate-700">
                    <ShieldAlert size={16} className="mt-0.5 shrink-0 text-amber-600" aria-hidden />
                    <span className={ta ? 'font-tamil' : ''}>{pick(s.why_en, s.why_ta)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <Disclaimer text={pick(result.disclaimer.en, result.disclaimer.ta)} />
        </div>
      )}

      {/* Game */}
      <section>
        <div className="mb-4">
          <h2 className="flex items-center gap-2 text-xl font-bold text-brand-800">
            <Gamepad2 size={20} aria-hidden /> {t('qr.gameTitle')}
          </h2>
          <p className="mt-1 text-sm text-slate-600">{t('qr.gameBody')}</p>
        </div>
        <ScenarioGame />
      </section>
    </div>
  )
}
