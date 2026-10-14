# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: showcase.spec.ts >> routes real access management and visit-card export from their demonstration
- Location: e2e\showcase.spec.ts:205:1

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('region', { name: '把了解它的记录，带到下一次照护。' })
Expected: visible
Timeout: 3000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByRole('region', { name: '把了解它的记录，带到下一次照护。' }) with timeout 3000ms
  - waiting for getByRole('region', { name: '把了解它的记录，带到下一次照护。' })

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
- button "暂停动画"
- main:
  - paragraph: PawTwin · 一起，好好照顾。
  - heading "它的每一天， 值得被好好记住。" [level=1]
  - paragraph: 一个属于它的小屋。 让全家的照顾、成长的瞬间，和一点点了解，在这里相遇。
  - link "进入应用":
    - /url: "#app"
  - link "了解产品":
    - /url: "#features"
  - paragraph:
    - link "体验 Alexa+ 网页模拟":
      - /url: "#alexa"
    - text: 文字模拟 · 与 App 共用记录
  - text: PawTwin Mochi 的小屋
  - complementary:
    - strong: Mochi
    - text: 属于它的小小世界 ⌂ 小屋 ♡ 照护 ✦ 分身 ↗ 成长
  - img "俯视的宠物小屋，中央是正面造型的橘猫": 陪伴的角落 照护区
  - text: 每一个小日常，都值得留下。 产品界面示意 今日概览 结构示意
  - strong: 今日照护
  - text: 逾期与今日待办
  - strong: 成长回顾
  - text: 实测与记录来源
  - strong: 家庭接力
  - text: 领取后完成记录
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
  - text: 每一个小日常，都值得留下。 产品界面示意 今日概览 结构示意
  - strong: 今日照护
  - text: 逾期与今日待办
  - strong: 成长回顾
  - text: 实测与记录来源
  - strong: 家庭接力
  - text: 领取后完成记录
  - paragraph: 每只宠物都有自己的记录与偏好
  - text: 产品界面示意 · 功能以应用内实际状态为准 01 / 宠物小屋
  - heading "给每个小家伙，一个自己的家。" [level=3]
  - paragraph: 从今日概览看待办、照护进度和成长记录，再回到它的小屋。档案、玩具、熟悉的窝和你确认的偏好，让照护从了解它开始。
  - text: ✓今日概览 ✓独立宠物档案 ✓像素小屋
  - link "在应用中体验":
    - /url: "#app/home"
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
      - /url: "#app/care"
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
    - /url: "#app/home"
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
  152 |     await expect(page).toHaveURL(new RegExp(`${route}$`), { timeout: 3000 })
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
  171 | test('explores handoff and visit demonstrations without business requests at all supported widths', async ({ page }) => {
  172 |   const requests: string[] = [], errors: string[] = []
  173 |   page.on('request', request => { if (new URL(request.url()).pathname.startsWith('/api/')) requests.push(request.url()) })
  174 |   page.on('pageerror', error => errors.push(error.message))
  175 |   for (const width of [320, 390, 1440]) {
  176 |     await page.setViewportSize({ width, height: 900 })
  177 |     await page.goto('/#vision')
  178 |     const vision = page.getByRole('region', { name: '把了解它的记录，带到下一次照护。' })
  179 |     await expect(vision).toBeVisible({ timeout: 3000 })
  180 |     const announcer = await vision.locator('.pt-vision-live').elementHandle()
  181 |     for (const [label, titles] of [
  182 |       ['照护交接', ['照护需求', '临时只读分身卡', '照护反馈示意', '主人核对']],
  183 |       ['就诊准备', ['已有记录概览', '缺项与来源', '就诊信息卡（诊断资料）']],
  184 |     ] as const) {
  185 |       await vision.getByRole('button', { name: label, exact: true }).click()
  186 |       const steps = vision.getByRole('group', { name: '查看交接与就诊演示步骤' }).getByRole('button')
  187 |       await expect(steps.nth(0)).toHaveAttribute('aria-pressed', 'true')
  188 |       for (let index = 0; index < titles.length; index++) {
  189 |         await steps.nth(index).focus()
  190 |         await page.keyboard.press('Enter')
  191 |         await expect(steps.nth(index)).toHaveAttribute('aria-pressed', 'true')
  192 |         await expect(vision.getByRole('heading', { name: titles[index], exact: true })).toBeVisible()
  193 |         await expect(vision.getByLabel('交接与就诊功能界面示意')).toContainText(`步骤 ${index + 1} / ${titles.length}`)
  194 |         expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  195 |       }
  196 |       expect(await announcer!.evaluate(element => element.isConnected)).toBe(true)
  197 |     }
  198 |     await vision.getByRole('button', { name: '照护交接', exact: true }).click()
  199 |     await expect(vision.getByRole('group', { name: '查看交接与就诊演示步骤' }).getByRole('button').first()).toHaveAttribute('aria-pressed', 'true')
  200 |   }
  201 |   expect(requests).toEqual([])
  202 |   expect(errors).toEqual([])
  203 | })
  204 | 
  205 | test('routes real access management and visit-card export from their demonstration', async ({ page }) => {
  206 |   for (const [scenario, shortcut, route] of [
  207 |     ['照护交接', '在应用中管理临时访问', '#app/family'],
  208 |     ['就诊准备', '导出就诊信息卡（诊断资料）', '#app/growth'],
  209 |   ]) {
  210 |     await page.goto('/#vision')
  211 |     const vision = page.getByRole('region', { name: '把了解它的记录，带到下一次照护。' })
> 212 |     await expect(vision).toBeVisible({ timeout: 3000 })
      |                          ^ Error: expect(locator).toBeVisible() failed
  213 |     await vision.getByRole('button', { name: scenario, exact: true }).click()
  214 |     await vision.getByRole('link', { name: shortcut, exact: true }).focus()
  215 |     await page.keyboard.press('Enter')
  216 |     await expect(page).toHaveURL(new RegExp(`${route}$`))
  217 |     await expect(page.getByRole('button', { name: '登录账号', exact: true })).toBeVisible()
  218 |   }
  219 | })
  220 | 
  221 | test('keeps new demonstration steps usable while motion is paused or reduced', async ({ page }) => {
  222 |   await page.goto('/#vision')
  223 |   const vision = page.getByRole('region', { name: '把了解它的记录，带到下一次照护。' })
  224 |   await expect(vision).toBeVisible({ timeout: 3000 })
  225 |   await page.getByRole('button', { name: '暂停动画', exact: true }).click()
  226 |   await vision.getByRole('button', { name: '授权分身卡', exact: true }).click()
  227 |   await expect(vision.getByRole('heading', { name: '临时只读分身卡', exact: true })).toBeVisible()
  228 |   expect(await vision.locator('.pt-vision-card').evaluate(element => getComputedStyle(element).animationName)).toBe('none')
  229 |   await page.emulateMedia({ reducedMotion: 'reduce' })
  230 |   await vision.getByRole('button', { name: '就诊准备', exact: true }).click()
  231 |   await vision.getByRole('button', { name: '预览就诊卡', exact: true }).click()
  232 |   await expect(vision.getByRole('heading', { name: '就诊信息卡（诊断资料）', exact: true })).toBeVisible()
  233 |   expect(await vision.locator('.pt-vision-card').evaluate(element => getComputedStyle(element).animationName)).toBe('none')
  234 |   await expect(page.getByRole('button', { name: '已遵循系统减少动画', exact: true })).toBeDisabled()
  235 | })
  236 | 
```