import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, MessageSquareHeart, Star } from 'lucide-react'
import { createFeedback } from '@/api/client'
import { useApp } from '@/context/AppContext'

interface Props {
  workshopId: number
  participantId?: number | null
  /** Rendered inline after an assessment, or as a standalone card on the workshops page. */
  compact?: boolean
}

/**
 * Collects the session rating that the impact dashboard reports.
 *
 * Without this the dashboard's "average rating" could only ever come from seeded data, and the
 * Community Service Project report has a beneficiary-feedback section with nothing to fill it.
 */
export default function FeedbackForm({ workshopId, participantId, compact = false }: Props) {
  const { t } = useTranslation()
  const { language } = useApp()
  const queryClient = useQueryClient()
  const ta = language === 'ta'

  const [rating, setRating] = useState(0)
  const [hovered, setHovered] = useState(0)
  const [comment, setComment] = useState('')

  const mutation = useMutation({
    mutationFn: () =>
      createFeedback({
        workshop_id: workshopId,
        participant_id: participantId ?? null,
        rating,
        comment: comment.trim() || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })

  if (mutation.isSuccess) {
    return (
      <div className="flex items-center gap-2 rounded-xl bg-accent-50 px-4 py-3 text-sm text-accent-900">
        <CheckCircle2 size={18} aria-hidden />
        <span className={ta ? 'font-tamil' : ''}>{t('feedback.thanks')}</span>
      </div>
    )
  }

  const shown = hovered || rating

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        if (rating > 0) mutation.mutate()
      }}
      className={compact ? '' : 'card p-5'}
    >
      <h3 className={`flex items-center gap-2 font-bold text-brand-800 ${ta ? 'font-tamil' : ''}`}>
        <MessageSquareHeart size={18} aria-hidden /> {t('feedback.title')}
      </h3>
      <p className={`mt-1 text-sm text-slate-600 ${ta ? 'font-tamil' : ''}`}>{t('feedback.subtitle')}</p>

      <fieldset className="mt-4">
        <legend className={`mb-2 text-sm font-semibold text-slate-700 ${ta ? 'font-tamil' : ''}`}>
          {t('feedback.rating')}
        </legend>
        <div className="flex gap-1.5" onMouseLeave={() => setHovered(0)}>
          {[1, 2, 3, 4, 5].map((n) => (
            <button
              key={n}
              type="button"
              onClick={() => setRating(n)}
              onMouseEnter={() => setHovered(n)}
              aria-label={t('feedback.starLabel', { n })}
              aria-pressed={rating === n}
              className="rounded-lg p-1.5 transition-transform hover:scale-110"
            >
              <Star
                size={30}
                className={n <= shown ? 'fill-amber-400 text-amber-500' : 'text-slate-300'}
                aria-hidden
              />
            </button>
          ))}
        </div>
      </fieldset>

      <label htmlFor="feedback-comment" className={`mt-4 block text-sm font-semibold text-slate-700 ${ta ? 'font-tamil' : ''}`}>
        {t('feedback.comment')}
      </label>
      <textarea
        id="feedback-comment"
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        rows={3}
        maxLength={500}
        placeholder={t('feedback.commentPlaceholder')}
        className={`input mt-1.5 resize-y ${ta ? 'font-tamil' : ''}`}
      />

      {mutation.isError && (
        <p role="alert" className="mt-2 text-sm text-risk-high">
          {t('common.error')}
        </p>
      )}

      <button type="submit" disabled={rating === 0 || mutation.isPending} className="btn-accent mt-4">
        {mutation.isPending ? t('common.loading') : t('feedback.submit')}
      </button>

      {rating === 0 && (
        <p className={`mt-2 text-xs text-slate-500 ${ta ? 'font-tamil' : ''}`}>
          {t('feedback.pickStars')}
        </p>
      )}
    </form>
  )
}
