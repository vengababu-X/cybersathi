import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import { Search, BookOpen, ArrowRight, Eye } from 'lucide-react'
import { getArticles, getCategories } from '@/api/client'
import { useApp } from '@/context/AppContext'
import { EmptyState, SectionTitle, Skeleton } from '@/components/ui/Bits'

const SEVERITY: Record<string, string> = {
  critical: 'bg-red-100 text-red-800',
  high: 'bg-amber-100 text-amber-900',
  medium: 'bg-slate-100 text-slate-700',
}

export default function KnowledgeBase() {
  const { t } = useTranslation()
  const { pick, language } = useApp()
  const [params, setParams] = useSearchParams()
  const category = params.get('category') ?? ''
  const [query, setQuery] = useState('')

  const { data: categories } = useQuery({ queryKey: ['kb-categories'], queryFn: getCategories })
  const { data: articles, isLoading } = useQuery({
    queryKey: ['kb-articles', category, query],
    queryFn: () => getArticles({ category: category || undefined, q: query || undefined }),
  })

  const ta = language === 'ta'

  return (
    <div className="space-y-6">
      <SectionTitle title={t('kb.title')} subtitle={t('kb.subtitle')} />

      <div className="card p-4">
        <div className="relative">
          <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" aria-hidden />
          <label htmlFor="kb-search" className="sr-only">{t('common.search')}</label>
          <input
            id="kb-search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t('kb.searchPlaceholder')}
            className="input pl-11"
          />
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <button
            onClick={() => setParams({})}
            aria-pressed={!category}
            className={`chip min-h-[38px] border px-3 ${
              !category ? 'border-brand-600 bg-brand-50 text-brand-800' : 'border-slate-300 bg-white text-slate-600'
            }`}
          >
            {t('kb.allCategories')}
          </button>
          {(categories ?? []).map((c) => (
            <button
              key={c.category}
              onClick={() => setParams({ category: c.category })}
              aria-pressed={category === c.category}
              className={`chip min-h-[38px] border px-3 ${ta ? 'font-tamil' : ''} ${
                category === c.category
                  ? 'border-brand-600 bg-brand-50 text-brand-800'
                  : 'border-slate-300 bg-white text-slate-600 hover:bg-slate-50'
              }`}
            >
              {pick(c.label_en, c.label_ta)}
              <span className="ml-1 text-[10px] text-slate-400">{c.count}</span>
            </button>
          ))}
        </div>
      </div>

      {isLoading && (
        <div className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-40" />)}
        </div>
      )}

      {articles?.length === 0 && <EmptyState message={t('kb.noResults')} />}

      <div className="grid gap-4 md:grid-cols-2">
        {(articles ?? []).map((a) => (
          <Link
            key={a.slug}
            to={`/learn/${a.slug}`}
            className="card group flex flex-col p-5 transition-shadow hover:shadow-md"
          >
            <div className="mb-2 flex items-center gap-2">
              <span className={`chip ${SEVERITY[a.severity] ?? SEVERITY.medium}`}>{a.severity}</span>
              <span className="chip bg-slate-100 text-slate-600">{a.category}</span>
              <span className="ml-auto inline-flex items-center gap-1 text-xs text-slate-400">
                <Eye size={12} aria-hidden /> {a.views}
              </span>
            </div>

            <h3 className={`font-bold leading-snug text-brand-800 ${ta ? 'font-tamil' : ''}`}>
              {pick(a.title_en, a.title_ta)}
            </h3>
            <p className={`mt-2 flex-1 text-sm leading-relaxed text-slate-600 ${ta ? 'font-tamil' : ''}`}>
              {pick(a.summary_en, a.summary_ta)}
            </p>

            <span className="mt-3 inline-flex items-center gap-1.5 text-sm font-semibold text-accent-700">
              <BookOpen size={15} aria-hidden /> {t('kb.readArticle')}
              <ArrowRight size={14} className="transition-transform group-hover:translate-x-1" aria-hidden />
            </span>
          </Link>
        ))}
      </div>
    </div>
  )
}
