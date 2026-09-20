import { useState } from 'react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  Shield, Menu, X, WifiOff, Contrast, LogOut, LogIn, Type,
} from 'lucide-react'
import LanguageToggle from '@/components/LanguageToggle'
import HelplineBanner from '@/components/HelplineBanner'
import { useApp } from '@/context/AppContext'

const NAV = [
  { to: '/', key: 'home', end: true },
  { to: '/analyzer', key: 'analyzer' },
  { to: '/url', key: 'url' },
  { to: '/qr', key: 'qr' },
  { to: '/learn', key: 'kb' },
  { to: '/ask', key: 'assistant' },
  { to: '/assessment', key: 'assessment' },
  { to: '/dashboard', key: 'dashboard' },
  { to: '/workshops', key: 'workshops' },
  { to: '/about', key: 'about' },
  // Rendered only for administrators; the page itself also guards on role.
  { to: '/admin', key: 'admin', adminOnly: true },
]

export default function Layout() {
  const { t } = useTranslation()
  const { online, highContrast, toggleContrast, fontScale, setFontScale, user, signOut } = useApp()
  const [open, setOpen] = useState(false)

  const cycleFontScale = () => {
    const next = fontScale >= 1.3 ? 1 : Number((fontScale + 0.15).toFixed(2))
    setFontScale(next)
  }

  // The Admin link is hidden from everyone else. This is presentation only — the route and
  // every admin endpoint enforce the role independently.
  const visibleNav = NAV.filter((item) => !item.adminOnly || user?.role === 'admin')

  return (
    <div className="flex min-h-screen flex-col">
      <HelplineBanner />

      <header className="no-print sticky top-0 z-40 bg-brand-800 text-white shadow-md">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-3">
          <Link to="/" className="flex items-center gap-2 font-bold" onClick={() => setOpen(false)}>
            <Shield size={24} aria-hidden />
            <span className="text-lg">{t('app.name')}</span>
          </Link>

          <nav className="ml-6 hidden flex-1 items-center gap-1 lg:flex" aria-label="Main">
            {visibleNav.slice(0, 7).map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                    isActive ? 'bg-white/20' : 'hover:bg-white/10'
                  }`
                }
              >
                {t(`nav.${item.key}`)}
              </NavLink>
            ))}
          </nav>

          <div className="ml-auto flex items-center gap-2">
            <button
              onClick={cycleFontScale}
              title={t('common.textSize')}
              aria-label={t('common.textSize')}
              className="hidden min-h-[40px] items-center gap-1 rounded-lg px-2.5 text-sm hover:bg-white/10 sm:inline-flex"
            >
              <Type size={16} aria-hidden />
              <span className="font-semibold">{fontScale === 1 ? 'A' : fontScale < 1.3 ? 'A+' : 'A++'}</span>
            </button>

            <button
              onClick={toggleContrast}
              title={t('common.contrast')}
              aria-label={t('common.contrast')}
              aria-pressed={highContrast}
              className="hidden min-h-[40px] items-center rounded-lg px-2.5 hover:bg-white/10 sm:inline-flex"
            >
              <Contrast size={16} aria-hidden />
            </button>

            <LanguageToggle />

            {user ? (
              <button
                onClick={signOut}
                className="hidden min-h-[40px] items-center gap-1.5 rounded-lg px-3 text-sm hover:bg-white/10 md:inline-flex"
              >
                <LogOut size={15} aria-hidden /> {t('nav.logout')}
              </button>
            ) : (
              <Link
                to="/login"
                className="hidden min-h-[40px] items-center gap-1.5 rounded-lg px-3 text-sm hover:bg-white/10 md:inline-flex"
              >
                <LogIn size={15} aria-hidden /> {t('nav.login')}
              </Link>
            )}

            <button
              className="inline-flex min-h-[44px] min-w-[44px] items-center justify-center rounded-lg hover:bg-white/10 lg:hidden"
              onClick={() => setOpen((v) => !v)}
              aria-expanded={open}
              aria-label={t('nav.menu')}
            >
              {open ? <X size={22} /> : <Menu size={22} />}
            </button>
          </div>
        </div>

        {open && (
          <nav className="border-t border-white/15 bg-brand-900 lg:hidden" aria-label="Mobile">
            <div className="mx-auto grid max-w-6xl grid-cols-2 gap-1 px-3 py-3">
              {visibleNav.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  onClick={() => setOpen(false)}
                  className={({ isActive }) =>
                    `min-h-[44px] rounded-lg px-3 py-2.5 text-sm font-medium ${
                      isActive ? 'bg-white/20' : 'hover:bg-white/10'
                    }`
                  }
                >
                  {t(`nav.${item.key}`)}
                </NavLink>
              ))}
              <Link
                to="/login"
                onClick={() => setOpen(false)}
                className="min-h-[44px] rounded-lg px-3 py-2.5 text-sm font-medium hover:bg-white/10 md:hidden"
              >
                {user ? t('nav.logout') : t('nav.login')}
              </Link>
            </div>
          </nav>
        )}
      </header>

      {!online && (
        <div className="no-print flex items-center justify-center gap-2 bg-amber-100 px-4 py-2 text-sm text-amber-900">
          <WifiOff size={15} aria-hidden />
          {t('common.offline')}
        </div>
      )}

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:py-8">
        <Outlet />
      </main>

      <footer className="no-print border-t border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-4 py-6 text-center text-sm text-slate-500">
          <p className="font-medium text-slate-700">
            {t('app.name')} — {t('app.tagline')}
          </p>
          <p className="mt-1">{t('disclaimer.full')}</p>
          <p className="mt-2 text-xs">{t('home.offlineNote')}</p>
        </div>
      </footer>
    </div>
  )
}
