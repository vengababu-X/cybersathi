import { describe, expect, it } from 'vitest'
import {
  assistantSchema,
  bulkUrlSchema,
  errorText,
  loginSchema,
  participantSchema,
  qrPayloadSchema,
  scamTextSchema,
  urlCheckSchema,
  workshopSchema,
} from '@/forms/validation'

/** Stands in for i18next: echoes the key, and shows the count when one was interpolated. */
const fakeT = ((key: string, options?: { count?: number }) =>
  options?.count === undefined ? key : `${key}(${options.count})`) as never

const firstError = (result: { success: boolean; error?: { issues: { message: string }[] } }) =>
  result.success ? null : result.error!.issues[0].message

describe('errorText', () => {
  it('resolves a plain key', () => {
    expect(errorText(fakeT, 'validation.required')).toBe('validation.required')
  })

  it('passes the number after the pipe through as count', () => {
    expect(errorText(fakeT, 'validation.minLength|5')).toBe('validation.minLength(5)')
  })

  it('returns an empty string when there is no message', () => {
    expect(errorText(fakeT, undefined)).toBe('')
  })

  it('leaves a resolver message that is not a validation key alone', () => {
    expect(errorText(fakeT, 'Something unexpected')).toBe('Something unexpected')
  })
})

describe('loginSchema', () => {
  it('accepts a well-formed email and a password', () => {
    expect(loginSchema.safeParse({ email: 'admin@cybersathi.org', password: 'Admin@123' }).success).toBe(true)
  })

  it('reports the email key for a malformed address', () => {
    expect(firstError(loginSchema.safeParse({ email: 'not-an-email', password: 'x' }))).toBe('validation.email')
  })

  it('rejects a blank password', () => {
    expect(firstError(loginSchema.safeParse({ email: 'a@b.com', password: '' }))).toBe('validation.required')
  })
})

describe('scamTextSchema', () => {
  it('rejects text that is too short to analyse', () => {
    expect(firstError(scamTextSchema.safeParse({ text: 'hi', channel: 'sms' }))).toBe('validation.minLength|3')
  })

  it('accepts a pasted message and trims it', () => {
    const parsed = scamTextSchema.safeParse({ text: '  Your KYC expired  ', channel: 'whatsapp' })
    expect(parsed.success).toBe(true)
    expect(parsed.data?.text).toBe('Your KYC expired')
  })

  it('catches a message past the API ceiling before it is sent', () => {
    const result = scamTextSchema.safeParse({ text: 'x'.repeat(5001), channel: 'sms' })
    expect(firstError(result)).toBe('validation.maxLength|5000')
  })

  it('rejects an unknown channel', () => {
    expect(scamTextSchema.safeParse({ text: 'hello there', channel: 'telegram' }).success).toBe(false)
  })
})

describe('urlCheckSchema', () => {
  it.each([
    'https://www.google.com',
    'hxxp://sbi-kyc-update[.]xyz/verify',
    'sbi-kyc.xyz',
    'http://192.168.44.9/bank/login',
  ])('accepts %s', (url) => {
    expect(urlCheckSchema.safeParse({ url }).success).toBe(true)
  })

  it('rejects something that is not a web address', () => {
    expect(firstError(urlCheckSchema.safeParse({ url: 'call me instead' }))).toBe('validation.url')
  })
})

describe('bulkUrlSchema', () => {
  it('accepts twenty links', () => {
    const urls = Array.from({ length: 20 }, (_, i) => `https://example${i}.com`).join('\n')
    expect(bulkUrlSchema.safeParse({ urls }).success).toBe(true)
  })

  it('rejects twenty-one links with the count in the message', () => {
    const urls = Array.from({ length: 21 }, (_, i) => `https://example${i}.com`).join('\n')
    expect(firstError(bulkUrlSchema.safeParse({ urls }))).toBe('validation.bulkLimit|20')
  })
})

describe('qrPayloadSchema and assistantSchema', () => {
  it('accepts a UPI deep link', () => {
    expect(qrPayloadSchema.safeParse({ payload: 'upi://pay?pa=someone@bank&am=0' }).success).toBe(true)
  })

  it('caps a question at the API limit', () => {
    expect(firstError(assistantSchema.safeParse({ question: 'x'.repeat(1001) }))).toBe('validation.maxLength|1000')
  })
})

describe('workshopSchema', () => {
  const valid = {
    title_en: 'Fraud awareness for seniors',
    title_ta: 'மூத்த குடிமக்களுக்கான விழிப்புணர்வு',
    venue: 'Panchayat hall',
    district: 'Madurai',
    conducted_on: '2026-09-20',
    audience_type: 'senior' as const,
    participants_expected: 25,
  }

  it('accepts a complete workshop', () => {
    expect(workshopSchema.safeParse(valid).success).toBe(true)
  })

  it('rejects a malformed date', () => {
    expect(firstError(workshopSchema.safeParse({ ...valid, conducted_on: '20-09-2026' }))).toBe('validation.date')
  })

  it('rejects a non-numeric expected count', () => {
    expect(firstError(workshopSchema.safeParse({ ...valid, participants_expected: Number.NaN })))
      .toBe('validation.number')
  })

  it('rejects a count outside the allowed range', () => {
    expect(firstError(workshopSchema.safeParse({ ...valid, participants_expected: 0 })))
      .toBe('validation.min|1')
  })
})

describe('participantSchema', () => {
  const base = {
    name: 'Lakshmi',
    age_group: 'senior' as const,
    gender: 'female' as const,
    language: 'ta' as const,
    phone: '',
    consent_given: true,
  }

  it('accepts an empty phone number', () => {
    expect(participantSchema.safeParse(base).success).toBe(true)
  })

  it('accepts a ten-digit phone number', () => {
    expect(participantSchema.safeParse({ ...base, phone: '9876543210' }).success).toBe(true)
  })

  it('rejects a phone number that is not ten digits', () => {
    expect(firstError(participantSchema.safeParse({ ...base, phone: '12345' }))).toBe('validation.phone')
  })
})
