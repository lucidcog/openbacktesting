import { chromium } from '@playwright/test'
const browser = await chromium.launch({ headless: true })
await browser.close()
console.log('Isolated bundled Chromium is available')
