# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: alexa.spec.ts >> keyboard input and account navigation can return to Alexa
- Location: frontend\e2e\alexa.spec.ts:128:1

# Error details

```
Error: expect(page).toHaveURL(expected) failed

Expected pattern: /#app$/
Received string:  "http://127.0.0.1:8822/#app/family"
Timeout: 20000ms

Call log:
  - Expect "toHaveURL" with timeout 20000ms
    43 × locator resolved to <html lang="zh-CN">…</html>
       - unexpected value "http://127.0.0.1:8822/#app/family"

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
  - heading "Alexa 体验家庭" [level=1]
  - button "模拟体验主人"
  - button "退出账号"
  - paragraph: 本地独立账号 · 云认证未接通
  - status: 已保存
  - text: 当前宠物
  - combobox "当前宠物":
    - option "Mochi" [selected]
  - text: 记录人：模拟体验主人 · 家庭成员
  - button "同步最新记录"
  - heading "个人设置" [level=2]
  - text: 个人头像
  - combobox "个人头像":
    - option "🐾" [selected]
    - option "🐱"
    - option "🐶"
    - option "🌿"
    - option "⭐"
  - text: 个人昵称
  - textbox "个人昵称": 模拟体验主人
  - text: 家庭称呼
  - combobox "家庭称呼"
  - paragraph: 称呼由你选择，权限由管理员授权。
  - button "保存个人设置"
  - heading "当前家人" [level=3]
  - article:
    - strong: 🐾 模拟体验主人 · 家庭成员
    - paragraph: 管理员
    - text: 成员权限
    - combobox "模拟体验主人 的权限":
      - option "管理员" [selected]
      - option "照护成员"
      - option "访客"
  - button "退出家庭"
  - heading "邀请与家庭交接" [level=2]
  - group: 宠物资料管理
  - text: 授予权限
  - combobox "授予权限":
    - option "照护成员" [selected]
    - option "访客"
    - option "管理员"
  - text: 邀请有效小时
  - spinbutton "邀请有效小时": "48"
  - text: 允许使用次数
  - spinbutton "允许使用次数": "1"
  - button "生成家庭邀请"
  - group: 家庭设置
  - heading "最近家庭动态" [level=3]
  - paragraph: 模拟执行器回执仍在原工作台核验。
  - link "原工作台与证据入口":
    - /url: "#workbench"
  - navigation "App 主导航":
    - text: 你的宠物世界
    - button "小屋"
    - button "照护"
    - button "助手"
    - button "成长"
    - button "家庭"
    - text: 小小的日常，慢慢的了解。
```

# Test source

```ts
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
  121 |   await expect(page.getByLabel("模拟口述内容")).toHaveValue("它喜欢什么");
  122 |   await expect(page.getByRole("article", { name: "Alexa 分身回复" })).toHaveCount(0);
  123 |   await page.getByRole("button", { name: "发送给 Alexa 模拟器" }).click();
  124 |   await expect(page.getByRole("article", { name: "Alexa 分身回复" })).toHaveCount(1);
  125 |   await expect(page.getByRole("alert")).toHaveCount(0);
  126 | });
  127 | 
  128 | test("keyboard input and account navigation can return to Alexa", async ({ page }) => {
  129 |   await page.emulateMedia({ reducedMotion: "reduce" });
  130 |   await start(page);
  131 |   await page.getByRole("button", { name: "模拟体验主人", exact: true }).click();
> 132 |   await expect(page).toHaveURL(/#app$/);
      |                      ^ Error: expect(page).toHaveURL(expected) failed
  133 |   await page.getByRole("link", { name: "Alexa+ 模拟器", exact: true }).click();
  134 |   await expect(page.getByRole("heading", { name: "Alexa+ 网页模拟器", exact: true })).toBeVisible();
  135 |   const input = page.getByLabel("模拟口述内容");
  136 |   await input.fill("它喜欢什么");
  137 |   await input.press("Tab");
  138 |   await expect(page.getByRole("button", { name: "发送给 Alexa 模拟器" })).toBeFocused();
  139 |   await page.keyboard.press("Enter");
  140 |   await expect(page.getByRole("article", { name: "Alexa 分身回复" })).toBeVisible();
  141 |   await expect(page.getByRole("button", { name: "新会话", exact: true })).toBeEnabled();
  142 |   await page.getByRole("button", { name: "新会话", exact: true }).focus();
  143 |   await page.keyboard.press("Enter");
  144 |   await expect(page.getByRole("article", { name: "Alexa 分身回复" })).toHaveCount(0);
  145 |   expect(await page.locator(".alx-orb").evaluate((element) => getComputedStyle(element).animationName)).toBe("none");
  146 | });
  147 | 
  148 | test("Alexa displays the response backend and same-response model evidence", async ({ page }) => {
  149 |   await start(page);
  150 |   // Transport fixture tests rendering only; this is never evidence of AWS connectivity.
  151 |   await page.route("**/api/family/pets/mochi/chat", async (route) => {
  152 |     const response = await route.fetch();
  153 |     const local = await response.json();
  154 |     await route.fulfill({ response, json: {
  155 |       ...local, backend: "bedrock", answer_origin: "model",
  156 |       request_id: "offline-browser-response-1", model_id: "amazon.nova-lite-v1:0",
  157 |       input_tokens: 900, output_tokens: 70, inference_status: "completed",
  158 |     }});
  159 |   }, { times: 1 });
  160 |   await page.getByRole("button", { name: "它喜欢什么", exact: true }).click();
  161 |   const replies = page.getByRole("article", { name: "Alexa 分身回复" });
  162 |   await expect(replies.first()).toContainText("Bedrock 模型回答");
  163 |   await replies.first().getByText(/查看这轮依据/).click();
  164 |   await expect(replies.first()).toContainText("offline-browser-response-1");
  165 |   await expect(replies.first()).toContainText("输入 900 / 输出 70 tokens");
  166 |   await page.getByRole("button", { name: "安排陪玩", exact: true }).click();
  167 |   await expect(replies.last()).toContainText("本地规则");
  168 |   await expect(page.getByRole("region", { name: "待确认照护草案" })).toBeVisible();
  169 | });
  170 | 
```