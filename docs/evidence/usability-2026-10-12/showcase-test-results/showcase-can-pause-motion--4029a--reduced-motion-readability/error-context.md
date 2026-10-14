# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: showcase.spec.ts >> can pause motion while retaining case interactions and reduced-motion readability
- Location: e2e\showcase.spec.ts:30:1

# Error details

```
Error: expect(locator).toBeDisabled() failed

Locator: getByRole('button', { name: '已遵循系统减少动画', exact: true })
Expected: disabled
Timeout: 20000ms
Error: element(s) not found

Call log:
  - Expect "toBeDisabled" getByRole('button', { name: '已遵循系统减少动画', exact: true }) with timeout 20000ms
  - waiting for getByRole('button', { name: '已遵循系统减少动画', exact: true })

```

```yaml
- link "跳到产品内容":
  - /url: "#product-content"
- banner:
  - link "PawTwin 产品首页":
    - /url: "#product"
    - text: PawTwin
  - navigation "产品导航":
    - link "产品体验":
      - /url: "#features"
    - link "如何使用":
      - /url: "#care"
    - link "日常案例":
      - /url: "#cases"
    - link "进入应用":
      - /url: "#app"
- button "开启动画" [disabled] [pressed]
- main:
  - paragraph: PawTwin · 一起，好好照顾。
  - heading "它的每一天， 值得被好好记住。" [level=1]
  - paragraph: 一个属于它的小屋。 让全家的照顾、成长的瞬间，和一点点了解，在这里相遇。
  - link "进入应用":
    - /url: "#app"
  - link "了解产品":
    - /url: "#features"
  - text: PawTwin Mochi 的小屋
  - complementary:
    - strong: Mochi
    - text: 属于它的小小世界 ⌂ 小屋 ♡ 照护 ✦ 分身 ↗ 成长
  - img "俯视的宠物小屋，中央是正面造型的橘猫": 陪伴的角落 照护区
  - text: 每一个小日常，都值得留下。 产品界面示意
  - paragraph: PawTwin
  - heading "小小的它。 独一无二的日常。" [level=3]
  - text: 档案与偏好 ⌂ 一起照顾 ♡ 成长故事 ↗ 产品界面示意
  - paragraph: 本地体验已开放 从猫和狗的日常照护开始
  - region "小小一间屋。 装下大大的陪伴。":
    - paragraph: 它的世界，从这里开始。
    - heading "小小一间屋。 装下大大的陪伴。" [level=2]
    - paragraph: 喜欢的玩具，熟悉的窝，今天的小故事。 把关于它的点点滴滴，放回属于它的地方。
    - text: 它的习惯 你的记录 全家的关心
    - paragraph: 像素宠物形象示意 · 可在应用中建立自己的宠物档案
  - paragraph: 彼此连接的四种体验。
  - heading "从一只宠物，到一个家。" [level=2]
  - paragraph: 让记录有归处，让照护有回应。
  - group "查看产品体验":
    - button "宠物小屋" [pressed]
    - button "家庭照护"
    - button "成长记录"
    - button "宠物分身"
  - text: PawTwin Mochi 的小屋
  - complementary:
    - strong: Mochi
    - text: ⌂ 小屋 ♡ 照护 ✦ 分身 ↗ 成长
  - img "俯视的宠物小屋，中央是正面造型的橘猫": 陪伴的角落 照护区
  - text: 每一个小日常，都值得留下。 产品界面示意
  - paragraph: 每只宠物都有自己的记录与偏好
  - text: 产品界面示意 · 功能以应用内实际状态为准 01 / 宠物小屋
  - heading "给每个小家伙，一个自己的家。" [level=3]
  - paragraph: 一张档案，一间小屋。把它喜欢的玩具、常睡的窝和你确认的偏好放在一起，让照护从了解它开始。
  - text: ✓独立宠物档案 ✓像素小屋 ✓照片日记
  - link "在应用中体验":
    - /url: "#app"
  - region "把功能，放进日常。":
    - paragraph: 三个场景，一起看看。
    - heading "把功能，放进日常。" [level=2]
    - paragraph: 不是功能清单，是你和它的一天。
    - group "选择日常案例":
      - button "家庭交接" [pressed]
      - button "成长回顾"
      - button "偏好接续"
    - text: 情景示意 步骤 1 / 3
    - heading "换一碗新鲜的水" [level=3]
    - text: 待领取
    - paragraph: 主人创建一项人工照护事项，等待家人接手。
    - text: 虚构情景演示 · 不会创建真实照护任务 案例 01 / 家庭交接
    - heading "你出门了，照顾还在继续。" [level=3]
    - paragraph: 出门前为 Mochi 安排换水。家人接手后，在实际完成时留下记录，彼此不用反复确认。
    - group "查看案例步骤":
      - button "01 主人安排" [pressed]:
        - text: "01"
        - strong: 主人安排
      - button "02 家人接手":
        - text: "02"
        - strong: 家人接手
      - button "03 完成并回写":
        - text: "03"
        - strong: 完成并回写
    - paragraph: 主人创建一项人工照护事项，等待家人接手。
    - paragraph: 任务的每一次交接，都有清楚的去向。
    - link "在应用中开始":
      - /url: "#app"
  - paragraph: 每一份了解，都有来处。
  - heading "记住它。 也记住为什么。" [level=2]
  - paragraph: 档案、实测成长和你确认的偏好，串起它的日常。 留下来源，保留空白，让每一次回顾都有依据。
  - link "探索成长记录":
    - /url: "#features"
  - text: "01"
  - heading "实测成长" [level=3]
  - paragraph: 来自你记录的测量与时间
  - text: "02"
  - heading "确认偏好" [level=3]
  - paragraph: 由主人确认，可修改与删除
  - text: "03"
  - heading "照护记录" [level=3]
  - paragraph: 实际完成之后，才留下记录
  - text: 记录结构示意 · 非真实宠物数据
  - paragraph: 从今天的一件小事开始。
  - heading "让关心，变成有回应的日常。" [level=2]
  - paragraph: 认识它，一起安排，接手照顾，再回看成长。
  - article:
    - text: "01"
    - heading "认识它" [level=3]
    - paragraph: 创建宠物档案，记录它的习惯与偏好。
  - article:
    - text: "02"
    - heading "一起安排" [level=3]
    - paragraph: 邀请家人，安排需要完成的照护事项。
  - article:
    - text: "03"
    - heading "接手照顾" [level=3]
    - paragraph: 领取任务，在实际完成后留下记录。
  - article:
    - text: "04"
    - heading "回看成长" [level=3]
    - paragraph: 在日记与报告里，看见点滴变化。
  - paragraph: PawTwin
  - heading "一起照顾。 也一起记得。" [level=2]
  - paragraph: 为它，也为每一个关心它的人。
  - link "建立我的宠物小屋":
    - /url: "#app"
- contentinfo:
  - link "PawTwin":
    - /url: "#product"
  - text: 给日常一点记忆，给陪伴更多了解。
  - link "照护工作台":
    - /url: "#workbench"
  - paragraph: 家庭身份与记录仍为本地服务；实际回答后端与依据见每轮回复，Alexa 为网页模拟。PawLink 项圈为概念，设备执行为模拟，云端能力尚未验证。
  - paragraph:
    - text: PawTwin · 每只宠物，各有不同。
    - link "进入家庭应用":
      - /url: "#app"
```

# Test source

```ts
  1   | import { expect, test } from '@playwright/test'
  2   | 
  3   | const headline = /它的每一天，\s*值得被好好记住。/
  4   | 
  5   | test('explores illustrative care cases without writing business data', async ({ page }) => {
  6   |   const requests: string[] = []
  7   |   page.on('request', request => { if (new URL(request.url()).pathname.startsWith('/api/')) requests.push(request.url()) })
  8   |   for (const width of [320, 390, 1440]) {
  9   |     await page.setViewportSize({ width, height: 900 })
  10  |     await page.goto('/#cases')
  11  |     const cases = page.getByRole('region', { name: '把功能，放进日常。' })
  12  |     await expect(cases).toBeVisible({ timeout: 5000 })
  13  |     await expect(cases.getByText('虚构情景演示 · 不会创建真实照护任务')).toBeVisible()
  14  |     for (const [label, title] of [['家庭交接', '你出门了，照顾还在继续。'], ['成长回顾', '一次次记录，看见成长的轨迹。'], ['偏好接续', '下一次交流，从已有了解开始。']]) {
  15  |       await cases.getByRole('button', { name: label, exact: true }).click()
  16  |       await expect(cases.getByRole('heading', { name: title })).toBeVisible()
  17  |       const steps = cases.getByRole('group', { name: '查看案例步骤' }).getByRole('button')
  18  |       await expect(steps.nth(0)).toHaveAttribute('aria-pressed', 'true')
  19  |       await steps.nth(2).focus()
  20  |       await page.keyboard.press('Enter')
  21  |       await expect(steps.nth(2)).toHaveAttribute('aria-pressed', 'true')
  22  |       await expect(cases.getByLabel('案例画面')).toContainText('步骤 3 / 3')
  23  |       await steps.nth(0).click()
  24  |       expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  25  |     }
  26  |   }
  27  |   expect(requests).toEqual([])
  28  | })
  29  | 
  30  | test('can pause motion while retaining case interactions and reduced-motion readability', async ({ page }) => {
  31  |   await page.goto('/')
  32  |   await page.getByRole('button', { name: '暂停动画', exact: true }).click({ timeout: 5000 })
  33  |   await expect(page.locator('.showcase')).toHaveAttribute('data-motion', 'paused')
  34  |   await page.locator('.pt-world-cat').scrollIntoViewIfNeeded()
  35  |   expect(await page.locator('.pt-world-cat').evaluate(element => getComputedStyle(element).animationName)).toBe('none')
  36  |   await page.getByRole('link', { name: '日常案例', exact: true }).click()
  37  |   await page.getByRole('button', { name: '成长回顾', exact: true }).click()
  38  |   await expect(page.getByRole('heading', { name: '一次次记录，看见成长的轨迹。' })).toBeVisible()
  39  |   await page.emulateMedia({ reducedMotion: 'reduce' })
  40  |   await page.reload()
  41  |   await expect(page.getByRole('heading', { name: '把功能，放进日常。' })).toBeVisible()
  42  |   expect(await page.locator('.pt-world-cat').evaluate(element => getComputedStyle(element).animationName)).toBe('none')
> 43  |   await expect(page.getByRole('button', { name: '已遵循系统减少动画', exact: true })).toBeDisabled()
      |                                                                              ^ Error: expect(locator).toBeDisabled() failed
  44  | })
  45  | 
  46  | test('introduces the product without requesting private business data, then opens the app', async ({ page }) => {
  47  |   const businessRequests: string[] = []
  48  |   page.on('request', (request) => {
  49  |     if (new URL(request.url()).pathname.startsWith('/api/')) businessRequests.push(request.url())
  50  |   })
  51  |   await page.goto('/')
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
```