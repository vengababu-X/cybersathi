import { useTranslation } from 'react-i18next'
import type { RiskLabel } from '@/types'
import { RISK_STYLES } from '@/components/riskStyles'

interface Props {
  score: number
  label: RiskLabel
  size?: number
}

export default function RiskMeter({ score, label, size = 168 }: Props) {
  const { t } = useTranslation()
  const style = RISK_STYLES[label]
  const { Icon } = style

  const radius = (size - 20) / 2
  const circumference = Math.PI * radius // semicircle
  const target = circumference * (1 - Math.min(Math.max(score, 0), 100) / 100)

  return (
    <div
      className="flex flex-col items-center"
      role="img"
      aria-label={`${t('common.score')} ${Math.round(score)} ${t('risk.outOf')} — ${t(`risk.${label}`)}`}
    >
      <svg width={size} height={size / 2 + 16} viewBox={`0 0 ${size} ${size / 2 + 16}`}>
        <path
          d={`M 10 ${size / 2} A ${radius} ${radius} 0 0 1 ${size - 10} ${size / 2}`}
          fill="none" stroke="#e2e8f0" strokeWidth="14" strokeLinecap="round"
        />
        <path
          d={`M 10 ${size / 2} A ${radius} ${radius} 0 0 1 ${size - 10} ${size / 2}`}
          fill="none" stroke={style.stroke} strokeWidth="14" strokeLinecap="round"
          strokeDasharray={circumference}
          className="animate-sweep"
          style={{
            ['--dash-full' as string]: `${circumference}`,
            ['--dash-target' as string]: `${target}`,
            strokeDashoffset: target,
          }}
        />
        <text
          x={size / 2} y={size / 2 - 8}
          textAnchor="middle" className="fill-slate-900"
          style={{ fontSize: size * 0.2, fontWeight: 700 }}
        >
          {Math.round(score)}
        </text>
        <text
          x={size / 2} y={size / 2 + 10}
          textAnchor="middle" className="fill-slate-400"
          style={{ fontSize: size * 0.075 }}
        >
          {t('risk.outOf')}
        </text>
      </svg>

      <div className={`chip mt-1 gap-2 px-4 py-2 text-sm ${style.bg} ${style.text} border ${style.border}`}>
        <Icon size={18} aria-hidden />
        <span>{t(`risk.${label}`)}</span>
      </div>
    </div>
  )
}
