# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: alexa.spec.ts >> Alexa simulator reads shared memory and confirms manual care exactly once
- Location: frontend\e2e\alexa.spec.ts:14:1

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.click: Test timeout of 30000ms exceeded.
Call log:
  - waiting for getByRole('button', { name: '确认记忆', exact: true })

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - banner [ref=e4]:
    - link "PawTwin 产品首页" [ref=e5] [cursor=pointer]:
      - /url: "#product"
      - text: PawTwin
      - generic [ref=e12]: 家庭应用
    - navigation "页面导航" [ref=e13]:
      - link "产品介绍" [ref=e14] [cursor=pointer]:
        - /url: "#product"
      - link "Alexa+ 模拟器" [ref=e15] [cursor=pointer]:
        - /url: "#alexa"
      - link "原工作台" [ref=e16] [cursor=pointer]:
        - /url: "#workbench"
        - text: 原工作台 ↗
  - main [ref=e17]:
    - generic [ref=e18]:
      - generic [ref=e19]:
        - paragraph [ref=e20]: PAWTWIN · HOME TOGETHER
        - heading "Alexa 体验家庭" [level=1] [ref=e21]
      - generic [ref=e22]:
        - button "模拟体验主人" [ref=e23] [cursor=pointer]
        - button "退出账号" [ref=e24] [cursor=pointer]
    - paragraph [ref=e25]: 本地独立账号 · 云认证未接通
    - generic [ref=e26]:
      - generic [ref=e27]:
        - text: 当前宠物
        - combobox "当前宠物" [ref=e28]:
          - option "Mochi" [selected]
      - generic [ref=e29]: 记录人：模拟体验主人 · 家庭成员
      - button "同步最新记录" [ref=e30] [cursor=pointer]
    - generic [ref=e31]:
      - generic [ref=e32]:
        - heading "Mochi 的个体分身" [level=2] [ref=e33]
        - paragraph [ref=e34]: 依据当前档案和主人记录回答。每轮显示实际后端；Alexa 为网页模拟。
        - link "打开 Alexa+ 模拟器" [ref=e35] [cursor=pointer]:
          - /url: "#alexa"
        - generic [ref=e36]:
          - generic [ref=e37]:
            - text: 对话入口
            - combobox "对话入口" [ref=e38]:
              - option "App 助手" [selected]
              - option "Alexa 网页模拟"
          - generic [ref=e39]:
            - text: 想了解什么
            - textbox "想了解什么" [ref=e40]: 它喜欢什么
          - button "询问分身" [ref=e41] [cursor=pointer]
        - heading "受控照护方案" [level=3] [ref=e42]
        - generic [ref=e43]:
          - generic [ref=e44]:
            - text: 方案类型
            - combobox "方案类型" [ref=e45]:
              - option "人工喂食" [selected]
              - option "换水"
              - option "陪玩"
              - option "梳毛"
              - option "洗澡"
              - option "剪指甲"
              - option "清洁"
              - option "散步"
          - generic [ref=e46]:
            - text: 方案名称
            - textbox "方案名称" [ref=e47]
          - generic [ref=e48]:
            - text: 计划时间
            - textbox "计划时间" [ref=e49]: 2026-10-12T16:21
          - button "建立待确认方案" [ref=e50] [cursor=pointer]
      - generic [ref=e51]:
        - heading "可查看和纠正的记忆" [level=2] [ref=e52]
        - generic [ref=e53]:
          - generic [ref=e54]:
            - text: 偏好原文
            - textbox "偏好原文" [active] [ref=e55]
          - generic [ref=e56]:
            - text: 主题
            - textbox "主题" [ref=e57]: play
          - button "保存候选记忆" [ref=e58] [cursor=pointer]
        - paragraph [ref=e59]: 候选经主人确认后才进入公共上下文；家庭公共资料，未使用 AgentCore 提炼。
        - paragraph [ref=e60]: 还没有已保存的偏好记忆，可以先记录一件它喜欢的小事。
    - navigation "App 主导航" [ref=e61]:
      - text: 你的宠物世界
      - button "小屋" [ref=e62] [cursor=pointer]:
        - generic [aria-hidden] [ref=e63]: ⌂
        - text: 小屋
      - button "照护" [ref=e64] [cursor=pointer]:
        - generic [aria-hidden] [ref=e65]: ✓
        - text: 照护
      - button "助手" [ref=e66] [cursor=pointer]:
        - generic [aria-hidden] [ref=e67]: ✦
        - text: 助手
      - button "成长" [ref=e68] [cursor=pointer]:
        - generic [aria-hidden] [ref=e69]: ↗
        - text: 成长
      - button "家庭" [ref=e70] [cursor=pointer]:
        - generic [aria-hidden] [ref=e71]: ♡
        - text: 家庭
      - text: 小小的日常，慢慢的了解。
```

# Test source

```ts
  1   | import { test, expect, type Page } from "@playwright/test";
  2   | 
  3   | async function start(page: Page) {
  4   |   await page.goto("/#alexa");
  5   |   await page.getByRole("button", { name: "创建本地账号", exact: true }).click();
  6   |   await page.getByLabel("账号名").fill(`alexa-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`);
  7   |   await page.getByLabel("密码", { exact: true }).fill("browser-test-password");
  8   |   await page.getByLabel("昵称").fill("模拟体验主人");
  9   |   await page.getByRole("button", { name: "注册并登录", exact: true }).click();
  10  |   await page.getByLabel("家庭名称").fill("Alexa 体验家庭");
  11  |   await page.getByRole("button", { name: "创建家庭", exact: true }).click();
  12  | }
  13  | 
  14  | test("Alexa simulator reads shared memory and confirms manual care exactly once", async ({ page }) => {
  15  |   await start(page);
  16  |   await expect(page.getByRole("heading", { name: "Alexa+ 网页模拟器", exact: true })).toBeVisible({ timeout: 1500 });
  17  |   await page.getByRole("button", { name: "助手", exact: true }).click();
  18  |   await page.getByLabel("偏好原文").fill("喜欢蓝色羽毛棒");
  19  |   await page.getByRole("button", { name: "保存候选记忆" }).click();
> 20  |   await page.getByRole("button", { name: "确认记忆", exact: true }).click();
      |                                                                 ^ Error: locator.click: Test timeout of 30000ms exceeded.
  21  |   await page.getByRole("link", { name: "打开 Alexa+ 模拟器" }).click();
  22  |   await page.getByRole("button", { name: "它喜欢什么", exact: true }).click();
  23  |   const log = page.getByRole("log", { name: "Alexa 模拟对话" });
  24  |   await expect(log).toContainText("喜欢蓝色羽毛棒");
  25  |   await page.getByRole("button", { name: "新会话", exact: true }).click();
  26  |   await expect(log).not.toContainText("喜欢蓝色羽毛棒");
  27  |   await page.getByRole("button", { name: "它喜欢什么", exact: true }).click();
  28  |   await expect(log).toContainText("喜欢蓝色羽毛棒");
  29  |   await page.getByRole("button", { name: "安排陪玩", exact: true }).click();
  30  |   await expect(page.getByRole("region", { name: "待确认照护草案" })).toBeVisible();
  31  |   await page.getByRole("button", { name: "准备待确认方案" }).click();
  32  |   await expect(page.getByRole("region", { name: "待确认照护方案" })).toBeVisible();
  33  |   await page.getByRole("button", { name: "确认安排人工照护", exact: true }).click();
  34  |   await expect(page.getByRole("region", { name: "照护结果" })).toContainText("已安排，等待人工完成");
  35  |   await page.getByRole("region", { name: "照护结果" }).getByRole("button", { name: "查看照护任务" }).click();
  36  |   const task = page.getByRole("article").filter({ has: page.getByRole("heading", { name: "陪 Mochi 玩耍", exact: true }) });
  37  |   await expect(task).toHaveCount(1);
  38  |   await task.getByRole("button", { name: "完成照护" }).click();
  39  |   await page.getByRole("link", { name: "Alexa+ 模拟器", exact: true }).click();
  40  |   await page.getByRole("button", { name: "最近完成了什么", exact: true }).click();
  41  |   await expect(page.getByRole("log", { name: "Alexa 模拟对话" })).toContainText("陪 Mochi 玩耍");
  42  |   await expect(page.getByRole("log", { name: "Alexa 模拟对话" })).toContainText("人工完成记录");
  43  | });
  44  | 
  45  | test("new session clears transcript and stale drafts require a fresh question", async ({ page }) => {
  46  |   await start(page);
  47  |   await page.getByRole("button", { name: "安排换水", exact: true }).click();
  48  |   await expect(page.getByRole("region", { name: "待确认照护草案" })).toBeVisible();
  49  |   await page.evaluate(async () => {
  50  |     const me = await (await fetch("/api/family/me")).json();
  51  |     await fetch("/api/home/pets/mochi/notes", {
  52  |       method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": me.csrf_token },
  53  |       body: JSON.stringify({ text: "刚刚已经换水" }),
  54  |     });
  55  |   });
  56  |   await page.getByRole("button", { name: "准备待确认方案" }).click();
  57  |   await expect(page.getByRole("alert")).toContainText("记录已变化");
  58  |   await expect(page.getByRole("button", { name: "确认安排人工照护" })).toHaveCount(0);
  59  |   await page.getByRole("button", { name: "新会话", exact: true }).click();
  60  |   await expect(page.getByRole("log", { name: "Alexa 模拟对话" })).not.toContainText("刚刚已经换水");
  61  |   await expect(page.getByRole("region", { name: "待确认照护草案" })).toHaveCount(0);
  62  |   await page.getByRole("button", { name: "今天有什么观察", exact: true }).click();
  63  |   await expect(page.getByRole("log", { name: "Alexa 模拟对话" })).toContainText("刚刚已经换水");
  64  | });
  65  | 
  66  | for (const width of [320, 390, 1440]) {
  67  |   test(`Alexa simulator is usable at ${width}px`, async ({ page }) => {
  68  |     await page.setViewportSize({ width, height: 900 });
  69  |     await start(page);
  70  |     await page.getByLabel("模拟口述内容").fill("它喜欢什么");
  71  |     await page.getByRole("button", { name: "发送给 Alexa 模拟器" }).click();
  72  |     await expect(page.getByRole("log", { name: "Alexa 模拟对话" })).toContainText("还没有已确认的偏好记忆");
  73  |     await page.getByRole("button", { name: "安排换水", exact: true }).click();
  74  |     await page.getByRole("button", { name: "准备待确认方案" }).click();
  75  |     await expect(page.getByRole("region", { name: "待确认照护方案" })).toBeVisible();
  76  |     expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  77  |     await page.screenshot({ path: `test-results/alexa-${width}.png`, fullPage: true });
  78  |   });
  79  | }
  80  | 
  81  | test("pet switching drops a delayed response and resets draft scope", async ({ page }) => {
  82  |   await start(page);
  83  |   const pet = await page.evaluate(async () => {
  84  |     const me = await (await fetch("/api/family/me")).json();
  85  |     const home = await (await fetch("/api/home/pets", {
  86  |       method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": me.csrf_token },
  87  |       body: JSON.stringify({ name: "Luna" }),
  88  |     })).json();
  89  |     return home.pets.find((p: { name: string }) => p.name === "Luna");
  90  |   });
  91  |   await page.getByRole("button", { name: "同步最新记录" }).click();
  92  |   let release!: () => void;
  93  |   let arrived!: () => void;
  94  |   const gate = new Promise<void>((resolve) => { release = resolve; });
  95  |   const fetched = new Promise<void>((resolve) => { arrived = resolve; });
  96  |   await page.route("**/api/family/pets/mochi/chat", async (route) => {
  97  |     const response = await route.fetch();
  98  |     arrived();
  99  |     await gate;
  100 |     await route.fulfill({ response }).catch(() => {}); // switching aborts the old fetch
  101 |   });
  102 |   try {
  103 |     await page.getByRole("button", { name: "安排陪玩", exact: true }).click();
  104 |     await fetched;
  105 |     await page.getByRole("combobox", { name: "当前宠物", exact: true }).selectOption(pet.id);
  106 |     release();
  107 |     await expect(page.getByRole("complementary", { name: "当前模拟设备与宠物" })).toContainText("Luna");
  108 |     await expect(page.getByRole("log", { name: "Alexa 模拟对话" })).not.toContainText("Mochi");
  109 |     await expect(page.getByRole("region", { name: "待确认照护草案" })).toHaveCount(0);
  110 |     await page.getByRole("button", { name: "安排换水", exact: true }).click();
  111 |     await expect(page.getByRole("region", { name: "待确认照护草案" })).toContainText("Luna");
  112 |   } finally { release(); }
  113 | });
  114 | 
  115 | test("a failed chat restores the input and can be retried without inventing a reply", async ({ page }) => {
  116 |   await start(page);
  117 |   await page.route("**/api/family/pets/mochi/chat", (route) => route.fulfill({ status: 503, body: "unavailable" }), { times: 1 });
  118 |   await page.getByLabel("模拟口述内容").fill("它喜欢什么");
  119 |   await page.getByRole("button", { name: "发送给 Alexa 模拟器" }).click();
  120 |   await expect(page.getByRole("alert")).toBeVisible();
```