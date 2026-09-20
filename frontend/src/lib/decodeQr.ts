import jsQR from 'jsqr'

/**
 * Decode a QR code from an image, trying progressively harder.
 *
 * A single naive pass fails constantly on real photographs, which is exactly what a workshop
 * participant will hand you:
 *
 *  - A 12-megapixel phone photo is ~48M pixels. jsQR scans it slowly and the finder patterns
 *    are tiny relative to the frame, so detection often misses. Downscaling helps far more
 *    than it hurts.
 *  - A QR photographed on a poster or screen sits in the middle of a lot of background. Cropping
 *    to the centre raises the code's share of the frame.
 *  - Shadow, glare and paper texture flatten the contrast below what the default binariser
 *    copes with, so a contrast-stretch pass rescues a lot of otherwise-dead images.
 *  - A QR screenshotted at small size can be below the minimum module size; upscaling fixes it.
 *  - White-on-dark codes need the inverted pass.
 *
 * Each strategy is cheap and the ladder stops at the first hit, so the common case (a clean
 * screenshot) still returns on the first attempt.
 */

export interface DecodeResult {
  data: string | null
  /** Which strategy succeeded — useful in tests and for debugging a stubborn image. */
  strategy?: string
  attempts: number
}

const MAX_DIMENSION = 1600 // beyond this, downscale before the first attempt

function toCanvas(
  source: CanvasImageSource,
  width: number,
  height: number,
  sx = 0,
  sy = 0,
  sw?: number,
  sh?: number,
): ImageData | null {
  const canvas = document.createElement('canvas')
  canvas.width = Math.max(1, Math.round(width))
  canvas.height = Math.max(1, Math.round(height))

  const ctx = canvas.getContext('2d', { willReadFrequently: true })
  if (!ctx) return null

  // A white backdrop matters for images with transparency: an alpha-0 background reads as
  // black to jsQR and destroys the quiet zone.
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  ctx.imageSmoothingEnabled = false

  if (sw !== undefined && sh !== undefined) {
    ctx.drawImage(source, sx, sy, sw, sh, 0, 0, canvas.width, canvas.height)
  } else {
    ctx.drawImage(source, 0, 0, canvas.width, canvas.height)
  }

  try {
    return ctx.getImageData(0, 0, canvas.width, canvas.height)
  } catch {
    // Tainted canvas (cross-origin source) — nothing we can do here.
    return null
  }
}

/** Grayscale, then stretch contrast so a washed-out photo binarises cleanly. */
export function boostContrast(image: ImageData): ImageData {
  const { data, width, height } = image
  const gray = new Uint8ClampedArray(width * height)

  let min = 255
  let max = 0
  for (let i = 0, p = 0; i < data.length; i += 4, p++) {
    // Rec. 601 luma — closer to perceived brightness than a flat average.
    const v = (data[i] * 299 + data[i + 1] * 587 + data[i + 2] * 114) / 1000
    gray[p] = v
    if (v < min) min = v
    if (v > max) max = v
  }

  const range = max - min
  const out = new Uint8ClampedArray(data.length)

  for (let p = 0, i = 0; p < gray.length; p++, i += 4) {
    // Flat image (range ~0) would divide by zero; leave it as-is and let the pass fail.
    const stretched = range > 8 ? ((gray[p] - min) / range) * 255 : gray[p]
    out[i] = out[i + 1] = out[i + 2] = stretched
    out[i + 3] = 255
  }

  return new ImageData(out, width, height)
}

function attempt(image: ImageData | null): string | null {
  if (!image) return null
  try {
    const code = jsQR(image.data, image.width, image.height, { inversionAttempts: 'attemptBoth' })
    return code?.data ?? null
  } catch {
    return null
  }
}

/** Run the full ladder against already-decoded pixels. Exported so tests can skip the DOM. */
export function decodeFromImageData(image: ImageData): DecodeResult {
  let attempts = 0

  const direct = attempt(image)
  attempts++
  if (direct) return { data: direct, strategy: 'direct', attempts }

  const boosted = attempt(boostContrast(image))
  attempts++
  if (boosted) return { data: boosted, strategy: 'contrast', attempts }

  return { data: null, attempts }
}

export async function decodeQrFromFile(file: File): Promise<DecodeResult> {
  let bitmap: ImageBitmap
  try {
    // from-image applies EXIF rotation, so a photo taken in portrait is not fed in sideways.
    bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' })
  } catch {
    try {
      bitmap = await createImageBitmap(file)
    } catch {
      return { data: null, attempts: 0 }
    }
  }

  const { width: w, height: h } = bitmap
  let attempts = 0

  const run = (
    label: string,
    width: number,
    height: number,
    crop?: { sx: number; sy: number; sw: number; sh: number },
  ): DecodeResult | null => {
    const image = crop
      ? toCanvas(bitmap, width, height, crop.sx, crop.sy, crop.sw, crop.sh)
      : toCanvas(bitmap, width, height)
    if (!image) return null

    attempts++
    const direct = attempt(image)
    if (direct) return { data: direct, strategy: label, attempts }

    attempts++
    const boosted = attempt(boostContrast(image))
    if (boosted) return { data: boosted, strategy: `${label}+contrast`, attempts }

    return null
  }

  const longest = Math.max(w, h)
  const fit = (target: number) => {
    const scale = target / longest
    return { width: Math.round(w * scale), height: Math.round(h * scale) }
  }

  const ladder: (() => DecodeResult | null)[] = []

  // 1. Native size — but only when it is not enormous, because a huge frame is both slow
  //    and the least likely to succeed.
  if (longest <= MAX_DIMENSION) {
    ladder.push(() => run('native', w, h))
  }

  // 2. Progressive downscales. Most phone photos decode at one of these.
  for (const target of [1600, 1000, 640, 400]) {
    if (longest > target) {
      const { width, height } = fit(target)
      ladder.push(() => run(`scale-${target}`, width, height))
    }
  }

  // 3. Upscale a small image — a screenshotted QR can fall under the minimum module size.
  if (longest < 500) {
    ladder.push(() => run('upscale-2x', w * 2, h * 2))
    ladder.push(() => run('upscale-4x', w * 4, h * 4))
  }

  // 4. Centre crops, for a code that occupies a small part of a wider photo.
  for (const portion of [0.7, 0.5]) {
    const sw = w * portion
    const sh = h * portion
    const sx = (w - sw) / 2
    const sy = (h - sh) / 2
    const target = Math.min(1000, Math.max(sw, sh))
    const scale = target / Math.max(sw, sh)
    ladder.push(() =>
      run(`crop-${portion}`, sw * scale, sh * scale, { sx, sy, sw, sh }),
    )
  }

  for (const step of ladder) {
    const result = step()
    if (result?.data) {
      bitmap.close?.()
      return result
    }
  }

  bitmap.close?.()
  return { data: null, attempts }
}
