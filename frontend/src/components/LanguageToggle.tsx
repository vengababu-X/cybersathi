import { useApp } from '@/context/AppContext'

export default function LanguageToggle() {
  const { language, setLanguage } = useApp()

  return (
    <div
      className="inline-flex overflow-hidden rounded-xl border border-white/30"
      role="group"
      aria-label="Language / மொழி"
    >
      {(['en', 'ta'] as const).map((code) => (
        <button
          key={code}
          onClick={() => setLanguage(code)}
          aria-pressed={language === code}
          className={`min-h-[40px] px-3 text-sm font-semibold transition-colors ${
            language === code ? 'bg-white text-brand-800' : 'text-white/90 hover:bg-white/10'
          } ${code === 'ta' ? 'font-tamil' : ''}`}
        >
          {code === 'en' ? 'EN' : 'தமிழ்'}
        </button>
      ))}
    </div>
  )
}
