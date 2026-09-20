export type Language = 'en' | 'ta'
export type RiskLabel = 'safe' | 'suspicious' | 'high_risk'
export type Channel = 'sms' | 'whatsapp' | 'email' | 'call_transcript'

export interface Bilingual { en: string; ta: string }
export interface BilingualList { en: string[]; ta: string[] }

export interface Signal {
  rule_id: string
  category: string
  matched_snippet: string
  why_en: string
  why_ta: string
  weight: number
}

export interface ScamResult {
  analysis_id: number | null
  risk_score: number
  risk_label: RiskLabel
  primary_category: string
  categories: { name: string; confidence: number }[]
  language_detected: Language
  redacted_text: string
  pii_found: string[]
  signals: Signal[]
  top_terms: { term: string; contribution: number }[]
  explanation: Bilingual
  safe_actions: BilingualList
  related_kb_slugs: string[]
  helplines: Record<string, string>
  disclaimer: Bilingual
  model_used: boolean
}

export interface UrlReason { feature: string; value: number; why_en: string; why_ta: string }

export interface UrlResult {
  check_id: number | null
  url_defanged: string
  risk_score: number
  risk_label: RiskLabel
  features: Record<string, number>
  top_reasons: UrlReason[]
  lookalike_brand: string | null
  advice: Bilingual
  disclaimer: Bilingual
  model_used: boolean
}

export interface QrResult {
  payload_type: string
  risk_label: RiskLabel
  risk_score: number
  parsed: Record<string, string>
  signals: Signal[]
  golden_rule: Bilingual
  advice: Bilingual
  disclaimer: Bilingual
}

export interface ScenarioChoice {
  text_en: string; text_ta: string; is_safe: boolean
  feedback_en: string; feedback_ta: string
}
export interface Scenario {
  id: string
  title_en: string; title_ta: string
  situation_en: string; situation_ta: string
  choices: ScenarioChoice[]
  lesson_en: string; lesson_ta: string
}

export interface KbSummary {
  id: number; slug: string; category: string; severity: string
  title_en: string; title_ta: string
  summary_en: string; summary_ta: string
  helpline: string; views: number
}

export interface KbDetail extends KbSummary {
  body_en: string; body_ta: string
  red_flags: BilingualList
  safe_actions: BilingualList
  victim_steps: BilingualList
  real_example_en: string; real_example_ta: string
  tags: string
}

export interface KbCategory {
  category: string; count: number; label_en: string; label_ta: string
}

export type AssistantSource = 'rule' | 'kb' | 'llm' | 'fallback' | 'refusal' | 'analyzer'

export interface QuickAction {
  kind: 'call' | 'link' | 'route'
  value: string
  label: string
}

export interface AssistantResponse {
  log_id: number | null
  answer: string
  language: Language
  source: AssistantSource
  intent: string
  confidence: number
  /** True when the answer must be acted on now — the UI styles it as an alert. */
  urgent: boolean
  related_articles: { slug: string; title: string; score: number }[]
  suggested_questions: string[]
  quick_actions: QuickAction[]
  disclaimer: string
}

export interface Workshop {
  id: number
  title_en: string; title_ta: string
  venue: string; district: string; locality: string | null
  conducted_on: string
  audience_type: string
  participants_expected: number
  notes: string | null
}

export interface Participant {
  id: number; workshop_id: number; name: string
  age_group: string; gender: string | null
  language: Language; consent_given: boolean
}

export interface QuizQuestion {
  id: number; category: string; difficulty: string
  question: string
  options: { index: number; text: string }[]
}

export interface AnswerReview {
  question_id: number; question: string
  your_answer: string; correct_answer: string
  is_correct: boolean; explanation: string
}

export interface AssessmentResult {
  assessment_id: number
  score: number; max_score: number; percentage: number
  per_category: Record<string, { correct: number; total: number }>
  weak_categories: string[]
  review: AnswerReview[]
}

export interface ImprovementResult {
  participant_id: number
  participant_name: string
  pre_score: number | null
  post_score: number | null
  max_score: number
  pre_percentage: number | null
  post_percentage: number | null
  /** null when pre_score is 0 — percentage change is undefined (division by zero). */
  improvement_percentage: number | null
  absolute_gain: number | null
  normalized_gain: number | null
  band: string
  note: string | null
}

export interface DashboardSummary {
  totals: {
    workshops: number; participants: number
    messages_analyzed: number; urls_checked: number; assistant_queries: number
  }
  awareness: {
    avg_pre_pct: number | null
    avg_post_pct: number | null
    avg_improvement_pct: number | null
    median_improvement_pct: number | null
    std_dev_improvement: number | null
    cohens_d: number | null
    t_statistic: number | null
    p_value: number | null
    n_pairs: number
    moved_to_aware_pct: number | null
    undefined_improvement_count: number
    interpretation_note: Bilingual | null
  }
  improvement_by_category: { category: string; pre: number; post: number; delta: number }[]
  by_age_group: GroupStat[]
  by_language: GroupStat[]
  by_district: GroupStat[]
  top_scam_categories: { name: string; count: number }[]
  risk_distribution: Record<string, number>
  timeline: { date: string; analyses: number; participants: number }[]
  feedback: { avg_rating: number; count: number }
}

export interface GroupStat {
  group: string; avg_pre: number; avg_post: number; avg_improvement: number; n: number
}

export interface User {
  id: number; full_name: string; email: string
  role: 'admin' | 'volunteer' | 'participant'
  preferred_language: Language
  age_group: string | null; locality: string | null
  is_active: boolean
  created_at: string
}

export interface ScamExample {
  id: number; category: string; language: Language; text: string; label: string
}

export interface MetaStatus {
  app: string; version: string
  text_model_loaded: boolean; url_model_loaded: boolean
  llm_enabled: boolean; languages: string[]
  offline_capable: boolean; api_keys_required: boolean
}
