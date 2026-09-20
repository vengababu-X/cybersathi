import type { ReactNode } from 'react'
import { AlertCircle, Loader2, Inbox } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { errorText } from '@/forms/validation'

export function Spinner({ label }: { label?: string }) {
  const { t } = useTranslation()
  return (
    <div className="flex items-center justify-center gap-3 py-10 text-slate-500" role="status">
      <Loader2 className="animate-spin" size={20} aria-hidden />
      <span>{label ?? t('common.loading')}</span>
    </div>
  )
}

export function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`skeleton ${className}`} aria-hidden />
}

export function ErrorState({ onRetry, message }: { onRetry?: () => void; message?: string }) {
  const { t } = useTranslation()
  return (
    <div className="card flex flex-col items-center gap-3 p-8 text-center">
      <AlertCircle className="text-risk-high" size={28} aria-hidden />
      <p className="text-slate-700">{message ?? t('common.error')}</p>
      {onRetry && (
        <button className="btn-ghost" onClick={onRetry}>
          {t('common.retry')}
        </button>
      )}
    </div>
  )
}

export function EmptyState({ message, action }: { message?: string; action?: ReactNode }) {
  const { t } = useTranslation()
  return (
    <div className="card flex flex-col items-center gap-3 p-10 text-center">
      <Inbox className="text-slate-300" size={34} aria-hidden />
      <p className="text-slate-500">{message ?? t('common.empty')}</p>
      {action}
    </div>
  )
}

/**
 * Inline, per-field validation message.
 *
 * `message` is an i18next key (optionally with a `|number` suffix) produced by a zod schema,
 * which is what keeps validation bilingual without translating the schemas themselves.
 * role="alert" makes screen readers announce the failure as soon as it appears.
 */
export function FieldError({ id, message }: { id?: string; message?: string }) {
  const { t } = useTranslation()
  if (!message) return null
  return (
    <p id={id} role="alert" className="mt-1.5 text-xs font-semibold text-risk-high">
      {errorText(t, message)}
    </p>
  )
}

export function SectionTitle({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-6">
      <h1 className="text-2xl font-bold text-brand-800 sm:text-3xl">{title}</h1>
      {subtitle && <p className="mt-1.5 text-slate-600">{subtitle}</p>}
    </div>
  )
}

export function Disclaimer({ text }: { text: string }) {
  return (
    <p className="mt-4 rounded-xl bg-slate-100 px-4 py-3 text-xs leading-relaxed text-slate-600">
      {text}
    </p>
  )
}
