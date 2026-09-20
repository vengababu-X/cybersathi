import { describe, expect, it } from 'vitest'
import en from '@/i18n/locales/en.json'
import ta from '@/i18n/locales/ta.json'

/** Walk a nested object and collect dotted key paths. */
function keys(obj: Record<string, unknown>, prefix = ''): string[] {
  return Object.entries(obj).flatMap(([k, v]) => {
    const path = prefix ? `${prefix}.${k}` : k
    return v && typeof v === 'object' && !Array.isArray(v)
      ? keys(v as Record<string, unknown>, path)
      : [path]
  })
}

describe('translations', () => {
  it('Tamil has every key English has', () => {
    const missing = keys(en).filter((k) => !keys(ta).includes(k))
    expect(missing).toEqual([])
  })

  it('English has every key Tamil has', () => {
    const extra = keys(ta).filter((k) => !keys(en).includes(k))
    expect(extra).toEqual([])
  })

  it('no Tamil value is left as the English placeholder', () => {
    // A few values are intentionally identical (brand names, "QR & UPI").
    const allowed = new Set(['app.name', 'nav.qr', 'dashboard.cohensD'])
    const untranslated = keys(en).filter((path) => {
      if (allowed.has(path)) return false
      const get = (o: Record<string, unknown>) =>
        path.split('.').reduce<unknown>((acc, p) => (acc as Record<string, unknown>)?.[p], o)
      const a = get(en as Record<string, unknown>)
      const b = get(ta as Record<string, unknown>)
      return typeof a === 'string' && a === b && a.length > 12
    })
    expect(untranslated).toEqual([])
  })
})
