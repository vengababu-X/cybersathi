import { describe, expect, it } from 'vitest'
import { boostContrast, decodeFromImageData } from '@/lib/decodeQr'
import fixture from './fixtures/qrMatrix.json'

/**
 * The fixture is a real QR matrix (33x33 modules) generated with the `qrcode` library from
 * an actual upi:// payload. Rendering it here at different scales, contrasts and quiet-zone
 * sizes reproduces the ways a workshop photo goes wrong, without needing image files.
 */

const { matrix, payload } = fixture as { matrix: number[][]; payload: string; size: number }

interface RenderOptions {
  /** Pixels per QR module. Below ~2 the code is unreadable by design. */
  scale?: number
  /** Quiet zone in modules. The spec requires 4; less than that breaks detection. */
  quiet?: number
  /** Foreground/background luminance, for simulating washed-out photos. */
  dark?: number
  light?: number
  /** Swap dark and light, as on a white-on-black poster. */
  invert?: boolean
  /** Uniform random noise amplitude, for paper grain and sensor noise. */
  noise?: number
}

function render(options: RenderOptions = {}): ImageData {
  const {
    scale = 6, quiet = 4, dark = 0, light = 255, invert = false, noise = 0,
  } = options

  const modules = matrix.length
  const size = (modules + quiet * 2) * scale
  const data = new Uint8ClampedArray(size * size * 4)

  const fg = invert ? light : dark
  const bg = invert ? dark : light

  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const mx = Math.floor(x / scale) - quiet
      const my = Math.floor(y / scale) - quiet
      const inside = mx >= 0 && my >= 0 && mx < modules && my < modules
      const isDark = inside && matrix[my][mx] === 1

      let v = isDark ? fg : bg
      if (noise > 0) v += (Math.random() - 0.5) * 2 * noise

      const i = (y * size + x) * 4
      data[i] = data[i + 1] = data[i + 2] = v
      data[i + 3] = 255
    }
  }

  return new ImageData(data, size, size)
}

describe('decodeFromImageData', () => {
  it('reads a clean QR code', () => {
    const result = decodeFromImageData(render())
    expect(result.data).toBe(payload)
  })

  it('reads a small QR code', () => {
    expect(decodeFromImageData(render({ scale: 3 })).data).toBe(payload)
  })

  it('reads a large QR code', () => {
    expect(decodeFromImageData(render({ scale: 14 })).data).toBe(payload)
  })

  it('reads an inverted (white-on-dark) code', () => {
    // Needs jsQR's inversionAttempts: 'attemptBoth'. Without it this returns null.
    expect(decodeFromImageData(render({ invert: true })).data).toBe(payload)
  })

  it('reads a washed-out low-contrast photo that the direct pass cannot', () => {
    // Luminance range of 20 out of 255 — a glare-flattened photo of a printed code.
    // Measured: jsQR fails on this directly below a range of about 45, and the contrast
    // pass rescues it down to roughly 10. Below that it is noise either way.
    const result = decodeFromImageData(render({ dark: 118, light: 138 }))
    expect(result.data).toBe(payload)
    expect(result.strategy).toBe('contrast')
  })

  it('still reads a moderately faded photo on the direct pass', () => {
    const result = decodeFromImageData(render({ dark: 105, light: 165 }))
    expect(result.data).toBe(payload)
  })

  it('reads a noisy photo', () => {
    expect(decodeFromImageData(render({ noise: 30 })).data).toBe(payload)
  })

  it('reads a code with a tight quiet zone', () => {
    expect(decodeFromImageData(render({ quiet: 2 })).data).toBe(payload)
  })

  it('returns null for an image with no QR code, without throwing', () => {
    const blank = new ImageData(new Uint8ClampedArray(200 * 200 * 4).fill(255), 200, 200)
    const result = decodeFromImageData(blank)
    expect(result.data).toBeNull()
    expect(result.attempts).toBeGreaterThan(0)
  })

  it('reports which strategy succeeded', () => {
    expect(decodeFromImageData(render()).strategy).toBe('direct')
  })
})

describe('boostContrast', () => {
  it('stretches a narrow luminance range to full range', () => {
    const flat = render({ dark: 110, light: 150 })
    const boosted = boostContrast(flat)

    let min = 255
    let max = 0
    for (let i = 0; i < boosted.data.length; i += 4) {
      min = Math.min(min, boosted.data[i])
      max = Math.max(max, boosted.data[i])
    }
    expect(min).toBeLessThan(20)
    expect(max).toBeGreaterThan(235)
  })

  it('leaves a uniform image alone instead of dividing by zero', () => {
    const uniform = new ImageData(new Uint8ClampedArray(40 * 40 * 4).fill(128), 40, 40)
    const boosted = boostContrast(uniform)
    expect(Number.isNaN(boosted.data[0])).toBe(false)
    expect(boosted.data[0]).toBe(128)
  })

  it('produces an opaque image', () => {
    const boosted = boostContrast(render())
    expect(boosted.data[3]).toBe(255)
  })
})
