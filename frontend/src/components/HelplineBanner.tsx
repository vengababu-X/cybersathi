import { Phone, ExternalLink } from 'lucide-react'
import { useTranslation } from 'react-i18next'

/**
 * Always visible. A person who has just been defrauded should never have to hunt
 * for the number — the first hour is when the money can still be frozen.
 */
export default function HelplineBanner() {
  const { t } = useTranslation()
  return (
    <div className="no-print bg-risk-high text-white">
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-2 px-4 py-2.5 text-sm sm:flex-row sm:justify-center">
        <span className="text-center font-medium">{t('helpline.banner')}</span>
        <div className="flex items-center gap-3">
          <a href="tel:1930" className="inline-flex items-center gap-1.5 rounded-lg bg-white/15 px-3 py-1 font-bold hover:bg-white/25">
            <Phone size={14} aria-hidden /> 1930
          </a>
          <a
            href="https://cybercrime.gov.in" target="_blank" rel="noopener noreferrer"
            className="inline-flex items-center gap-1 underline underline-offset-2 hover:no-underline"
          >
            cybercrime.gov.in <ExternalLink size={12} aria-hidden />
          </a>
        </div>
      </div>
    </div>
  )
}
