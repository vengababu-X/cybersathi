import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ShieldQuestion } from 'lucide-react'

export default function NotFound() {
  const { t } = useTranslation()
  return (
    <div className="card mx-auto max-w-md p-10 text-center">
      <ShieldQuestion size={40} className="mx-auto text-slate-300" aria-hidden />
      <h1 className="mt-3 text-xl font-bold text-brand-800">{t('common.notFound')}</h1>
      <Link to="/" className="btn-primary mt-5">{t('nav.home')}</Link>
    </div>
  )
}
