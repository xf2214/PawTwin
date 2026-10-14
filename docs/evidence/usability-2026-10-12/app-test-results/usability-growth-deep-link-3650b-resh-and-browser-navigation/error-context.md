# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: usability.spec.ts >> growth deep link survives signup, refresh and browser navigation
- Location: frontend\e2e\usability.spec.ts:27:1

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.click: Test timeout of 30000ms exceeded.
Call log:
  - waiting for getByRole('button', { name: '创建本地账号', exact: true })

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - link "跳到产品内容" [ref=e4] [cursor=pointer]:
    - /url: "#product-content"
  - banner [ref=e5]:
    - generic [ref=e6]:
      - link "PawTwin 产品首页" [ref=e7] [cursor=pointer]:
        - /url: "#product"
        - text: PawTwin
      - navigation "产品导航" [ref=e14]:
        - link "产品体验" [ref=e15] [cursor=pointer]:
          - /url: "#features"
        - link "如何使用" [ref=e16] [cursor=pointer]:
          - /url: "#care"
        - link "日常案例" [ref=e17] [cursor=pointer]:
          - /url: "#cases"
        - link "进入应用" [ref=e18] [cursor=pointer]:
          - /url: "#app"
  - button "暂停动画" [ref=e19] [cursor=pointer]:
    - generic [aria-hidden] [ref=e20]: Ⅱ
    - text: 暂停动画
  - main [ref=e21]:
    - generic [ref=e22]:
      - generic [ref=e23]:
        - paragraph [ref=e24]: PawTwin · 一起，好好照顾。
        - heading "它的每一天， 值得被好好记住。" [level=1] [ref=e25]: 它的每一天，值得被好好记住。
        - paragraph [ref=e26]: 一个属于它的小屋。让全家的照顾、成长的瞬间，和一点点了解，在这里相遇。
        - generic [ref=e27]:
          - link "进入应用" [ref=e28] [cursor=pointer]:
            - /url: "#app"
          - link "了解产品" [ref=e29] [cursor=pointer]:
            - /url: "#features"
            - text: 了解产品
            - generic [aria-hidden] [ref=e30]: ›
      - generic "产品界面示意" [ref=e31]:
        - generic [ref=e34]:
          - generic [ref=e35]:
            - generic [ref=e36]: PawTwin
            - generic [ref=e43]: Mochi 的小屋
          - generic [ref=e45]:
            - complementary [ref=e46]:
              - strong [ref=e57]: Mochi
              - generic [ref=e58]: 属于它的小小世界
              - generic [ref=e59]:
                - generic [ref=e60]: ⌂ 小屋
                - generic [ref=e61]: ♡ 照护
                - generic [ref=e62]: ✦ 分身
                - generic [ref=e63]: ↗ 成长
            - generic [ref=e64]:
              - img "俯视的宠物小屋，中央是正面造型的橘猫" [ref=e65]:
                - generic [ref=e111]:
                  - generic [ref=e112]: 陪伴的角落
                  - generic [ref=e113]: 照护区
              - generic [ref=e114]:
                - generic [ref=e115]: 每一个小日常，都值得留下。
                - generic [ref=e116]: 产品界面示意
        - generic [ref=e117]:
          - paragraph [ref=e119]: PawTwin
          - heading "小小的它。 独一无二的日常。" [level=3] [ref=e129]: 小小的它。独一无二的日常。
          - generic [ref=e131]:
            - generic [ref=e132]:
              - text: 档案与偏好
              - generic [ref=e133]: ⌂
            - generic [ref=e134]:
              - text: 一起照顾
              - generic [ref=e135]: ♡
            - generic [ref=e136]:
              - text: 成长故事
              - generic [ref=e137]: ↗
          - generic [ref=e138]: 产品界面示意
      - paragraph [ref=e139]: 本地体验已开放 · 从猫和狗的日常照护开始
    - region [ref=e140]:
      - generic [ref=e141]:
        - paragraph [ref=e142]: 它的世界，从这里开始。
        - heading "小小一间屋。 装下大大的陪伴。" [level=2] [ref=e143]: 小小一间屋。装下大大的陪伴。
        - paragraph [ref=e144]: 喜欢的玩具，熟悉的窝，今天的小故事。把关于它的点点滴滴，放回属于它的地方。
      - generic [ref=e145]:
        - generic [ref=e158]: 它的习惯
        - generic [ref=e159]: 你的记录
        - generic [ref=e160]: 全家的关心
      - paragraph [ref=e161]: 像素宠物形象示意 · 可在应用中建立自己的宠物档案
    - generic [ref=e162]:
      - generic [ref=e163]:
        - paragraph [ref=e164]: 彼此连接的四种体验。
        - heading "从一只宠物，到一个家。" [level=2] [ref=e165]
        - paragraph [ref=e166]: 让记录有归处，让照护有回应。
      - group "查看产品体验" [ref=e167]:
        - button "宠物小屋" [pressed] [ref=e168] [cursor=pointer]:
          - generic [aria-hidden] [ref=e169]: ⌂
          - text: 宠物小屋
        - button "家庭照护" [ref=e170] [cursor=pointer]:
          - generic [aria-hidden] [ref=e171]: ✓
          - text: 家庭照护
        - button "成长记录" [ref=e172] [cursor=pointer]:
          - generic [aria-hidden] [ref=e173]: ↗
          - text: 成长记录
        - button "宠物分身" [ref=e174] [cursor=pointer]:
          - generic [aria-hidden] [ref=e175]: ✦
          - text: 宠物分身
      - generic [ref=e176]:
        - generic [ref=e177]:
          - generic [ref=e179]:
            - generic [ref=e180]:
              - generic [ref=e181]: PawTwin
              - generic [ref=e188]: Mochi 的小屋
            - generic [ref=e190]:
              - complementary [ref=e191]:
                - strong [ref=e202]: Mochi
                - generic [ref=e203]:
                  - generic [ref=e204]: ⌂ 小屋
                  - generic [ref=e205]: ♡ 照护
                  - generic [ref=e206]: ✦ 分身
                  - generic [ref=e207]: ↗ 成长
              - generic [ref=e208]:
                - img "俯视的宠物小屋，中央是正面造型的橘猫" [ref=e209]:
                  - generic [ref=e255]:
                    - generic [ref=e256]: 陪伴的角落
                    - generic [ref=e257]: 照护区
                - generic [ref=e258]:
                  - generic [ref=e259]: 每一个小日常，都值得留下。
                  - generic [ref=e260]: 产品界面示意
          - paragraph [ref=e261]: 每只宠物都有自己的记录与偏好
          - generic [ref=e262]: 产品界面示意 · 功能以应用内实际状态为准
        - generic [ref=e263]:
          - generic [ref=e264]: 01 / 宠物小屋
          - heading "给每个小家伙，一个自己的家。" [level=3] [ref=e265]
          - paragraph [ref=e266]: 一张档案，一间小屋。把它喜欢的玩具、常睡的窝和你确认的偏好放在一起，让照护从了解它开始。
          - generic [ref=e267]:
            - generic [ref=e268]: ✓独立宠物档案
            - generic [ref=e269]: ✓像素小屋
            - generic [ref=e270]: ✓照片日记
          - link "在应用中体验" [ref=e271] [cursor=pointer]:
            - /url: "#app"
            - text: 在应用中体验
            - generic [aria-hidden] [ref=e272]: ›
    - region [ref=e273]:
      - generic [ref=e274]:
        - paragraph [ref=e275]: 三个场景，一起看看。
        - heading "把功能，放进日常。" [level=2] [ref=e276]
        - paragraph [ref=e277]: 不是功能清单，是你和它的一天。
      - group "选择日常案例" [ref=e278]:
        - button "家庭交接" [pressed] [ref=e279] [cursor=pointer]
        - button "成长回顾" [ref=e280] [cursor=pointer]
        - button "偏好接续" [ref=e281] [cursor=pointer]
      - generic [ref=e282]:
        - generic "案例画面" [ref=e283]:
          - generic [aria-hidden] [ref=e284]:
            - generic [ref=e296]: ♡
            - generic [ref=e297]: Mochi 的日常
          - generic [ref=e298]:
            - generic [ref=e299]:
              - generic [ref=e300]: 情景示意
              - generic [ref=e301]: 步骤 1 / 3
            - heading "换一碗新鲜的水" [level=3] [ref=e302]
            - generic [ref=e303]: 待领取
            - paragraph [ref=e304]: 主人创建一项人工照护事项，等待家人接手。
          - generic [ref=e309]: 虚构情景演示 · 不会创建真实照护任务
        - generic [ref=e310]:
          - generic [ref=e311]:
            - generic [ref=e312]: 案例 01 / 家庭交接
            - heading "你出门了，照顾还在继续。" [level=3] [ref=e313]
            - paragraph [ref=e314]: 出门前为 Mochi 安排换水。家人接手后，在实际完成时留下记录，彼此不用反复确认。
          - group "查看案例步骤" [ref=e315]:
            - button "01 主人安排" [pressed] [ref=e316] [cursor=pointer]:
              - generic [ref=e317]: "01"
              - strong [ref=e318]: 主人安排
              - generic [aria-hidden] [ref=e319]: −
            - button "02 家人接手" [ref=e320] [cursor=pointer]:
              - generic [ref=e321]: "02"
              - strong [ref=e322]: 家人接手
              - generic [aria-hidden] [ref=e323]: +
            - button "03 完成并回写" [ref=e324] [cursor=pointer]:
              - generic [ref=e325]: "03"
              - strong [ref=e326]: 完成并回写
              - generic [aria-hidden] [ref=e327]: +
          - paragraph [ref=e328]: 主人创建一项人工照护事项，等待家人接手。
          - paragraph [ref=e329]: 任务的每一次交接，都有清楚的去向。
          - link "在应用中开始" [ref=e330] [cursor=pointer]:
            - /url: "#app"
            - text: 在应用中开始
            - generic [aria-hidden] [ref=e331]: ›
    - generic [ref=e332]:
      - generic [ref=e333]:
        - paragraph [ref=e334]: 每一份了解，都有来处。
        - heading "记住它。 也记住为什么。" [level=2] [ref=e335]: 记住它。也记住为什么。
        - paragraph [ref=e336]: 档案、实测成长和你确认的偏好，串起它的日常。留下来源，保留空白，让每一次回顾都有依据。
        - link "探索成长记录" [ref=e337] [cursor=pointer]:
          - /url: "#features"
          - text: 探索成长记录
          - generic [aria-hidden] [ref=e338]: ›
      - generic "记录来源示意" [ref=e339]:
        - generic [ref=e341]:
          - generic [ref=e342]: "01"
          - generic [ref=e343]:
            - heading "实测成长" [level=3] [ref=e344]
            - paragraph [ref=e345]: 来自你记录的测量与时间
        - generic [ref=e346]:
          - generic [ref=e347]: "02"
          - generic [ref=e348]:
            - heading "确认偏好" [level=3] [ref=e349]
            - paragraph [ref=e350]: 由主人确认，可修改与删除
        - generic [ref=e351]:
          - generic [ref=e352]: "03"
          - generic [ref=e353]:
            - heading "照护记录" [level=3] [ref=e354]
            - paragraph [ref=e355]: 实际完成之后，才留下记录
        - generic [ref=e356]: 记录结构示意 · 非真实宠物数据
    - generic [ref=e357]:
      - generic [ref=e358]:
        - paragraph [ref=e359]: 从今天的一件小事开始。
        - heading "让关心，变成有回应的日常。" [level=2] [ref=e360]
        - paragraph [ref=e361]: 认识它，一起安排，接手照顾，再回看成长。
      - generic [ref=e362]:
        - article [ref=e363]:
          - text: "01"
          - heading "认识它" [level=3] [ref=e364]
          - paragraph [ref=e365]: 创建宠物档案，记录它的习惯与偏好。
        - article [ref=e366]:
          - text: "02"
          - heading "一起安排" [level=3] [ref=e367]
          - paragraph [ref=e368]: 邀请家人，安排需要完成的照护事项。
        - article [ref=e369]:
          - text: "03"
          - heading "接手照顾" [level=3] [ref=e370]
          - paragraph [ref=e371]: 领取任务，在实际完成后留下记录。
        - article [ref=e372]:
          - text: "04"
          - heading "回看成长" [level=3] [ref=e373]
          - paragraph [ref=e374]: 在日记与报告里，看见点滴变化。
    - generic [ref=e375]:
      - paragraph [ref=e383]: PawTwin
      - heading "一起照顾。 也一起记得。" [level=2] [ref=e384]: 一起照顾。也一起记得。
      - paragraph [ref=e385]: 为它，也为每一个关心它的人。
      - link "建立我的宠物小屋" [ref=e386] [cursor=pointer]:
        - /url: "#app"
        - text: 建立我的宠物小屋
        - generic [aria-hidden] [ref=e387]: ›
  - contentinfo [ref=e388]:
    - generic [ref=e389]:
      - generic [ref=e390]:
        - link "PawTwin" [ref=e391] [cursor=pointer]:
          - /url: "#product"
        - generic [ref=e398]: 给日常一点记忆，给陪伴更多了解。
        - link "照护工作台" [ref=e399] [cursor=pointer]:
          - /url: "#workbench"
      - paragraph [ref=e400]: 家庭身份与记录仍为本地服务；实际回答后端与依据见每轮回复，Alexa 为网页模拟。PawLink 项圈为概念，设备执行为模拟，云端能力尚未验证。
      - paragraph [ref=e401]:
        - text: PawTwin · 每只宠物，各有不同。
        - link "进入家庭应用" [ref=e402] [cursor=pointer]:
          - /url: "#app"
          - text: 进入家庭应用 ↗
```

# Test source

```ts
  1   | import { test, expect, type Page } from "@playwright/test";
  2   | 
  3   | test.use({ timezoneId: "Asia/Shanghai" });
  4   | 
  5   | async function start(page: Page, timezone = "Asia/Shanghai", path = "/#app") {
  6   |   await page.goto(path);
> 7   |   await page.getByRole("button", { name: "创建本地账号", exact: true }).click();
      |                                                                   ^ Error: locator.click: Test timeout of 30000ms exceeded.
  8   |   await page.getByLabel("账号名").fill(`daily-${Date.now()}-${Math.floor(Math.random() * 99999)}`);
  9   |   await page.getByLabel("密码", { exact: true }).fill("browser-test-password");
  10  |   await page.getByLabel("昵称").fill("日常主人");
  11  |   await page.getByRole("button", { name: "注册并登录", exact: true }).click();
  12  |   await page.getByLabel("家庭名称").fill("我们的日常");
  13  |   await page.getByLabel("家庭时区", { exact: true }).fill(timezone);
  14  |   await page.getByRole("button", { name: "创建家庭", exact: true }).click();
  15  |   await expect(page.getByRole("navigation", { name: "App 主导航" })).toBeVisible();
  16  | }
  17  | 
  18  | async function mutate(page: Page, path: string, body: object, method = "POST") {
  19  |   return page.evaluate(async ({ path, body, method }) => {
  20  |     const me = await (await fetch("/api/family/me")).json();
  21  |     const response = await fetch(path, { method, headers: { "Content-Type": "application/json", "X-CSRF-Token": me.csrf_token }, body: JSON.stringify(body) });
  22  |     if (!response.ok) throw new Error(`${response.status}: ${await response.text()}`);
  23  |     return response.json();
  24  |   }, { path, body, method });
  25  | }
  26  | 
  27  | test("growth deep link survives signup, refresh and browser navigation", async ({ page }) => {
  28  |   await start(page, "Asia/Shanghai", "/#app/growth");
  29  |   await expect(page.getByRole("heading", { name: "成长曲线", exact: true })).toBeVisible();
  30  |   await page.reload();
  31  |   await expect(page.getByRole("heading", { name: "成长曲线", exact: true })).toBeVisible();
  32  |   await page.getByRole("button", { name: "照护", exact: true }).click();
  33  |   await expect(page).toHaveURL(/#app\/care$/);
  34  |   await page.goBack();
  35  |   await expect(page.getByRole("heading", { name: "成长曲线", exact: true })).toBeVisible();
  36  | });
  37  | 
  38  | test("editing only a recurring task title preserves its future time and interval", async ({ page }) => {
  39  |   await start(page);
  40  |   await page.getByRole("button", { name: "照护", exact: true }).click();
  41  |   const created = await mutate(page, "/api/home/pets/mochi/tasks", { kind: "brush", title: "每周梳毛", due_at: "2027-01-20T12:00:00+00:00", interval_days: 7 });
  42  |   const original = created.tasks.find((t: { title: string }) => t.title === "每周梳毛");
  43  |   await page.getByRole("button", { name: "同步最新记录" }).click();
  44  |   const card = page.getByRole("article").filter({ has: page.getByRole("heading", { name: "每周梳毛", exact: true }) });
  45  |   await card.getByText("编辑或延期", { exact: true }).click();
  46  |   await card.getByLabel("任务标题").fill("温柔梳毛");
  47  |   await card.getByRole("button", { name: "保存任务编辑" }).click();
  48  |   await expect(page.getByRole("heading", { name: "温柔梳毛", exact: true })).toBeVisible();
  49  |   const updated = (await (await page.request.get("/api/home/state")).json()).tasks.find((t: { id: string }) => t.id === original.id);
  50  |   expect(updated.due_at).toBe(original.due_at);
  51  |   expect(updated.interval_days).toBe(7);
  52  | });
  53  | 
  54  | test("daily queue uses household day and keeps completed care out of active filters", async ({ page }) => {
  55  |   await page.clock.setFixedTime(new Date("2026-10-12T01:00:00Z"));
  56  |   await start(page, "Pacific/Honolulu");
  57  |   const me = await (await page.request.get("/api/family/me")).json();
  58  |   for (const task of [
  59  |     { title: "昨天换水", due_at: "2026-10-10T21:00:00Z" },
  60  |     { title: "今天陪玩", due_at: "2026-10-12T02:00:00Z", assigned_to: me.user.user_id },
  61  |     { title: "以后梳毛", due_at: "2026-10-13T20:00:00Z" },
  62  |     { title: "已做清洁", due_at: "2026-10-11T20:00:00Z" },
  63  |   ]) await mutate(page, "/api/home/pets/mochi/tasks", { kind: "play", ...task });
  64  |   const home = await (await page.request.get("/api/home/state")).json();
  65  |   const done = home.tasks.find((t: { title: string }) => t.title === "已做清洁");
  66  |   await mutate(page, `/api/home/tasks/${done.id}/action`, { action: "complete", version: done.version, event_id: crypto.randomUUID() });
  67  |   await page.getByRole("button", { name: "同步最新记录" }).click();
  68  |   const overview = page.getByRole("region", { name: "今日概览" });
  69  |   await expect(overview).toContainText("2026-10-11");
  70  |   await overview.getByRole("button", { name: "查看照护" }).click();
  71  |   await page.getByRole("button", { name: "今天", exact: true }).click();
  72  |   const queue = page.getByRole("region", { name: "照护队列" });
  73  |   await expect(queue).toContainText("今天陪玩");
  74  |   await expect(queue).not.toContainText("以后梳毛");
  75  |   await expect(queue).not.toContainText("已做清洁");
  76  |   await page.getByRole("button", { name: "逾期", exact: true }).click();
  77  |   await expect(queue).toContainText("昨天换水");
  78  |   await expect(queue).not.toContainText("今天陪玩");
  79  |   await page.getByRole("button", { name: "我负责", exact: true }).click();
  80  |   await expect(queue).toContainText("今天陪玩");
  81  |   await expect(queue).not.toContainText("昨天换水");
  82  |   await page.getByRole("button", { name: "已完成", exact: true }).click();
  83  |   await expect(queue).toContainText("已做清洁");
  84  |   await page.getByRole("button", { name: "小屋", exact: true }).first().click();
  85  |   await page.getByRole("button", { name: "管理照护计划", exact: true }).click();
  86  |   await expect(page).toHaveURL(/#app\/care$/);
  87  | });
  88  | 
  89  | test("a failed measurement read preserves reports and retries the failed resource", async ({ page }) => {
  90  |   await start(page);
  91  |   await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 1.2, unit: "kg", measured_at: "2026-10-01T12:00:00Z", source: "owner_measured" });
  92  |   await mutate(page, "/api/family/pets/mochi/reports/generate", { period: "weekly", date: "2026-10-02" });
  93  |   let failed = false;
  94  |   await page.route("**/api/family/pets/mochi/measurements", async route => {
  95  |     if (!failed && route.request().method() === "GET") { failed = true; await route.fulfill({ status: 503, json: { detail: "temporarily unavailable" } }); }
  96  |     else await route.continue();
  97  |   });
  98  |   await page.goto("/#app/growth");
  99  |   await page.reload();
  100 |   await expect(page.getByText("成长记录暂时无法读取。", { exact: true })).toBeVisible();
  101 |   await expect(page.getByRole("heading", { name: /^周报 ·/ })).toBeVisible();
  102 |   await expect(page.getByText("还没有有效成长记录。", { exact: true })).toHaveCount(0);
  103 |   await page.getByRole("button", { name: "重试成长记录", exact: true }).click();
  104 |   await expect(page.getByText("1.2 kg · 主人实测", { exact: true })).toBeVisible();
  105 |   await expect(page.getByText("成长记录暂时无法读取。", { exact: true })).toHaveCount(0);
  106 | });
  107 | 
```