import '@testing-library/jest-dom/vitest'

/**
 * jsdom ships no canvas implementation, so `ImageData` is undefined. The pure pixel functions
 * in `lib/decodeQr` only read `data`, `width` and `height`, so a structural stand-in is enough
 * to test them without pulling in the native `canvas` package (which needs a compiler toolchain
 * on Windows). Anything that genuinely needs a canvas is verified in the browser instead.
 */
if (typeof globalThis.ImageData === 'undefined') {
  class ImageDataPolyfill {
    readonly data: Uint8ClampedArray
    readonly width: number
    readonly height: number
    readonly colorSpace = 'srgb' as const

    constructor(data: Uint8ClampedArray | number, widthOrHeight: number, height?: number) {
      if (typeof data === 'number') {
        // new ImageData(width, height)
        this.width = data
        this.height = widthOrHeight
        this.data = new Uint8ClampedArray(this.width * this.height * 4)
      } else {
        this.data = data
        this.width = widthOrHeight
        this.height = height ?? data.length / 4 / widthOrHeight
      }
    }
  }

  globalThis.ImageData = ImageDataPolyfill as unknown as typeof ImageData
}
