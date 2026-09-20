import { AlertTriangle, CheckCircle2, ShieldAlert } from 'lucide-react'
import type { RiskLabel } from '@/types'

/**
 * Risk is communicated three ways at once — colour, icon and text label.
 * Colour alone excludes colour-blind users, which is roughly 1 in 12 men.
 *
 * This lives outside RiskMeter.tsx so that module only exports a component: a file that
 * exports both a component and a data table cannot use Vite's fast refresh.
 */
export const RISK_STYLES: Record<RiskLabel, {
  stroke: string; text: string; bg: string; border: string; Icon: typeof CheckCircle2
}> = {
  safe: {
    stroke: '#15803d', text: 'text-risk-safe', bg: 'bg-green-50',
    border: 'border-green-300', Icon: CheckCircle2,
  },
  suspicious: {
    stroke: '#b45309', text: 'text-risk-suspicious', bg: 'bg-amber-50',
    border: 'border-amber-300', Icon: AlertTriangle,
  },
  high_risk: {
    stroke: '#b91c1c', text: 'text-risk-high', bg: 'bg-red-50',
    border: 'border-red-300', Icon: ShieldAlert,
  },
}
