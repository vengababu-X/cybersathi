import type { TFunction } from 'i18next'
import { z } from 'zod'

/**
 * Form schemas for every validated input in the app.
 *
 * Message convention: a schema never contains user-facing English. Each failure carries an
 * i18next key instead, and `errorText()` resolves it at render time — so the same form
 * validates in English and Tamil without duplicating any rules.
 *
 * A key may carry an interpolated number after a pipe: `"validation.minLength|5"`.
 */

const required = { error: 'validation.required' }
const email = { error: 'validation.email' }
const phone = { error: 'validation.phone' }
const url = { error: 'validation.url' }
const date = { error: 'validation.date' }

// --- Auth -------------------------------------------------------------------

export const loginSchema = z.object({
  email: z.string().trim().min(1, required).email(email),
  password: z.string().min(1, required),
})
export type LoginForm = z.infer<typeof loginSchema>

// --- Modules 1 and 2: the two public detectors ---------------------------------

export const scamTextSchema = z.object({
  text: z
    .string()
    .trim()
    .min(3, { error: 'validation.minLength|3' })
    .max(5000, { error: 'validation.maxLength|5000' }),
  channel: z.enum(['sms', 'whatsapp', 'email', 'call_transcript'], required),
})
export type ScamTextForm = z.infer<typeof scamTextSchema>

// Accepts defanged input on purpose: "hxxp://sbi-kyc[.]xyz" is what a user copies out of a
// report, and the backend undefangs it. Only the shape is checked here.
const URL_SHAPE = /^(hxxps?|https?):\/\/\S+$|^\S+\.(com|in|org|net|xyz|top|buzz|tk|ml|ga|cf|gq|info|co|io|club|online|site|shop|live|app|dev|me|cc|ru|su|cn|to|link|click|zip|mov|shop|store)(\/\S*)?$/i

// The 2000 cap mirrors the API's own limit, so an over-long paste is caught before it is sent.
export const urlCheckSchema = z.object({
  url: z
    .string()
    .trim()
    .min(1, required)
    .max(2000, { error: 'validation.maxLength|2000' })
    .regex(URL_SHAPE, url),
})
export type UrlCheckForm = z.infer<typeof urlCheckSchema>

export const bulkUrlSchema = z.object({
  urls: z
    .string()
    .trim()
    .min(1, required)
    .refine(
      (value) => value.split(/\r?\n/).filter((line) => line.trim()).length <= 20,
      { error: 'validation.bulkLimit|20' },
    ),
})
export type BulkUrlForm = z.infer<typeof bulkUrlSchema>

// --- Module 3: QR / UPI --------------------------------------------------------

export const qrPayloadSchema = z.object({
  payload: z
    .string()
    .trim()
    .min(3, { error: 'validation.minLength|3' })
    // 3000 is the API's ceiling for a decoded QR payload.
    .max(3000, { error: 'validation.maxLength|3000' }),
})
export type QrPayloadForm = z.infer<typeof qrPayloadSchema>

// --- Module 5: the assistant ----------------------------------------------------

export const assistantSchema = z.object({
  question: z
    .string()
    .trim()
    .min(2, { error: 'validation.minLength|2' })
    // 1000 is the API's ceiling for a question.
    .max(1000, { error: 'validation.maxLength|1000' }),
})
export type AssistantForm = z.infer<typeof assistantSchema>

// --- Module 6: workshops and participants ---------------------------------------

export const workshopSchema = z.object({
  title_en: z.string().trim().min(3, { error: 'validation.minLength|3' }).max(200, { error: 'validation.maxLength|200' }),
  title_ta: z.string().trim().min(3, { error: 'validation.minLength|3' }).max(200, { error: 'validation.maxLength|200' }),
  venue: z.string().trim().min(2, { error: 'validation.minLength|2' }).max(200, { error: 'validation.maxLength|200' }),
  district: z.string().trim().min(2, { error: 'validation.minLength|2' }).max(80, { error: 'validation.maxLength|80' }),
  // An <input type="date"> yields exactly YYYY-MM-DD, which is what the API expects.
  conducted_on: z.string().trim().min(1, date).regex(/^\d{4}-\d{2}-\d{2}$/, date),
  audience_type: z.enum(['school', 'college', 'senior', 'rural', 'women', 'mixed'], required),
  participants_expected: z
    .number({ error: 'validation.number' })
    .int({ error: 'validation.wholeNumber' })
    .min(1, { error: 'validation.min|1' })
    .max(500, { error: 'validation.max|500' }),
})
export type WorkshopForm = z.infer<typeof workshopSchema>

export const participantSchema = z.object({
  name: z.string().trim().min(2, { error: 'validation.minLength|2' }).max(120, { error: 'validation.maxLength|120' }),
  age_group: z.enum(['student', 'adult', 'senior'], required),
  gender: z.enum(['male', 'female', 'other'], required),
  language: z.enum(['en', 'ta'], required),
  // Optional: an empty string is valid, anything else must be a 10-digit number. The backend
  // stores only a salted hash of it, never the number itself.
  phone: z.union([z.literal(''), z.string().trim().regex(/^\d{10}$/, phone)]),
  consent_given: z.boolean(),
})
export type ParticipantForm = z.infer<typeof participantSchema>

/**
 * Resolve a schema message key into display text.
 *
 * Renders `"validation.minLength|5"` as the translated string with `count` set to 5.
 */
export function errorText(t: TFunction, message?: string): string {
  if (!message) return ''
  const [key, param] = message.split('|')
  if (!key.startsWith('validation.')) return message // a raw message from the resolver
  return param === undefined ? t(key) : t(key, { count: Number(param) })
}
