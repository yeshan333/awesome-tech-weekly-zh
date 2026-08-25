#!/usr/bin/env node
/**
 * 生成后自检:在真实浏览器里验证 site/index.html 的滚动 / 筛选 / 滑动等交互。
 *
 * 用法:  node scripts/verify_site.mjs [--dir site]
 * 退出码:0 = 全部通过;1 = 有失败项(失败清单打印在 stdout,勿部署)。
 *
 * 页面必须带 data-test 钩子(见 ai_agents_configs/paseo/prompts/weekly-site.md 步骤 5),
 * 缺钩子直接判 FAIL —— 自检不做「猜选择器」的启发式匹配。
 */
import { createServer } from 'node:http'
import { readFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import { extname, join, resolve } from 'node:path'
import { execSync } from 'node:child_process'

const require = createRequire(import.meta.url)

function loadPlaywright() {
  const candidates = ['playwright']
  try {
    const root = execSync('npm root -g', { encoding: 'utf8' }).trim()
    candidates.push(join(root, '@playwright/cli/node_modules/playwright'))
    candidates.push(join(root, 'playwright'))
  } catch {}
  for (const c of candidates) {
    try { return require(c) } catch {}
  }
  throw new Error('找不到 playwright。装一个:npm i -g @playwright/cli')
}

const MIME = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.ico': 'image/x-icon' }

function serve(dir) {
  const server = createServer(async (req, res) => {
    const rel = decodeURIComponent(req.url.split('?')[0])
    const file = resolve(dir, '.' + (rel === '/' ? '/index.html' : rel))
    if (!file.startsWith(resolve(dir))) { res.writeHead(403).end(); return }
    try {
      const body = await readFile(file)
      res.writeHead(200, { 'content-type': MIME[extname(file)] ?? 'application/octet-stream' }).end(body)
    } catch {
      res.writeHead(404).end('not found')
    }
  })
  return new Promise(r => server.listen(0, '127.0.0.1', () => r({ server, port: server.address().port })))
}

const results = []
const check = (name, ok, detail = '') => { results.push({ name, ok: !!ok, detail }); console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? `  — ${detail}` : ''}`) }
/** 一组检查抛异常(点不动、元素被遮挡、超时)时记为 FAIL 继续跑,不让整轮自检崩掉。 */
const guard = async (label, fn) => { try { await fn() } catch (e) { check(`${label} 执行中断`, false, String(e.message ?? e).split('\n')[0]) } }
const sel = k => `[data-test="${k}"]`
const sleep = ms => new Promise(r => setTimeout(r, ms))

const activeIndex = page => page.$$eval(sel('featured-card'), els => els.findIndex(e => e.dataset.active === 'true'))
const visibleCards = page => page.$$eval(sel('feed-card'), els => els.filter(e => e.offsetParent !== null).length)

/** 用 CDP 发真实触摸事件 —— Playwright 的 touchscreen 只有 tap,做不了滑动。 */
async function drag(page, x0, y0, dx, dy, steps = 10) {
  const cdp = await page.context().newCDPSession(page)
  const pt = (x, y) => ({ x, y, radiusX: 8, radiusY: 8, force: 1, id: 1 })
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [pt(x0, y0)] })
  for (let i = 1; i <= steps; i++) {
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [pt(x0 + (dx * i) / steps, y0 + (dy * i) / steps)] })
    await sleep(16)
  }
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] })
  await cdp.detach()
  await sleep(700)
}
/** 横向滑动(切轮播)。 */
const swipe = (page, box, dx) => drag(page, box.x + box.width / 2, box.y + box.height / 2, dx, 0, 6)
/** 纵向滑动(滚页面),driftX 模拟真实手指的横向漂移。 */
const dragY = (page, x, y, dy, driftX = 0) => drag(page, x, y, driftX, dy, 12)

async function checkHooks(page) {
  const need = ['hero', 'featured', 'featured-card', 'nav', 'nav-item', 'feed-card', 'back-to-top', 'theme-toggle']
  const counts = await page.evaluate(ks => Object.fromEntries(ks.map(k => [k, document.querySelectorAll(`[data-test="${k}"]`).length])), need)
  const missing = need.filter(k => counts[k] === 0)
  check('data-test 钩子齐全', missing.length === 0, missing.length ? `缺少:${missing.join(', ')}` : JSON.stringify(counts))
  return missing.length === 0
}

async function checkFirstScreen(page) {
  const heroH = await page.$eval(sel('hero'), e => e.getBoundingClientRect().height).catch(() => -1)
  check('hero 不独占首屏(< 视口 65%)', heroH > 0 && heroH < 900 * 0.65, `hero 高 ${Math.round(heroH)}px`)
  const cardTop = await page.$eval(sel('featured-card'), e => e.getBoundingClientRect().top).catch(() => 1e9)
  check('首屏可见精选卡片', cardTop < 900, `首卡 top=${Math.round(cardTop)}px`)
}

async function checkScroll(page, label, { touch = false } = {}) {
  const scrollable = await page.evaluate(() => document.documentElement.scrollHeight > innerHeight + 200)
  check(`${label} 页面可上下滚动`, scrollable)

  /* 真实输入滚动。programmatic scrollTo 永远能滚,测不出「手势/滚轮被 preventDefault 吃掉」
     或 touch-action 设错 —— 而首屏最容易挡住手势的正是轮播区,所以特意在它上面试。 */
  const stage = await page.$(sel('featured'))
  if (stage) {
    const b = await stage.boundingBox()
    const cx = b.x + b.width / 2, cy = b.y + b.height / 2
    for (const drift of touch ? [0, 25] : [0]) {
      await page.evaluate(() => scrollTo(0, 0)); await sleep(450)
      if (touch) await dragY(page, cx, cy, -300, drift)
      else { await page.mouse.move(cx, cy); await page.mouse.wheel(0, 500); await sleep(600) }
      const y = await page.evaluate(() => Math.round(scrollY))
      const how = touch ? `触摸纵滑(横向漂移 ${drift}px)` : '鼠标滚轮'
      check(`${label} 轮播区上${how}能滚动页面`, y > 80, `scrollY=${y}`)
    }
  }

  await page.evaluate(() => scrollTo(0, 1500))
  await sleep(400)
  const nav = await page.$eval(sel('nav'), e => {
    const r = e.getBoundingClientRect()
    return { top: r.top, h: r.height, sticky: ['sticky', 'fixed'].includes(getComputedStyle(e).position) }
  })
  check(`${label} 分类导航滚动后吸顶可见`, nav.sticky && nav.top <= 4 && nav.h > 0, `position sticky/fixed=${nav.sticky}, top=${Math.round(nav.top)}`)

  const btn = await page.$(sel('back-to-top'))
  check(`${label} 回到顶部按钮滚动后出现`, await btn.isVisible())
  const size = await btn.boundingBox()
  check(`${label} 回到顶部按钮 ≥44px`, size.width >= 40 && size.height >= 40, `${Math.round(size.width)}x${Math.round(size.height)}`)
  await btn.click()
  await sleep(900)
  check(`${label} 点击后回到页顶`, (await page.evaluate(() => scrollY)) < 60)

  await page.evaluate(() => scrollTo(0, 0))
  await sleep(300)
  const hiddenAtTop = await page.$eval(sel('back-to-top'), e => {
    const s = getComputedStyle(e)
    return s.display === 'none' || s.visibility === 'hidden' || parseFloat(s.opacity) < 0.1
  })
  check(`${label} 回到顶部按钮在页顶隐藏`, hiddenAtTop)
}

async function checkFilter(page) {
  await page.evaluate(() => scrollTo(0, 0))
  const total = await visibleCards(page)
  const cats = await page.$$eval(sel('nav-item'), els => els.map(e => e.dataset.category ?? ''))
  check('导航含「全部」项', cats.includes('all'), `分类:${cats.join('|')}`)
  const target = cats.find(c => c && c !== 'all')
  if (!target) return check('分类筛选生效', false, '没有可点的非「全部」分类')

  await page.click(`${sel('nav-item')}[data-category="${target.replace(/"/g, '\\"')}"]`)
  await sleep(500)
  const filtered = await visibleCards(page)
  check('点击分类只显示该类卡片', filtered > 0 && filtered < total, `${total} → ${filtered}(分类 ${target})`)
  const highlighted = await page.$$eval(sel('nav-item'), els => els.filter(e => e.dataset.active === 'true' || e.getAttribute('aria-current')).length)
  check('当前分类高亮', highlighted === 1, `高亮项 ${highlighted} 个`)

  await page.click(`${sel('nav-item')}[data-category="all"]`)
  await sleep(500)
  check('点「全部」恢复所有卡片', (await visibleCards(page)) === total, `恢复到 ${await visibleCards(page)}/${total}`)
}

async function checkCarousel(page, label, { touch = false } = {}) {
  const n = (await page.$$(sel('featured-card'))).length
  if (n < 2) return check(`${label} 轮播卡片 ≥2 张`, false, `只有 ${n} 张`)
  const start = await activeIndex(page)
  check(`${label} 轮播有当前卡(data-active)`, start >= 0, `active index=${start}`)

  const next = await page.$(sel('carousel-next'))
  if (next) {
    await guard(`${label} 右箭头`, async () => {
      await next.click(); await sleep(700)
      check(`${label} 右箭头切换卡片`, (await activeIndex(page)) !== start, `${start} → ${await activeIndex(page)}`)
    })
  } else check(`${label} 提供左右箭头按钮`, false, '缺 carousel-next')

  const dots = await page.$$(sel('carousel-dot'))
  if (dots.length >= 2) {
    await guard(`${label} 圆点`, async () => {
      const before = await activeIndex(page)
      await dots[(before + 2) % dots.length].click(); await sleep(700)
      check(`${label} 圆点指示器可跳转`, (await activeIndex(page)) !== before)
    })
  } else check(`${label} 提供圆点指示器`, false, `dots=${dots.length}`)

  const box = await page.$eval(sel('featured'), e => { const r = e.getBoundingClientRect(); return { x: r.x, y: r.y, width: r.width, height: r.height } })
  const before = await activeIndex(page)
  if (touch) {
    await swipe(page, box, -Math.min(200, box.width * 0.4))
    await sleep(800)
    check(`${label} 触摸滑动切换卡片`, (await activeIndex(page)) !== before, `${before} → ${await activeIndex(page)}`)
  } else {
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2)
    await page.mouse.down()
    for (let i = 1; i <= 6; i++) { await page.mouse.move(box.x + box.width / 2 - (180 * i) / 6, box.y + box.height / 2); await sleep(16) }
    await page.mouse.up()
    await sleep(800)
    check(`${label} 鼠标拖拽切换卡片`, (await activeIndex(page)) !== before, `${before} → ${await activeIndex(page)}`)
  }

  if (!touch) {
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2)
    const held = await activeIndex(page)
    await sleep(6500)
    check('鼠标悬停时自动轮播暂停', (await activeIndex(page)) === held, `hover 6.5s 后 active=${await activeIndex(page)}`)
  }
}

async function checkMisc(page, label) {
  /* 注意:不能只看 `scrollWidth - innerWidth`。移动端若有元素横向溢出,Chrome 会把
     布局视口撑宽(innerWidth 跟着变大),两个数一起变大、差值仍是 0,整页却被缩放显示。
     所以必须拿 innerWidth 和 visualViewport.width 对比,并逐元素找越界者。 */
  const of = await page.evaluate(() => {
    const vw = visualViewport ? visualViewport.width : innerWidth
    const offenders = []
    document.querySelectorAll('*').forEach(e => {
      for (let a = e.parentElement; a; a = a.parentElement) {
        if (['hidden', 'auto', 'scroll', 'clip'].includes(getComputedStyle(a).overflowX)) return // 被祖先裁掉,不算
      }
      const r = e.getBoundingClientRect()
      if (r.width > 0 && (r.right > vw + 1 || r.left < -1)) offenders.push(`${e.tagName}.${String(e.className).slice(0, 22)}`)
    })
    return { vw, innerW: innerWidth, docSW: document.documentElement.scrollWidth, list: [...new Set(offenders)].slice(0, 5), n: offenders.length }
  })
  check(`${label} 布局视口未被撑宽`, Math.abs(of.innerW - of.vw) <= 1, `innerWidth=${of.innerW} visualViewport=${of.vw}${of.innerW > of.vw + 1 ? ' —— 整页会被缩放显示' : ''}`)
  check(`${label} 无横向溢出`, of.docSW - of.innerW <= 1, `scrollWidth - innerWidth = ${of.docSW - of.innerW}`)
  check(`${label} 无元素横向越界`, of.n === 0, of.n ? `${of.n} 个,例如 ${of.list.join(', ')}` : '')

  const cardClickable = await page.$eval(sel('feed-card'), e => e.tagName === 'A' || !!e.closest('a') || !!e.querySelector('a[data-test="feed-card-link"]'))
  check(`${label} 周刊卡片整卡可点`, cardClickable)

  const toggle = await page.$(sel('theme-toggle'))
  const themeBefore = await page.evaluate(() => document.documentElement.className + document.documentElement.dataset.theme)
  await toggle.click(); await sleep(500)
  const themeAfter = await page.evaluate(() => document.documentElement.className + document.documentElement.dataset.theme)
  check(`${label} 明暗切换按钮生效`, themeBefore !== themeAfter)
  check(`${label} 主题写入 localStorage`, await page.evaluate(() => Object.keys(localStorage).length > 0))
  await toggle.click(); await sleep(300)
}

async function main() {
  const args = process.argv.slice(2)
  const dir = resolve(args.includes('--dir') ? args[args.indexOf('--dir') + 1] : 'site')
  const { server, port } = await serve(dir)
  const url = `http://127.0.0.1:${port}/index.html`
  const { chromium } = loadPlaywright()
  const browser = await chromium.launch()
  const errors = []

  try {
    const desktop = await browser.newContext({ viewport: { width: 1440, height: 900 } })
    const page = await desktop.newPage()
    page.setDefaultTimeout(8000)
    page.on('pageerror', e => errors.push(String(e)))
    page.on('console', m => { if (m.type() === 'error') errors.push(m.text()) })
    await page.goto(url, { waitUntil: 'load' })
    await sleep(800)

    if (await checkHooks(page)) {
      await guard('桌面 首屏', () => checkFirstScreen(page))
      await guard('桌面 轮播', () => checkCarousel(page, '桌面'))
      await guard('桌面 筛选', () => checkFilter(page))
      await guard('桌面 滚动', () => checkScroll(page, '桌面'))
      await guard('桌面 其它', () => checkMisc(page, '桌面'))
      await page.screenshot({ path: '/tmp/weekly-verify-desktop.png', fullPage: false })

      const mobileCtx = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true, deviceScaleFactor: 2 })
      const m = await mobileCtx.newPage()
      m.setDefaultTimeout(8000)
      m.on('pageerror', e => errors.push(String(e)))
      await m.goto(url, { waitUntil: 'load' })
      await sleep(800)
      await guard('移动端 轮播', () => checkCarousel(m, '移动端', { touch: true }))
      await guard('移动端 筛选', () => checkFilter(m))
      await guard('移动端 滚动', () => checkScroll(m, '移动端', { touch: true }))
      await guard('移动端 其它', () => checkMisc(m, '移动端'))
      await m.screenshot({ path: '/tmp/weekly-verify-mobile.png', fullPage: false })
    }
    check('无 JS 报错', errors.length === 0, errors.slice(0, 3).join(' | '))
  } finally {
    await browser.close()
    server.close()
  }

  const failed = results.filter(r => !r.ok)
  console.log(`\n=== ${results.length - failed.length}/${results.length} 通过 · 截图 /tmp/weekly-verify-{desktop,mobile}.png ===`)
  if (failed.length) {
    console.log('未通过:\n' + failed.map(f => `  - ${f.name}${f.detail ? ` (${f.detail})` : ''}`).join('\n'))
    process.exit(1)
  }
}

main().catch(e => { console.error('自检脚本自身出错:', e); process.exit(2) })
