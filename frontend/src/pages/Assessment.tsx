import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ClipboardList, Play, CheckCircle2, XCircle, Award, TrendingUp, Info, Download, GraduationCap,
} from 'lucide-react'
import {
  certificateUrl, getImprovement, getParticipants, getQuestions, getWorkshops, submitAssessment,
} from '@/api/client'
import CampaignChecklist from '@/components/CampaignChecklist'
import { useApp } from '@/context/AppContext'
import { EmptyState, SectionTitle, Spinner } from '@/components/ui/Bits'
import type { AssessmentResult, QuizQuestion } from '@/types'

type Phase = 'setup' | 'quiz' | 'result' | 'campaign' | 'improvement'

export default function Assessment() {
  const { t } = useTranslation()
  const { language } = useApp()
  const queryClient = useQueryClient()

  const [workshopOverride, setWorkshopId] = useState<number | null>(null)
  const [participantId, setParticipantId] = useState<number | null>(null)
  const [type, setType] = useState<'pre' | 'post'>('pre')
  const [phase, setPhase] = useState<Phase>('setup')
  const [questions, setQuestions] = useState<QuizQuestion[]>([])
  const [current, setCurrent] = useState(0)
  const [answers, setAnswers] = useState<Record<number, number>>({})
  const [startedAt, setStartedAt] = useState(0)
  const [result, setResult] = useState<AssessmentResult | null>(null)

  const ta = language === 'ta'

  const { data: workshops } = useQuery({ queryKey: ['workshops'], queryFn: () => getWorkshops() })

  // Derived, not stored in an effect — see the note in Workshops.tsx.
  const workshopId = workshopOverride ?? workshops?.[0]?.id ?? null

  const { data: participants } = useQuery({
    queryKey: ['participants', workshopId],
    queryFn: () => getParticipants(workshopId!),
    enabled: !!workshopId,
  })

  const loadQuestions = useMutation({
    mutationFn: () =>
      getQuestions({
        workshop_id: workshopId!, participant_id: participantId!,
        type, language, count: 10,
      }),
    onSuccess: (data) => {
      setQuestions(data)
      setAnswers({})
      setCurrent(0)
      setStartedAt(Date.now())
      setPhase('quiz')
    },
  })

  const submit = useMutation({
    mutationFn: () =>
      submitAssessment({
        participant_id: participantId!, workshop_id: workshopId!, type,
        answers: questions.map((q) => ({
          question_id: q.id,
          selected_index: answers[q.id] ?? 0,
        })),
        duration_seconds: Math.round((Date.now() - startedAt) / 1000),
        language,
      }),
    onSuccess: (data) => {
      setResult(data)
      setPhase('result')
      queryClient.invalidateQueries({ queryKey: ['improvement', participantId] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })

  const { data: improvement } = useQuery({
    queryKey: ['improvement', participantId],
    queryFn: () => getImprovement(participantId!),
    enabled: !!participantId && phase === 'improvement',
  })

  const answeredCount = useMemo(() => Object.keys(answers).length, [answers])

  // ------------------------------------------------------------------ setup
  if (phase === 'setup') {
    return (
      <div className="space-y-6">
        <SectionTitle title={t('assessment.title')} subtitle={t('assessment.subtitle')} />

        <div className="card space-y-5 p-6">
          <div>
            <label htmlFor="workshop" className="mb-1.5 block text-sm font-semibold text-slate-700">
              {t('assessment.selectWorkshop')}
            </label>
            <select
              id="workshop"
              className="input"
              value={workshopId ?? ''}
              onChange={(e) => {
                setWorkshopId(Number(e.target.value))
                // A participant belongs to exactly one workshop, so the old choice is stale.
                setParticipantId(null)
              }}
            >
              {(workshops ?? []).map((w) => (
                <option key={w.id} value={w.id}>
                  {ta ? w.title_ta : w.title_en} — {w.venue} ({w.conducted_on})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="participant" className="mb-1.5 block text-sm font-semibold text-slate-700">
              {t('assessment.selectParticipant')}
            </label>
            {participants?.length === 0 ? (
              <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-900">
                {t('assessment.noParticipants')}
              </p>
            ) : (
              <select
                id="participant"
                className="input"
                value={participantId ?? ''}
                onChange={(e) => setParticipantId(Number(e.target.value))}
              >
                <option value="">—</option>
                {(participants ?? []).map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} · {t(`workshops.ages.${p.age_group}`)}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="flex flex-wrap gap-3">
            {(['pre', 'post'] as const).map((k) => (
              <button
                key={k}
                onClick={() => setType(k)}
                aria-pressed={type === k}
                className={`chip min-h-[42px] border px-4 ${
                  type === k
                    ? 'border-brand-600 bg-brand-50 text-brand-800'
                    : 'border-slate-300 bg-white text-slate-600'
                }`}
              >
                {t(`assessment.${k}test`)}
              </button>
            ))}
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => loadQuestions.mutate()}
              disabled={!participantId || loadQuestions.isPending}
              className="btn-primary"
            >
              <Play size={18} aria-hidden />
              {t(type === 'pre' ? 'assessment.startPre' : 'assessment.startPost')}
            </button>

            <button
              onClick={() => setPhase('improvement')}
              disabled={!participantId}
              className="btn-ghost"
            >
              <TrendingUp size={16} aria-hidden /> {t('assessment.improvementTitle')}
            </button>
          </div>

          <p className="rounded-xl bg-accent-50 px-4 py-3 text-sm text-accent-900">
            {t('assessment.notExam')}
          </p>
        </div>
      </div>
    )
  }

  // ------------------------------------------------------------------- quiz
  if (phase === 'quiz') {
    if (loadQuestions.isPending || !questions.length) return <Spinner />
    const q = questions[current]
    const selected = answers[q.id]

    return (
      <div className="mx-auto max-w-2xl space-y-5">
        <div className="flex items-center justify-between text-sm">
          <span className="chip bg-brand-50 text-brand-800">
            {t('assessment.question', { current: current + 1, total: questions.length })}
          </span>
          <span className="chip bg-slate-100 text-slate-600">{q.category}</span>
        </div>

        <div className="h-2 overflow-hidden rounded-full bg-slate-200">
          <div
            className="h-full rounded-full bg-accent-600 transition-all"
            style={{ width: `${((current + 1) / questions.length) * 100}%` }}
          />
        </div>

        <div className="card p-6">
          <h2 className={`text-lg font-bold leading-relaxed text-slate-900 ${ta ? 'font-tamil' : ''}`}>
            {q.question}
          </h2>

          <div className="mt-5 space-y-3">
            {q.options.map((opt) => (
              <button
                key={opt.index}
                onClick={() => setAnswers((prev) => ({ ...prev, [q.id]: opt.index }))}
                className={`flex w-full min-h-[56px] items-center gap-3 rounded-xl border-2 p-4 text-left transition-colors ${
                  selected === opt.index
                    ? 'border-brand-600 bg-brand-50'
                    : 'border-slate-200 bg-white hover:border-brand-300'
                }`}
              >
                <span
                  className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 text-xs font-bold ${
                    selected === opt.index
                      ? 'border-brand-600 bg-brand-600 text-white'
                      : 'border-slate-300 text-slate-500'
                  }`}
                >
                  {String.fromCharCode(65 + opt.index)}
                </span>
                <span className={`text-slate-800 ${ta ? 'font-tamil' : ''}`}>{opt.text}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-between gap-3">
          <button
            onClick={() => setCurrent((c) => Math.max(0, c - 1))}
            disabled={current === 0}
            className="btn-ghost"
          >
            {t('common.back')}
          </button>

          {current + 1 < questions.length ? (
            <button
              onClick={() => setCurrent((c) => c + 1)}
              disabled={selected === undefined}
              className="btn-primary"
            >
              {t('common.next')}
            </button>
          ) : (
            <button
              onClick={() => submit.mutate()}
              disabled={answeredCount < questions.length || submit.isPending}
              className="btn-accent"
            >
              <CheckCircle2 size={18} aria-hidden /> {t('assessment.finish')}
            </button>
          )}
        </div>

        <p className="text-center text-xs text-slate-500">
          {answeredCount} / {questions.length}
        </p>
      </div>
    )
  }

  // ----------------------------------------------------------------- result
  if (phase === 'result' && result) {
    return (
      <div className="mx-auto max-w-2xl space-y-5">
        <div className="card p-8 text-center">
          <ClipboardList size={36} className="mx-auto text-brand-600" aria-hidden />
          <h2 className="mt-3 text-xl font-bold text-brand-800">{t('assessment.resultTitle')}</h2>
          <p className="mt-3 text-5xl font-bold text-accent-700">{result.percentage}%</p>
          <p className="mt-1 text-slate-600">
            {t('assessment.correctAnswers', { score: result.score, max: result.max_score })}
          </p>

          {result.weak_categories.length > 0 && (
            <div className="mt-5">
              <p className="mb-2 text-sm font-semibold text-slate-700">{t('assessment.weakTitle')}</p>
              <div className="flex flex-wrap justify-center gap-2">
                {result.weak_categories.map((c) => (
                  <span key={c} className="chip bg-amber-100 text-amber-900">{c}</span>
                ))}
              </div>
            </div>
          )}

          <div className="mt-6 flex flex-wrap justify-center gap-3">
            {/* After a PRE-test the next step is the intervention, not the score comparison —
                there is nothing to compare yet. Offering "improvement" here was the wrong
                affordance and skipped the part that does the actual teaching. */}
            {type === 'pre' ? (
              <button onClick={() => setPhase('campaign')} className="btn-primary">
                <GraduationCap size={16} aria-hidden /> {t('assessment.startCampaign')}
              </button>
            ) : (
              <button onClick={() => setPhase('improvement')} className="btn-primary">
                <TrendingUp size={16} aria-hidden /> {t('assessment.improvementTitle')}
              </button>
            )}
            <button onClick={() => setPhase('setup')} className="btn-ghost">
              {t('common.back')}
            </button>
          </div>
        </div>

        <div className="card p-5">
          <h3 className="mb-4 font-bold text-brand-800">{t('assessment.reviewTitle')}</h3>
          <ul className="space-y-4">
            {result.review.map((r) => (
              <li key={r.question_id} className="rounded-xl border border-slate-200 p-4">
                <div className="flex gap-3">
                  {r.is_correct ? (
                    <CheckCircle2 size={18} className="mt-0.5 shrink-0 text-green-700" aria-hidden />
                  ) : (
                    <XCircle size={18} className="mt-0.5 shrink-0 text-red-700" aria-hidden />
                  )}
                  <div className="flex-1">
                    <p className={`font-medium text-slate-800 ${ta ? 'font-tamil' : ''}`}>{r.question}</p>

                    {!r.is_correct && (
                      <p className={`mt-2 text-sm text-red-700 ${ta ? 'font-tamil' : ''}`}>
                        {t('assessment.yourAnswer')}: {r.your_answer}
                      </p>
                    )}
                    <p className={`mt-1 text-sm text-green-800 ${ta ? 'font-tamil' : ''}`}>
                      {t('assessment.correctAnswer')}: {r.correct_answer}
                    </p>
                    <p className={`mt-2 rounded-lg bg-slate-50 p-3 text-sm leading-relaxed text-slate-600 ${ta ? 'font-tamil' : ''}`}>
                      {r.explanation}
                    </p>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    )
  }

  // --------------------------------------------------------------- campaign
  // The intervention between the two tests. Without it the app would measure a change it
  // never helped cause, and the facilitator would have no in-app guide for what to teach.
  if (phase === 'campaign') {
    return (
      <div className="mx-auto max-w-2xl">
        <CampaignChecklist
          weakCategories={result?.weak_categories ?? []}
          onStartPostTest={() => {
            setType('post')
            loadQuestions.mutate()
          }}
        />
      </div>
    )
  }

  // ------------------------------------------------------------ improvement
  if (phase === 'improvement') {
    if (!improvement) return <Spinner />

    const undefinedPct = improvement.improvement_percentage === null

    return (
      <div className="mx-auto max-w-2xl space-y-5">
        <div className="card p-6 text-center">
          <Award size={36} className="mx-auto text-accent-600" aria-hidden />
          <h2 className="mt-3 text-xl font-bold text-brand-800">{t('assessment.improvementTitle')}</h2>
          <p className="mt-1 text-slate-600">{improvement.participant_name}</p>

          <div className="mt-6 grid grid-cols-3 gap-3">
            <div className="rounded-2xl bg-slate-50 p-4">
              <p className="text-2xl font-bold text-slate-700">
                {improvement.pre_percentage ?? '—'}
                {improvement.pre_percentage !== null && '%'}
              </p>
              <p className="mt-1 text-xs text-slate-500">{t('assessment.preScore')}</p>
            </div>
            <div className="rounded-2xl bg-accent-50 p-4">
              <p className="text-2xl font-bold text-accent-700">
                {improvement.post_percentage ?? '—'}
                {improvement.post_percentage !== null && '%'}
              </p>
              <p className="mt-1 text-xs text-slate-500">{t('assessment.postScore')}</p>
            </div>
            <div className="rounded-2xl bg-brand-50 p-4">
              {undefinedPct ? (
                <>
                  <p className="text-2xl font-bold text-brand-700">
                    +{improvement.absolute_gain ?? 0}
                  </p>
                  <p className="mt-1 text-xs text-slate-500">{t('assessment.absoluteGain')}</p>
                </>
              ) : (
                <>
                  <p className="text-2xl font-bold text-brand-700">
                    {improvement.improvement_percentage! > 0 ? '+' : ''}
                    {improvement.improvement_percentage}%
                  </p>
                  <p className="mt-1 text-xs text-slate-500">{t('assessment.improvement')}</p>
                </>
              )}
            </div>
          </div>

          <p className="mt-4 chip mx-auto bg-slate-100 text-slate-700">
            {t(`assessment.bands.${improvement.band}`, { defaultValue: improvement.band })}
          </p>

          {/*
            When the pre-test score is 0 the percentage formula divides by zero.
            Rather than hiding those participants, we explain it and show the
            alternative metrics — this is the honest reading of the data.
          */}
          {undefinedPct && (
            <div className="mt-5 flex gap-3 rounded-xl bg-amber-50 p-4 text-left">
              <Info size={18} className="mt-0.5 shrink-0 text-amber-700" aria-hidden />
              <div>
                <p className={`text-sm leading-relaxed text-amber-900 ${ta ? 'font-tamil' : ''}`}>
                  {t('assessment.undefinedNote')}
                </p>
                {improvement.normalized_gain !== null && (
                  <p className="mt-2 text-sm font-semibold text-amber-900">
                    {t('assessment.normalizedGain')}: {improvement.normalized_gain}
                  </p>
                )}
              </div>
            </div>
          )}

          <div className="mt-6 flex flex-wrap justify-center gap-3">
            {improvement.post_score !== null && (
              <a
                href={certificateUrl(improvement.participant_id)}
                className="btn-accent"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Download size={16} aria-hidden /> {t('assessment.certificate')}
              </a>
            )}
            <button onClick={() => setPhase('setup')} className="btn-ghost">
              {t('common.back')}
            </button>
          </div>
        </div>
      </div>
    )
  }

  return <EmptyState />
}
