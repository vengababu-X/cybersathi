import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { LANGUAGE_KEY } from '@/i18n'
import { TOKEN_KEY, getMe, login as apiLogin } from '@/api/client'
import type { Language, User } from '@/types'

interface AppContextValue {
  language: Language
  setLanguage: (l: Language) => void
  /** Pick the right half of a bilingual pair for the current language. */
  pick: (en: string, ta: string) => string
  fontScale: number
  setFontScale: (n: number) => void
  highContrast: boolean
  toggleContrast: () => void
  online: boolean
  user: User | null
  signIn: (email: string, password: string) => Promise<void>
  signOut: () => void
}

const AppContext = createContext<AppContextValue | null>(null)

const FONT_KEY = 'cybersathi.fontScale'
const CONTRAST_KEY = 'cybersathi.contrast'

function readStorage(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

function writeStorage(key: string, value: string) {
  try {
    localStorage.setItem(key, value)
  } catch {
    // Private browsing — settings simply do not persist. Not worth failing over.
  }
}

export function AppProvider({ children }: { children: ReactNode }) {
  const { i18n } = useTranslation()
  const [language, setLanguageState] = useState<Language>(
    (i18n.language === 'ta' ? 'ta' : 'en') as Language,
  )
  const [fontScale, setFontScaleState] = useState<number>(() => {
    const raw = Number(readStorage(FONT_KEY))
    return raw >= 1 && raw <= 1.4 ? raw : 1
  })
  const [highContrast, setHighContrast] = useState<boolean>(() => readStorage(CONTRAST_KEY) === '1')
  const [online, setOnline] = useState<boolean>(() => navigator.onLine)
  const [user, setUser] = useState<User | null>(null)

  const setLanguage = useCallback(
    (l: Language) => {
      setLanguageState(l)
      i18n.changeLanguage(l)
      writeStorage(LANGUAGE_KEY, l)
      document.documentElement.lang = l
    },
    [i18n],
  )

  const setFontScale = useCallback((n: number) => {
    setFontScaleState(n)
    writeStorage(FONT_KEY, String(n))
  }, [])

  const toggleContrast = useCallback(() => {
    setHighContrast((prev) => {
      writeStorage(CONTRAST_KEY, prev ? '0' : '1')
      return !prev
    })
  }, [])

  useEffect(() => {
    document.documentElement.style.setProperty('--font-scale', String(fontScale))
  }, [fontScale])

  useEffect(() => {
    document.documentElement.classList.toggle('contrast-boost', highContrast)
  }, [highContrast])

  useEffect(() => {
    document.documentElement.lang = language
  }, [language])

  useEffect(() => {
    const goOnline = () => setOnline(true)
    const goOffline = () => setOnline(false)
    window.addEventListener('online', goOnline)
    window.addEventListener('offline', goOffline)
    return () => {
      window.removeEventListener('online', goOnline)
      window.removeEventListener('offline', goOffline)
    }
  }, [])

  // Restore an existing session on load.
  useEffect(() => {
    if (!readStorage(TOKEN_KEY)) return
    getMe()
      .then(setUser)
      .catch(() => {
        try {
          localStorage.removeItem(TOKEN_KEY)
        } catch { /* ignore */ }
      })
  }, [])

  const signIn = useCallback(async (email: string, password: string) => {
    const data = await apiLogin(email, password)
    writeStorage(TOKEN_KEY, data.access_token)
    setUser(data.user)
  }, [])

  const signOut = useCallback(() => {
    try {
      localStorage.removeItem(TOKEN_KEY)
    } catch { /* ignore */ }
    setUser(null)
  }, [])

  const pick = useCallback((en: string, ta: string) => (language === 'ta' ? ta || en : en), [language])

  const value = useMemo(
    () => ({
      language, setLanguage, pick,
      fontScale, setFontScale,
      highContrast, toggleContrast,
      online, user, signIn, signOut,
    }),
    [language, setLanguage, pick, fontScale, setFontScale, highContrast, toggleContrast, online, user, signIn, signOut],
  )

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useApp() {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp must be used inside AppProvider')
  return ctx
}
