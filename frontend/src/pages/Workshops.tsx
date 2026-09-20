import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Plus, MapPin, CalendarDays, Users, ShieldCheck, Lock } from 'lucide-react'
import { addParticipants, createWorkshop, getParticipants, getWorkshops } from '@/api/client'
import FeedbackForm from '@/components/FeedbackForm'
import { useApp } from '@/context/AppContext'
import { EmptyState, FieldError, SectionTitle, Spinner } from '@/components/ui/Bits'
import {
  participantSchema, workshopSchema, type ParticipantForm, type WorkshopForm,
} from '@/forms/validation'

const AUDIENCES = ['school', 'college', 'senior', 'rural', 'women', 'mixed'] as const
const AGES = ['student', 'adult', 'senior'] as const
const GENDERS = ['male', 'female', 'other'] as const

export default function Workshops() {
  const { t } = useTranslation()
  const { user, language } = useApp()
  const queryClient = useQueryClient()
  const ta = language === 'ta'

  const [selectedOverride, setSelected] = useState<number | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [showParticipantForm, setShowParticipantForm] = useState(false)

  const workshopForm = useForm<WorkshopForm>({
    resolver: zodResolver(workshopSchema),
    defaultValues: {
      title_en: '', title_ta: '', venue: '', district: '',
      conducted_on: new Date().toISOString().slice(0, 10),
      audience_type: 'mixed',
      participants_expected: 20,
    },
  })

  const participantForm = useForm<ParticipantForm>({
    resolver: zodResolver(participantSchema),
    defaultValues: {
      name: '', age_group: 'adult', gender: 'female', language: 'ta',
      phone: '', consent_given: true,
    },
  })
  const participantErrors = participantForm.formState.errors
  const workshopErrors = workshopForm.formState.errors

  const { data: workshops, isLoading } = useQuery({ queryKey: ['workshops'], queryFn: () => getWorkshops() })

  // Derived rather than stored: defaulting to the first workshop inside an effect costs an
  // extra render and flashes an empty roster. The override holds a deliberate user choice.
  const selected = selectedOverride ?? workshops?.[0]?.id ?? null

  const { data: participants } = useQuery({
    queryKey: ['participants', selected],
    queryFn: () => getParticipants(selected!),
    enabled: !!selected,
  })

  const create = useMutation({
    mutationFn: (values: WorkshopForm) => createWorkshop(values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workshops'] })
      setShowForm(false)
      workshopForm.reset()
    },
  })

  const addPerson = useMutation({
    mutationFn: (values: ParticipantForm) =>
      // An empty phone must be omitted rather than sent as "", so the server never hashes one.
      addParticipants(selected!, [{ ...values, phone: values.phone || null }]),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['participants', selected] })
      participantForm.reset()
      setShowParticipantForm(false)
    },
  })

  const canManage = user?.role === 'admin' || user?.role === 'volunteer'

  if (isLoading) return <Spinner />

  return (
    <div className="space-y-6">
      <SectionTitle title={t('workshops.title')} subtitle={t('workshops.subtitle')} />

      {!canManage && (
        <div className="card flex items-center gap-3 border-l-4 border-amber-400 bg-amber-50 p-4">
          <Lock size={18} className="text-amber-700" aria-hidden />
          <p className="text-sm text-amber-900">{t('workshops.loginRequired')}</p>
        </div>
      )}

      {canManage && (
        <button onClick={() => setShowForm((v) => !v)} className="btn-primary">
          <Plus size={18} aria-hidden /> {t('workshops.create')}
        </button>
      )}

      {showForm && canManage && (
        <form
          onSubmit={workshopForm.handleSubmit((values) => create.mutate(values))}
          noValidate
          className="card grid gap-4 p-6 sm:grid-cols-2"
        >
          {([
            ['title_en', t('workshops.titleEn')],
            ['title_ta', t('workshops.titleTa')],
            ['venue', t('workshops.venue')],
            ['district', t('workshops.district')],
          ] as const).map(([key, label]) => (
            <div key={key}>
              <label htmlFor={key} className="mb-1.5 block text-sm font-semibold text-slate-700">{label}</label>
              <input
                id={key}
                className={`input ${key === 'title_ta' ? 'font-tamil' : ''}`}
                aria-invalid={workshopErrors[key] ? true : undefined}
                aria-describedby={workshopErrors[key] ? `${key}-error` : undefined}
                {...workshopForm.register(key)}
              />
              <FieldError id={`${key}-error`} message={workshopErrors[key]?.message} />
            </div>
          ))}

          <div>
            <label htmlFor="conducted_on" className="mb-1.5 block text-sm font-semibold text-slate-700">
              {t('workshops.date')}
            </label>
            <input
              id="conducted_on" type="date" className="input"
              aria-invalid={workshopErrors.conducted_on ? true : undefined}
              aria-describedby={workshopErrors.conducted_on ? 'conducted_on-error' : undefined}
              {...workshopForm.register('conducted_on')}
            />
            <FieldError id="conducted_on-error" message={workshopErrors.conducted_on?.message} />
          </div>

          <div>
            <label htmlFor="audience" className="mb-1.5 block text-sm font-semibold text-slate-700">
              {t('workshops.audience')}
            </label>
            <select id="audience" className="input" {...workshopForm.register('audience_type')}>
              {AUDIENCES.map((a) => (
                <option key={a} value={a}>{t(`workshops.audiences.${a}`)}</option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="expected" className="mb-1.5 block text-sm font-semibold text-slate-700">
              {t('workshops.expected')}
            </label>
            <input
              id="expected"
              type="number"
              min={1}
              max={500}
              className="input"
              aria-invalid={workshopErrors.participants_expected ? true : undefined}
              aria-describedby={workshopErrors.participants_expected ? 'expected-error' : undefined}
              {...workshopForm.register('participants_expected', { valueAsNumber: true })}
            />
            <FieldError
              id="expected-error"
              message={workshopErrors.participants_expected?.message}
            />
          </div>

          <div className="sm:col-span-2">
            <button type="submit" disabled={create.isPending} className="btn-accent">
              {t('workshops.save')}
            </button>
          </div>
        </form>
      )}

      {workshops?.length === 0 && <EmptyState />}

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="space-y-3 lg:col-span-1">
          {(workshops ?? []).map((w) => (
            <button
              key={w.id}
              onClick={() => setSelected(w.id)}
              className={`card w-full p-4 text-left transition-colors ${
                selected === w.id ? 'border-brand-500 bg-brand-50' : 'hover:bg-slate-50'
              }`}
            >
              <p className={`font-semibold text-brand-800 ${ta ? 'font-tamil' : ''}`}>
                {ta ? w.title_ta : w.title_en}
              </p>
              <p className="mt-1.5 flex items-center gap-1.5 text-xs text-slate-600">
                <MapPin size={12} aria-hidden /> {w.venue}
              </p>
              <p className="mt-1 flex items-center gap-1.5 text-xs text-slate-500">
                <CalendarDays size={12} aria-hidden /> {w.conducted_on} · {w.district}
              </p>
              <span className="chip mt-2 bg-slate-100 text-slate-600">
                {t(`workshops.audiences.${w.audience_type}`, { defaultValue: w.audience_type })}
              </span>
            </button>
          ))}
        </div>

        <div className="lg:col-span-2">
          <div className="card p-5">
            <div className="mb-4 flex items-center justify-between gap-3">
              <h3 className="flex items-center gap-2 font-bold text-brand-800">
                <Users size={18} aria-hidden /> {t('workshops.participants')}
                <span className="chip bg-slate-100 text-slate-600">{participants?.length ?? 0}</span>
              </h3>
              {canManage && selected && (
                <button onClick={() => setShowParticipantForm((v) => !v)} className="btn-ghost">
                  <Plus size={15} aria-hidden /> {t('workshops.addParticipant')}
                </button>
              )}
            </div>

            {showParticipantForm && canManage && (
              <form
                onSubmit={participantForm.handleSubmit((values) => addPerson.mutate(values))}
                noValidate
                className="mb-5 grid gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 sm:grid-cols-2"
              >
                <div className="sm:col-span-2">
                  <label htmlFor="pname" className="mb-1 block text-xs font-semibold text-slate-600">
                    {t('workshops.name')}
                  </label>
                  <input
                    id="pname"
                    className="input"
                    aria-invalid={participantErrors.name ? true : undefined}
                    aria-describedby={participantErrors.name ? 'pname-error' : undefined}
                    {...participantForm.register('name')}
                  />
                  <FieldError id="pname-error" message={participantErrors.name?.message} />
                </div>

                <div>
                  <label htmlFor="page" className="mb-1 block text-xs font-semibold text-slate-600">
                    {t('workshops.ageGroup')}
                  </label>
                  <select id="page" className="input" {...participantForm.register('age_group')}>
                    {AGES.map((a) => <option key={a} value={a}>{t(`workshops.ages.${a}`)}</option>)}
                  </select>
                </div>

                <div>
                  <label htmlFor="pgender" className="mb-1 block text-xs font-semibold text-slate-600">
                    {t('workshops.gender')}
                  </label>
                  <select id="pgender" className="input" {...participantForm.register('gender')}>
                    {GENDERS.map((g) => <option key={g} value={g}>{t(`workshops.genders.${g}`)}</option>)}
                  </select>
                </div>

                <div>
                  <label htmlFor="plang" className="mb-1 block text-xs font-semibold text-slate-600">
                    {t('workshops.language')}
                  </label>
                  <select id="plang" className="input" {...participantForm.register('language')}>
                    <option value="en">{t('workshops.languages.en')}</option>
                    <option value="ta">{t('workshops.languages.ta')}</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="pphone" className="mb-1 block text-xs font-semibold text-slate-600">
                    {t('workshops.phone')}
                  </label>
                  <input
                    id="pphone"
                    className="input"
                    inputMode="numeric"
                    aria-invalid={participantErrors.phone ? true : undefined}
                    aria-describedby={participantErrors.phone ? 'pphone-error' : undefined}
                    {...participantForm.register('phone')}
                  />
                  <FieldError id="pphone-error" message={participantErrors.phone?.message} />
                </div>

                <p className="sm:col-span-2 rounded-lg bg-accent-50 px-3 py-2 text-xs text-accent-900">
                  {t('workshops.phoneNote')}
                </p>

                <label className="flex items-center gap-2 text-sm text-slate-700 sm:col-span-2">
                  <input
                    type="checkbox"
                    className="h-4 w-4"
                    {...participantForm.register('consent_given')}
                  />
                  <ShieldCheck size={15} className="text-accent-700" aria-hidden />
                  {t('workshops.consent')}
                </label>

                <div className="sm:col-span-2">
                  <button type="submit" disabled={addPerson.isPending} className="btn-accent">
                    {t('workshops.save')}
                  </button>
                </div>
              </form>
            )}

            {participants?.length === 0 ? (
              <p className="py-6 text-center text-sm text-slate-500">
                {t('assessment.noParticipants')}
              </p>
            ) : (
              <ul className="divide-y divide-slate-100">
                {(participants ?? []).map((p) => (
                  <li key={p.id} className="flex items-center gap-3 py-2.5 text-sm">
                    <span className="font-medium text-slate-800">{p.name}</span>
                    <span className="chip bg-slate-100 text-slate-600">
                      {t(`workshops.ages.${p.age_group}`, { defaultValue: p.age_group })}
                    </span>
                    <span className="chip bg-slate-100 text-slate-600">{p.language.toUpperCase()}</span>
                    {p.consent_given && (
                      <ShieldCheck size={14} className="ml-auto text-accent-600" aria-hidden />
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Collected at the end of a session. Without this the dashboard's average rating
              could only ever come from seeded data, and the project report's beneficiary
              feedback section would have nothing behind it. */}
          {selected && (
            <div className="mt-4">
              <FeedbackForm workshopId={selected} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
