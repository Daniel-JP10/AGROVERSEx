// asistido por SI: Claude Code (Anthropic), presupuesto de la entrada (plan v2 §2): LCP con red lenta y bytes transferidos, sin MapLibre
import { expect, test } from '@playwright/test'

// Red lenta de la línea base de v1 §a: 9 Mbit/s y 150 ms de latencia (CDP: solo Chromium)
test('entrada: LCP ≤ 2,5 s con red lenta, ≤ 600 KB transferidos y sin MapLibre', async ({ page, browserName }) => {
  test.skip(browserName !== 'chromium', 'la limitación de red y el LCP se miden con CDP de Chromium')
  const cdp = await page.context().newCDPSession(page)
  await cdp.send('Network.enable')
  await cdp.send('Network.emulateNetworkConditions', { offline: false, latency: 150, downloadThroughput: 9e6 / 8, uploadThroughput: 9e6 / 8 })
  let bytes = 0
  const urls: string[] = []
  cdp.on('Network.loadingFinished', (e) => { bytes += e.encodedDataLength })
  cdp.on('Network.requestWillBeSent', (e) => { urls.push(e.request.url) })
  await page.goto('/', { waitUntil: 'networkidle' })
  const lcp = await page.evaluate(() => new Promise<number>((ok) => {
    new PerformanceObserver((l) => { const e = l.getEntries(); ok(e[e.length - 1].startTime) }).observe({ type: 'largest-contentful-paint', buffered: true })
  }))
  console.log(`LCP ${Math.round(lcp)} ms, ${Math.round(bytes / 1024)} KB, ${urls.length} pedidos`)
  expect(urls.filter((u) => /maplibre|Tierra-/i.test(u))).toEqual([])
  expect(lcp).toBeLessThanOrEqual(2500)
  expect(bytes).toBeLessThanOrEqual(600 * 1024)
})
