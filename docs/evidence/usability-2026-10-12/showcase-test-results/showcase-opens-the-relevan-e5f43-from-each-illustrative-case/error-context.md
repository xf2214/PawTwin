# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: showcase.spec.ts >> opens the relevant application feature from each illustrative case
- Location: e2e\showcase.spec.ts:142:1

# Error details

```
Error: expect(page).toHaveURL(expected) failed

Expected pattern: /#app\/care$/
Received string:  "http://127.0.0.1:8823/#app"
Timeout: 3000ms

Call log:
  - Expect "toHaveURL" with timeout 3000ms
    10 × locator resolved to <html lang="zh-CN">…</html>
       - unexpected value "http://127.0.0.1:8823/#app"

```

```yaml
- banner:
  - link "PawTwin 产品首页":
    - /url: "#product"
    - text: PawTwin 家庭应用
  - navigation "页面导航":
    - link "产品介绍":
      - /url: "#product"
    - link "Alexa+ 模拟器":
      - /url: "#alexa"
    - link "原工作台":
      - /url: "#workbench"
- main:
  - paragraph: PAWTWIN · HOME TOGETHER
  - heading "欢迎回到你们的小屋。" [level=1]
  - paragraph: 登录后查看宠物近况、接手照护，或记下今天的新变化。
  - heading "独立账号登录" [level=2]
  - text: 账号名
  - textbox "账号名"
  - text: 密码
  - textbox "密码"
  - button "登录账号"
  - button "创建本地账号"
  - paragraph: 本地独立账号 · 云认证未接通
  - link "原工作台 / 演示登录":
    - /url: "#workbench"
```

# Test source

```ts
  52  |   await expect(page.getByRole('heading', { name: headline })).toBeVisible({ timeout: 5000 })
  53  |   await expect(page.getByLabel('产品界面示意')).toBeVisible()
  54  |   await expect(page.getByLabel('演示口令')).toHaveCount(0)
  55  |   expect(businessRequests).toEqual([])
  56  |   await page.screenshot({ path: 'test-results/showcase-desktop.png', fullPage: true, animations: 'disabled' })
  57  | 
  58  |   await page.getByRole('link', { name: '了解产品' }).click()
  59  |   await expect(page.getByRole('heading', { name: '从一只宠物，到一个家。' })).toBeInViewport()
  60  |   await page.getByRole('button', { name: '成长记录' }).click()
  61  |   await expect(page.getByRole('heading', { name: '把成长，留在时间里。' })).toBeVisible()
  62  |   expect(businessRequests).toEqual([])
  63  | 
  64  |   await page.getByRole('link', { name: '进入应用', exact: true }).first().click()
  65  |   await expect(page).toHaveURL(/#app$/)
  66  |   await expect(page.getByRole('button', { name: '登录账号', exact: true })).toBeVisible()
  67  |   await page.getByRole('link', { name: '产品介绍', exact: true }).click()
  68  |   await expect(page).toHaveURL(/#product$/)
  69  |   await expect(page.getByRole('heading', { name: headline })).toBeVisible()
  70  | })
  71  | 
  72  | test('keeps the showcase readable on mobile and the original workbench reachable', async ({ page }) => {
  73  |   await page.setViewportSize({ width: 390, height: 844 })
  74  |   await page.goto('/')
  75  |   await expect(page.getByRole('heading', { name: headline })).toBeVisible({ timeout: 5000 })
  76  |   const fits = () => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)
  77  |   expect(await fits()).toBe(true)
  78  |   await page.screenshot({ path: 'test-results/showcase-mobile.png', fullPage: true, animations: 'disabled' })
  79  |   await page.getByRole('link', { name: '照护工作台', exact: true }).click()
  80  |   await expect(page.getByLabel('演示口令')).toBeVisible()
  81  |   expect(await fits()).toBe(true)
  82  |   await page.getByRole('link', { name: '产品介绍', exact: true }).click()
  83  |   await expect(page.getByRole('heading', { name: headline })).toBeVisible()
  84  | })
  85  | 
  86  | test('supports direct product anchors and distinct preview panels at narrow widths', async ({ page }) => {
  87  |   const errors: string[] = []
  88  |   page.on('pageerror', error => errors.push(error.message))
  89  |   for (const width of [320, 390, 1440]) {
  90  |     await page.setViewportSize({ width, height: 900 })
  91  |     await page.goto('/#features')
  92  |     await expect(page.getByRole('heading', { name: '从一只宠物，到一个家。' })).toBeInViewport()
  93  |     for (const label of ['家庭照护', '成长记录', '宠物分身']) {
  94  |       await page.getByRole('button', { name: label, exact: true }).click()
  95  |       await expect(page.getByLabel(`${label}界面示意`, { exact: true })).toBeVisible()
  96  |       expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  97  |     }
  98  |   }
  99  |   await page.goto('/#care')
  100 |   await expect(page.getByRole('heading', { name: '让关心，变成有回应的日常。' })).toBeInViewport()
  101 |   expect(errors).toEqual([])
  102 | })
  103 | 
  104 | test('supports keyboard exploration, reduced motion and the growth shortcut', async ({ page }) => {
  105 |   await page.emulateMedia({ reducedMotion: 'reduce' })
  106 |   await page.goto('/')
  107 |   await page.keyboard.press('Tab')
  108 |   await expect(page.getByRole('link', { name: '跳到产品内容' })).toBeFocused()
  109 |   await page.keyboard.press('Enter')
  110 |   expect(await page.locator('.pt-hero-copy').evaluate(element => getComputedStyle(element).animationName)).toBe('none')
  111 |   await page.getByRole('link', { name: '探索成长记录' }).click()
  112 |   await expect(page.getByRole('button', { name: '成长记录', exact: true })).toHaveAttribute('aria-pressed', 'true')
  113 |   await expect(page.getByRole('heading', { name: '从一只宠物，到一个家。' })).toBeInViewport()
  114 |   const twin = page.getByRole('button', { name: '宠物分身', exact: true })
  115 |   const announcer = await page.locator('.pt-story-copy').elementHandle()
  116 |   await twin.focus()
  117 |   await page.keyboard.press('Enter')
  118 |   await expect(twin).toHaveAttribute('aria-pressed', 'true')
  119 |   await expect(page.getByLabel('宠物分身界面示意')).toContainText('实际回答后端见应用内每轮回复')
  120 |   await expect(page.locator('.pt-story-copy')).toHaveAttribute('aria-live', 'polite')
  121 |   expect(await announcer!.evaluate(element => element.isConnected)).toBe(true)
  122 | })
  123 | 
  124 | test('routes each product experience to its application feature with the keyboard', async ({ page }) => {
  125 |   for (const [label, route] of [
  126 |     ['宠物小屋', '#app/home'],
  127 |     ['家庭照护', '#app/care'],
  128 |     ['成长记录', '#app/growth'],
  129 |     ['宠物分身', '#app/assistant'],
  130 |   ]) {
  131 |     await page.goto('/#features')
  132 |     await page.getByRole('button', { name: label, exact: true }).click()
  133 |     await page.getByRole('link', { name: '在应用中体验', exact: true }).focus()
  134 |     await page.keyboard.press('Enter')
  135 |     await expect(page).toHaveURL(new RegExp(`${route}$`), { timeout: 3000 })
  136 |     await expect(page.getByRole('button', { name: '登录账号', exact: true })).toBeVisible()
  137 |     await page.getByRole('link', { name: '产品介绍', exact: true }).click()
  138 |     await expect(page.getByRole('heading', { name: headline })).toBeVisible()
  139 |   }
  140 | })
  141 | 
  142 | test('opens the relevant application feature from each illustrative case', async ({ page }) => {
  143 |   for (const [label, route] of [
  144 |     ['家庭交接', '#app/care'],
  145 |     ['成长回顾', '#app/growth'],
  146 |     ['偏好接续', '#app/assistant'],
  147 |   ]) {
  148 |     await page.goto('/#cases')
  149 |     const cases = page.getByRole('region', { name: '把功能，放进日常。' })
  150 |     await cases.getByRole('button', { name: label, exact: true }).click()
  151 |     await cases.getByRole('link', { name: '在应用中开始', exact: true }).click()
> 152 |     await expect(page).toHaveURL(new RegExp(`${route}$`), { timeout: 3000 })
      |                        ^ Error: expect(page).toHaveURL(expected) failed
  153 |     await expect(page.getByRole('button', { name: '登录账号', exact: true })).toBeVisible()
  154 |   }
  155 | })
  156 | 
  157 | test('makes the Alexa web simulation discoverable on mobile before opening it by keyboard', async ({ page }) => {
  158 |   const requests: string[] = []
  159 |   page.on('request', request => { if (new URL(request.url()).pathname.startsWith('/api/')) requests.push(request.url()) })
  160 |   await page.setViewportSize({ width: 320, height: 844 })
  161 |   await page.goto('/')
  162 |   const shortcut = page.getByRole('link', { name: '体验 Alexa+ 网页模拟', exact: true })
  163 |   await expect(shortcut).toBeVisible({ timeout: 3000 })
  164 |   await shortcut.focus()
  165 |   expect(requests).toEqual([])
  166 |   await page.keyboard.press('Enter')
  167 |   await expect(page).toHaveURL(/#alexa$/)
  168 |   await expect(page.getByRole('button', { name: '登录账号', exact: true })).toBeVisible()
  169 | })
  170 | 
```