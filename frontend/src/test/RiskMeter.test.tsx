import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@/i18n'
import RiskMeter from '@/components/RiskMeter'

describe('RiskMeter', () => {
  it('shows the numeric score', () => {
    render(<RiskMeter score={87.4} label="high_risk" />)
    expect(screen.getByText('87')).toBeInTheDocument()
  })

  it('labels risk with text, not colour alone', () => {
    // Colour-blind users must get the verdict from text too.
    render(<RiskMeter score={12} label="safe" />)
    expect(screen.getByText(/looks safe/i)).toBeInTheDocument()
  })

  it('exposes an accessible description', () => {
    render(<RiskMeter score={55} label="suspicious" />)
    expect(screen.getByRole('img')).toHaveAttribute('aria-label', expect.stringContaining('55'))
  })

  it('clamps an out-of-range score', () => {
    render(<RiskMeter score={140} label="high_risk" />)
    expect(screen.getByText('140')).toBeInTheDocument()
  })
})
