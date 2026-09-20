import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ShieldCheck, UserPlus, Users, Cpu, Database, AlertTriangle, CheckCircle2, XCircle,
} from 'lucide-react'
import {
  createStaffUser, getArticles, getCategories, getModelMetrics, getStatus,
  getUsers, setUserActive, setUserRole,
} from '@/api/client'
import { useApp } from '@/context/AppContext'
import { ErrorState, SectionTitle, Spinner } from '@/components/ui/Bits'
import type { User } from '@/types'

const ROLES = ['admin', 'volunteer', 'participant'] as const

const ROLE_STYLE: Record<string, string> = {
  admin: 'bg-brand-100 text-brand-800',
  volunteer: 'bg-accent-100 text-accent-800',
  participant: 'bg-slate-100 text-slate-700',
}

function UserRow({ user, currentUserId }: { user: User; currentUserId: number | undefined }) {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)
  const isSelf = user.id === currentUserId

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['admin-users'] })
  const onError = (e: unknown) => {
    const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    setError(detail ?? t('common.error'))
  }

  const roleMutation = useMutation({
    mutationFn: (role: string) => setUserRole(user.id, role),
    onSuccess: () => { setError(null); invalidate() },
    onError,
  })
  const activeMutation = useMutation({
    mutationFn: (isActive: boolean) => setUserActive(user.id, isActive),
    onSuccess: () => { setError(null); invalidate() },
    onError,
  })

  return (
    <li className="flex flex-wrap items-center gap-3 border-b border-slate-100 py-3 text-sm last:border-0">
      <div className="min-w-[170px] flex-1">
        <p className="font-medium text-slate-800">
          {user.full_name}
          {isSelf && <span className="ml-2 text-xs text-slate-400">({t('admin.you')})</span>}
        </p>
        <p className="text-xs text-slate-500">{user.email}</p>
        {error && (
          <p role="alert" className="mt-1 text-xs text-risk-high">{error}</p>
        )}
      </div>

      <span className={`chip ${ROLE_STYLE[user.role] ?? ROLE_STYLE.participant}`}>
        {t(`admin.roles.${user.role}`, { defaultValue: user.role })}
      </span>

      <label className="sr-only" htmlFor={`role-${user.id}`}>{t('admin.changeRole')}</label>
      <select
        id={`role-${user.id}`}
        value={user.role}
        onChange={(e) => roleMutation.mutate(e.target.value)}
        disabled={roleMutation.isPending}
        className="input min-h-[38px] w-auto py-1 text-xs"
      >
        {ROLES.map((r) => (
          <option key={r} value={r}>{t(`admin.roles.${r}`)}</option>
        ))}
      </select>

      <button
        onClick={() => activeMutation.mutate(!user.is_active)}
        disabled={activeMutation.isPending}
        className={`chip min-h-[38px] px-3 ${
          user.is_active
            ? 'bg-green-100 text-green-800 hover:bg-green-200'
            : 'bg-red-100 text-red-800 hover:bg-red-200'
        }`}
      >
        {user.is_active
          ? <><CheckCircle2 size={13} aria-hidden /> {t('admin.active')}</>
          : <><XCircle size={13} aria-hidden /> {t('admin.disabled')}</>}
      </button>
    </li>
  )
}

export default function Admin() {
  const { t } = useTranslation()
  const { user, language } = useApp()
  const queryClient = useQueryClient()
  const ta = language === 'ta'

  const [form, setForm] = useState({
    full_name: '', email: '', password: '', role: 'volunteer' as (typeof ROLES)[number],
  })
  const [createError, setCreateError] = useState<string | null>(null)

  const { data: users, isLoading, isError, refetch } = useQuery({
    queryKey: ['admin-users'],
    queryFn: getUsers,
    enabled: user?.role === 'admin',
  })
  const { data: status } = useQuery({ queryKey: ['meta-status'], queryFn: getStatus })
  const { data: metrics } = useQuery({ queryKey: ['meta-metrics'], queryFn: getModelMetrics })
  const { data: articles } = useQuery({ queryKey: ['kb-articles-admin'], queryFn: () => getArticles() })
  const { data: categories } = useQuery({ queryKey: ['kb-categories'], queryFn: getCategories })

  const create = useMutation({
    mutationFn: () => createStaffUser(form),
    onSuccess: () => {
      setCreateError(null)
      setForm({ full_name: '', email: '', password: '', role: 'volunteer' })
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
    },
    onError: (e: unknown) => {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setCreateError(detail ?? t('common.error'))
    },
  })

  // Route is admin-only. Sending a non-admin to the sign-in page is clearer than a blank screen.
  if (!user) return <Navigate to="/login" replace />
  if (user.role !== 'admin') {
    return (
      <div className="card flex items-center gap-3 border-l-4 border-amber-400 bg-amber-50 p-5">
        <AlertTriangle size={20} className="text-amber-700" aria-hidden />
        <p className={`text-sm text-amber-900 ${ta ? 'font-tamil' : ''}`}>{t('admin.adminOnly')}</p>
      </div>
    )
  }

  const textMeta = (metrics?.text_model ?? {}) as Record<string, unknown>
  const urlMeta = (metrics?.url_model ?? {}) as Record<string, unknown>

  return (
    <div className="space-y-6">
      <SectionTitle title={t('admin.title')} subtitle={t('admin.subtitle')} />

      {/* Create staff account */}
      <section className="card p-5">
        <h2 className={`flex items-center gap-2 font-bold text-brand-800 ${ta ? 'font-tamil' : ''}`}>
          <UserPlus size={18} aria-hidden /> {t('admin.createUser')}
        </h2>
        <p className={`mt-1 text-sm text-slate-600 ${ta ? 'font-tamil' : ''}`}>
          {t('admin.createUserHint')}
        </p>

        <form
          onSubmit={(e) => { e.preventDefault(); create.mutate() }}
          className="mt-4 grid gap-3 sm:grid-cols-2"
        >
          <div>
            <label htmlFor="new-name" className="mb-1 block text-xs font-semibold text-slate-600">
              {t('admin.fullName')}
            </label>
            <input
              id="new-name" required minLength={2} className="input" value={form.full_name}
              onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
            />
          </div>
          <div>
            <label htmlFor="new-email" className="mb-1 block text-xs font-semibold text-slate-600">
              {t('auth.email')}
            </label>
            <input
              id="new-email" type="email" required className="input" value={form.email}
              onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
            />
          </div>
          <div>
            <label htmlFor="new-pass" className="mb-1 block text-xs font-semibold text-slate-600">
              {t('auth.password')}
            </label>
            <input
              id="new-pass" type="password" required minLength={6} className="input" value={form.password}
              onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
            />
          </div>
          <div>
            <label htmlFor="new-role" className="mb-1 block text-xs font-semibold text-slate-600">
              {t('admin.role')}
            </label>
            <select
              id="new-role" className="input" value={form.role}
              onChange={(e) => setForm((f) => ({ ...f, role: e.target.value as typeof f.role }))}
            >
              {ROLES.map((r) => <option key={r} value={r}>{t(`admin.roles.${r}`)}</option>)}
            </select>
          </div>

          {createError && (
            <p role="alert" className="sm:col-span-2 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">
              {createError}
            </p>
          )}

          <div className="sm:col-span-2">
            <button type="submit" disabled={create.isPending} className="btn-accent">
              {create.isPending ? t('common.loading') : t('admin.createUser')}
            </button>
          </div>
        </form>
      </section>

      {/* Users */}
      <section className="card p-5">
        <h2 className={`flex items-center gap-2 font-bold text-brand-800 ${ta ? 'font-tamil' : ''}`}>
          <Users size={18} aria-hidden /> {t('admin.users')}
          <span className="chip bg-slate-100 text-slate-600">{users?.length ?? 0}</span>
        </h2>

        {isLoading && <Spinner />}
        {isError && <ErrorState onRetry={refetch} />}

        {users && (
          <ul className="mt-3">
            {users.map((u) => (
              <UserRow key={u.id} user={u} currentUserId={user.id} />
            ))}
          </ul>
        )}
      </section>

      {/* Content overview */}
      <section className="card p-5">
        <h2 className={`flex items-center gap-2 font-bold text-brand-800 ${ta ? 'font-tamil' : ''}`}>
          <Database size={18} aria-hidden /> {t('admin.content')}
        </h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <div className="rounded-xl bg-slate-50 p-4 text-center">
            <p className="text-2xl font-bold text-brand-700">{articles?.length ?? '—'}</p>
            <p className={`mt-1 text-xs text-slate-600 ${ta ? 'font-tamil' : ''}`}>{t('admin.articles')}</p>
          </div>
          <div className="rounded-xl bg-slate-50 p-4 text-center">
            <p className="text-2xl font-bold text-brand-700">{categories?.length ?? '—'}</p>
            <p className={`mt-1 text-xs text-slate-600 ${ta ? 'font-tamil' : ''}`}>{t('admin.categories')}</p>
          </div>
          <div className="rounded-xl bg-slate-50 p-4 text-center">
            <p className="text-2xl font-bold text-brand-700">
              {articles ? articles.reduce((sum, a) => sum + a.views, 0) : '—'}
            </p>
            <p className={`mt-1 text-xs text-slate-600 ${ta ? 'font-tamil' : ''}`}>{t('admin.totalReads')}</p>
          </div>
        </div>

        {articles && (
          <ul className="mt-4 max-h-64 space-y-1 overflow-y-auto text-sm">
            {[...articles].sort((a, b) => b.views - a.views).map((a) => (
              <li key={a.slug} className="flex items-center gap-3 rounded-lg px-3 py-1.5 hover:bg-slate-50">
                <span className={`flex-1 truncate text-slate-700 ${ta ? 'font-tamil' : ''}`}>
                  {ta ? a.title_ta : a.title_en}
                </span>
                <span className="chip bg-slate-100 text-slate-600">{a.category}</span>
                <span className="w-14 text-right text-xs text-slate-400">{a.views}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Models */}
      <section className="card p-5">
        <h2 className={`flex items-center gap-2 font-bold text-brand-800 ${ta ? 'font-tamil' : ''}`}>
          <Cpu size={18} aria-hidden /> {t('admin.models')}
        </h2>

        {status && (
          <div className="mt-3 flex flex-wrap gap-2">
            <span className={`chip ${status.text_model_loaded ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
              <ShieldCheck size={13} aria-hidden /> {t('admin.textModel')}
            </span>
            <span className={`chip ${status.url_model_loaded ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
              <ShieldCheck size={13} aria-hidden /> {t('admin.urlModel')}
            </span>
            <span className="chip bg-slate-100 text-slate-600">
              {t('admin.llm')}: {status.llm_enabled ? t('common.yes') : t('common.no')}
            </span>
            <span className="chip bg-accent-100 text-accent-800">
              {t('admin.noKeys')}
            </span>
          </div>
        )}

        <dl className="mt-4 grid gap-2 text-sm sm:grid-cols-2">
          {([
            [t('admin.textMacroF1'), textMeta.binary_test_macro_f1],
            [t('admin.textCorpus'), textMeta.rows],
            [t('admin.urlAccuracy'), urlMeta.test_accuracy],
            [t('admin.urlCorpus'), urlMeta.rows],
            [t('admin.trainedAt'), String(textMeta.trained_at ?? '').slice(0, 10)],
            [t('admin.categoryF1'), textMeta.category_macro_f1],
          ] as [string, unknown][]).map(([label, value]) => (
            <div key={label} className="flex justify-between rounded-lg bg-slate-50 px-3 py-2">
              <dt className={`text-slate-600 ${ta ? 'font-tamil' : ''}`}>{label}</dt>
              <dd className="font-mono font-semibold text-slate-900">{String(value ?? '—')}</dd>
            </div>
          ))}
        </dl>

        {/* The scores come from a synthetic corpus, so they are an upper bound. Saying so here
            keeps the caveat next to the number rather than buried in a document. */}
        {metrics?.interpretation_note && (
          <p className="mt-4 rounded-xl bg-amber-50 px-4 py-3 text-xs leading-relaxed text-amber-900">
            {metrics.interpretation_note as string}
          </p>
        )}
      </section>
    </div>
  )
}
