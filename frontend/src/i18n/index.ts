import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import en from './locales/en.json'
import ta from './locales/ta.json'

export const LANGUAGE_KEY = 'cybersathi.language'

const saved = (() => {
  try {
    return localStorage.getItem(LANGUAGE_KEY)
  } catch {
    return null
  }
})()

i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, ta: { translation: ta } },
  lng: saved === 'ta' || saved === 'en' ? saved : 'en',
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
})

export default i18n
