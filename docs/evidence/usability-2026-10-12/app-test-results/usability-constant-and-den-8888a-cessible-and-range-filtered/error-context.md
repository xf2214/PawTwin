# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: usability.spec.ts >> constant and dense real measurements remain accessible and range-filtered
- Location: frontend\e2e\usability.spec.ts:129:1

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.selectOption: Test timeout of 30000ms exceeded.
Call log:
  - waiting for getByLabel('曲线时间范围')

```

# Page snapshot

```yaml
- generic [ref=f1e3]:
  - link "跳到产品内容" [ref=f1e4] [cursor=pointer]:
    - /url: "#product-content"
  - banner [ref=f1e5]:
    - generic [ref=f1e6]:
      - link "PawTwin 产品首页" [ref=f1e7] [cursor=pointer]:
        - /url: "#product"
        - text: PawTwin
      - navigation "产品导航" [ref=f1e14]:
        - link "产品体验" [ref=f1e15] [cursor=pointer]:
          - /url: "#features"
        - link "如何使用" [ref=f1e16] [cursor=pointer]:
          - /url: "#care"
        - link "日常案例" [ref=f1e17] [cursor=pointer]:
          - /url: "#cases"
        - link "进入应用" [ref=f1e18] [cursor=pointer]:
          - /url: "#app"
  - button "暂停动画" [ref=f1e19] [cursor=pointer]:
    - generic [aria-hidden] [ref=f1e20]: Ⅱ
    - text: 暂停动画
  - main [ref=f1e21]:
    - generic [ref=f1e22]:
      - generic [ref=f1e23]:
        - paragraph [ref=f1e24]: PawTwin · 一起，好好照顾。
        - heading "它的每一天， 值得被好好记住。" [level=1] [ref=f1e25]: 它的每一天，值得被好好记住。
        - paragraph [ref=f1e26]: 一个属于它的小屋。让全家的照顾、成长的瞬间，和一点点了解，在这里相遇。
        - generic [ref=f1e27]:
          - link "进入应用" [ref=f1e28] [cursor=pointer]:
            - /url: "#app"
          - link "了解产品" [ref=f1e29] [cursor=pointer]:
            - /url: "#features"
            - text: 了解产品
            - generic [aria-hidden] [ref=f1e30]: ›
      - generic "产品界面示意" [ref=f1e31]:
        - generic [ref=f1e34]:
          - generic [ref=f1e35]:
            - generic [ref=f1e36]: PawTwin
            - generic [ref=f1e43]: Mochi 的小屋
          - generic [ref=f1e45]:
            - complementary [ref=f1e46]:
              - strong [ref=f1e57]: Mochi
              - generic [ref=f1e58]: 属于它的小小世界
              - generic [ref=f1e59]:
                - generic [ref=f1e60]: ⌂ 小屋
                - generic [ref=f1e61]: ♡ 照护
                - generic [ref=f1e62]: ✦ 分身
                - generic [ref=f1e63]: ↗ 成长
            - generic [ref=f1e64]:
              - img "俯视的宠物小屋，中央是正面造型的橘猫" [ref=f1e65]:
                - generic [ref=f1e111]:
                  - generic [ref=f1e112]: 陪伴的角落
                  - generic [ref=f1e113]: 照护区
              - generic [ref=f1e114]:
                - generic [ref=f1e115]: 每一个小日常，都值得留下。
                - generic [ref=f1e116]: 产品界面示意
        - generic [ref=f1e117]:
          - paragraph [ref=f1e119]: PawTwin
          - heading "小小的它。 独一无二的日常。" [level=3] [ref=f1e129]: 小小的它。独一无二的日常。
          - generic [ref=f1e131]:
            - generic [ref=f1e132]:
              - text: 档案与偏好
              - generic [ref=f1e133]: ⌂
            - generic [ref=f1e134]:
              - text: 一起照顾
              - generic [ref=f1e135]: ♡
            - generic [ref=f1e136]:
              - text: 成长故事
              - generic [ref=f1e137]: ↗
          - generic [ref=f1e138]: 产品界面示意
      - paragraph [ref=f1e139]: 本地体验已开放 · 从猫和狗的日常照护开始
    - region [ref=f1e140]:
      - generic [ref=f1e141]:
        - paragraph [ref=f1e142]: 它的世界，从这里开始。
        - heading "小小一间屋。 装下大大的陪伴。" [level=2] [ref=f1e143]: 小小一间屋。装下大大的陪伴。
        - paragraph [ref=f1e144]: 喜欢的玩具，熟悉的窝，今天的小故事。把关于它的点点滴滴，放回属于它的地方。
      - generic [ref=f1e145]:
        - generic [ref=f1e158]: 它的习惯
        - generic [ref=f1e159]: 你的记录
        - generic [ref=f1e160]: 全家的关心
      - paragraph [ref=f1e161]: 像素宠物形象示意 · 可在应用中建立自己的宠物档案
    - generic [ref=f1e162]:
      - generic [ref=f1e163]:
        - paragraph [ref=f1e164]: 彼此连接的四种体验。
        - heading "从一只宠物，到一个家。" [level=2] [ref=f1e165]
        - paragraph [ref=f1e166]: 让记录有归处，让照护有回应。
      - group "查看产品体验" [ref=f1e167]:
        - button "宠物小屋" [pressed] [ref=f1e168] [cursor=pointer]:
          - generic [aria-hidden] [ref=f1e169]: ⌂
          - text: 宠物小屋
        - button "家庭照护" [ref=f1e170] [cursor=pointer]:
          - generic [aria-hidden] [ref=f1e171]: ✓
          - text: 家庭照护
        - button "成长记录" [ref=f1e172] [cursor=pointer]:
          - generic [aria-hidden] [ref=f1e173]: ↗
          - text: 成长记录
        - button "宠物分身" [ref=f1e174] [cursor=pointer]:
          - generic [aria-hidden] [ref=f1e175]: ✦
          - text: 宠物分身
      - generic [ref=f1e176]:
        - generic [ref=f1e177]:
          - generic [ref=f1e179]:
            - generic [ref=f1e180]:
              - generic [ref=f1e181]: PawTwin
              - generic [ref=f1e188]: Mochi 的小屋
            - generic [ref=f1e190]:
              - complementary [ref=f1e191]:
                - strong [ref=f1e202]: Mochi
                - generic [ref=f1e203]:
                  - generic [ref=f1e204]: ⌂ 小屋
                  - generic [ref=f1e205]: ♡ 照护
                  - generic [ref=f1e206]: ✦ 分身
                  - generic [ref=f1e207]: ↗ 成长
              - generic [ref=f1e208]:
                - img "俯视的宠物小屋，中央是正面造型的橘猫" [ref=f1e209]:
                  - generic [ref=f1e255]:
                    - generic [ref=f1e256]: 陪伴的角落
                    - generic [ref=f1e257]: 照护区
                - generic [ref=f1e258]:
                  - generic [ref=f1e259]: 每一个小日常，都值得留下。
                  - generic [ref=f1e260]: 产品界面示意
          - paragraph [ref=f1e261]: 每只宠物都有自己的记录与偏好
          - generic [ref=f1e262]: 产品界面示意 · 功能以应用内实际状态为准
        - generic [ref=f1e263]:
          - generic [ref=f1e264]: 01 / 宠物小屋
          - heading "给每个小家伙，一个自己的家。" [level=3] [ref=f1e265]
          - paragraph [ref=f1e266]: 一张档案，一间小屋。把它喜欢的玩具、常睡的窝和你确认的偏好放在一起，让照护从了解它开始。
          - generic [ref=f1e267]:
            - generic [ref=f1e268]: ✓独立宠物档案
            - generic [ref=f1e269]: ✓像素小屋
            - generic [ref=f1e270]: ✓照片日记
          - link "在应用中体验" [ref=f1e271] [cursor=pointer]:
            - /url: "#app"
            - text: 在应用中体验
            - generic [aria-hidden] [ref=f1e272]: ›
    - region [ref=f1e273]:
      - generic [ref=f1e274]:
        - paragraph [ref=f1e275]: 三个场景，一起看看。
        - heading "把功能，放进日常。" [level=2] [ref=f1e276]
        - paragraph [ref=f1e277]: 不是功能清单，是你和它的一天。
      - group "选择日常案例" [ref=f1e278]:
        - button "家庭交接" [pressed] [ref=f1e279] [cursor=pointer]
        - button "成长回顾" [ref=f1e280] [cursor=pointer]
        - button "偏好接续" [ref=f1e281] [cursor=pointer]
      - generic [ref=f1e282]:
        - generic "案例画面" [ref=f1e283]:
          - generic [aria-hidden] [ref=f1e284]:
            - generic [ref=f1e296]: ♡
            - generic [ref=f1e297]: Mochi 的日常
          - generic [ref=f1e298]:
            - generic [ref=f1e299]:
              - generic [ref=f1e300]: 情景示意
              - generic [ref=f1e301]: 步骤 1 / 3
            - heading "换一碗新鲜的水" [level=3] [ref=f1e302]
            - generic [ref=f1e303]: 待领取
            - paragraph [ref=f1e304]: 主人创建一项人工照护事项，等待家人接手。
          - generic [ref=f1e309]: 虚构情景演示 · 不会创建真实照护任务
        - generic [ref=f1e310]:
          - generic [ref=f1e311]:
            - generic [ref=f1e312]: 案例 01 / 家庭交接
            - heading "你出门了，照顾还在继续。" [level=3] [ref=f1e313]
            - paragraph [ref=f1e314]: 出门前为 Mochi 安排换水。家人接手后，在实际完成时留下记录，彼此不用反复确认。
          - group "查看案例步骤" [ref=f1e315]:
            - button "01 主人安排" [pressed] [ref=f1e316] [cursor=pointer]:
              - generic [ref=f1e317]: "01"
              - strong [ref=f1e318]: 主人安排
              - generic [aria-hidden] [ref=f1e319]: −
            - button "02 家人接手" [ref=f1e320] [cursor=pointer]:
              - generic [ref=f1e321]: "02"
              - strong [ref=f1e322]: 家人接手
              - generic [aria-hidden] [ref=f1e323]: +
            - button "03 完成并回写" [ref=f1e324] [cursor=pointer]:
              - generic [ref=f1e325]: "03"
              - strong [ref=f1e326]: 完成并回写
              - generic [aria-hidden] [ref=f1e327]: +
          - paragraph [ref=f1e328]: 主人创建一项人工照护事项，等待家人接手。
          - paragraph [ref=f1e329]: 任务的每一次交接，都有清楚的去向。
          - link "在应用中开始" [ref=f1e330] [cursor=pointer]:
            - /url: "#app"
            - text: 在应用中开始
            - generic [aria-hidden] [ref=f1e331]: ›
    - generic [ref=f1e332]:
      - generic [ref=f1e333]:
        - paragraph [ref=f1e334]: 每一份了解，都有来处。
        - heading "记住它。 也记住为什么。" [level=2] [ref=f1e335]: 记住它。也记住为什么。
        - paragraph [ref=f1e336]: 档案、实测成长和你确认的偏好，串起它的日常。留下来源，保留空白，让每一次回顾都有依据。
        - link "探索成长记录" [ref=f1e337] [cursor=pointer]:
          - /url: "#features"
          - text: 探索成长记录
          - generic [aria-hidden] [ref=f1e338]: ›
      - generic "记录来源示意" [ref=f1e339]:
        - generic [ref=f1e341]:
          - generic [ref=f1e342]: "01"
          - generic [ref=f1e343]:
            - heading "实测成长" [level=3] [ref=f1e344]
            - paragraph [ref=f1e345]: 来自你记录的测量与时间
        - generic [ref=f1e346]:
          - generic [ref=f1e347]: "02"
          - generic [ref=f1e348]:
            - heading "确认偏好" [level=3] [ref=f1e349]
            - paragraph [ref=f1e350]: 由主人确认，可修改与删除
        - generic [ref=f1e351]:
          - generic [ref=f1e352]: "03"
          - generic [ref=f1e353]:
            - heading "照护记录" [level=3] [ref=f1e354]
            - paragraph [ref=f1e355]: 实际完成之后，才留下记录
        - generic [ref=f1e356]: 记录结构示意 · 非真实宠物数据
    - generic [ref=f1e357]:
      - generic [ref=f1e358]:
        - paragraph [ref=f1e359]: 从今天的一件小事开始。
        - heading "让关心，变成有回应的日常。" [level=2] [ref=f1e360]
        - paragraph [ref=f1e361]: 认识它，一起安排，接手照顾，再回看成长。
      - generic [ref=f1e362]:
        - article [ref=f1e363]:
          - text: "01"
          - heading "认识它" [level=3] [ref=f1e364]
          - paragraph [ref=f1e365]: 创建宠物档案，记录它的习惯与偏好。
        - article [ref=f1e366]:
          - text: "02"
          - heading "一起安排" [level=3] [ref=f1e367]
          - paragraph [ref=f1e368]: 邀请家人，安排需要完成的照护事项。
        - article [ref=f1e369]:
          - text: "03"
          - heading "接手照顾" [level=3] [ref=f1e370]
          - paragraph [ref=f1e371]: 领取任务，在实际完成后留下记录。
        - article [ref=f1e372]:
          - text: "04"
          - heading "回看成长" [level=3] [ref=f1e373]
          - paragraph [ref=f1e374]: 在日记与报告里，看见点滴变化。
    - generic [ref=f1e375]:
      - paragraph [ref=f1e383]: PawTwin
      - heading "一起照顾。 也一起记得。" [level=2] [ref=f1e384]: 一起照顾。也一起记得。
      - paragraph [ref=f1e385]: 为它，也为每一个关心它的人。
      - link "建立我的宠物小屋" [ref=f1e386] [cursor=pointer]:
        - /url: "#app"
        - text: 建立我的宠物小屋
        - generic [aria-hidden] [ref=f1e387]: ›
  - contentinfo [ref=f1e388]:
    - generic [ref=f1e389]:
      - generic [ref=f1e390]:
        - link "PawTwin" [ref=f1e391] [cursor=pointer]:
          - /url: "#product"
        - generic [ref=f1e398]: 给日常一点记忆，给陪伴更多了解。
        - link "照护工作台" [ref=f1e399] [cursor=pointer]:
          - /url: "#workbench"
      - paragraph [ref=f1e400]: 家庭身份与记录仍为本地服务；实际回答后端与依据见每轮回复，Alexa 为网页模拟。PawLink 项圈为概念，设备执行为模拟，云端能力尚未验证。
      - paragraph [ref=f1e401]:
        - text: PawTwin · 每只宠物，各有不同。
        - link "进入家庭应用" [ref=f1e402] [cursor=pointer]:
          - /url: "#app"
          - text: 进入家庭应用 ↗
```

# Test source

```ts
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
  98  |   await page.goto("/#app");
  99  |   await page.reload();
  100 |   await page.getByRole("button", { name: "成长", exact: true }).click();
  101 |   await expect(page.getByText("成长记录暂时无法读取。", { exact: true })).toBeVisible();
  102 |   await expect(page.getByRole("heading", { name: /^周报 ·/ })).toBeVisible();
  103 |   await expect(page.getByText("还没有有效成长记录。", { exact: true })).toHaveCount(0);
  104 |   await page.getByRole("button", { name: "重试成长记录", exact: true }).click();
  105 |   await expect(page.getByText("1.2 kg · 主人实测", { exact: true })).toBeVisible();
  106 |   await expect(page.getByText("成长记录暂时无法读取。", { exact: true })).toHaveCount(0);
  107 | });
  108 | 
  109 | test("a late growth read cannot replace the selected pet data", async ({ page }) => {
  110 |   await start(page);
  111 |   const created = await mutate(page, "/api/home/pets", { name: "Luna", species: "cat" });
  112 |   const luna = created.pets.find((p: { name: string }) => p.name === "Luna");
  113 |   await mutate(page, `/api/family/pets/${luna.id}/measurements`, { kind: "weight", value: 3, unit: "kg", measured_at: "2026-10-01T12:00:00Z", source: "vet" });
  114 |   let release!: () => void;
  115 |   const gate = new Promise<void>(resolve => { release = resolve; });
  116 |   let reached!: () => void;
  117 |   const received = new Promise<void>(resolve => { reached = resolve; });
  118 |   await page.route("**/api/family/pets/mochi/measurements", async route => { const response = await route.fetch(); reached(); await gate; await route.fulfill({ response }); });
  119 |   await page.goto("/#app");
  120 |   await page.reload({ waitUntil: "domcontentloaded" });
  121 |   await received;
  122 |   try {
  123 |     await page.getByRole("button", { name: "成长", exact: true }).click();
  124 |     await page.locator(".fa-petbar").getByLabel("当前宠物").selectOption(luna.id);
  125 |     await expect(page.getByRole("region", { name: "成长概览" })).toContainText("3 kg");
  126 |   } finally { release(); }
  127 |   await expect(page.getByRole("region", { name: "成长概览" })).toContainText("兽医资料");
  128 |   await expect(page.getByRole("region", { name: "成长概览" })).not.toContainText("暂无称重");
  129 | });
  130 | 
  131 | test("constant and dense real measurements remain accessible and range-filtered", async ({ page }) => {
  132 |   await page.clock.setFixedTime(new Date("2026-10-12T01:00:00Z"));
  133 |   await start(page);
  134 |   await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 1.5, unit: "kg", measured_at: "2026-06-01T12:00:00Z", source: "vet" });
  135 |   for (let day = 1; day <= 10; day++) await mutate(page, "/api/family/pets/mochi/measurements", { kind: "weight", value: 2, unit: "kg", measured_at: `2026-10-${String(day).padStart(2, "0")}T12:00:00Z`, source: "owner_measured" });
> 136 |   await page.goto("/#app");
      |                                   ^ Error: locator.selectOption: Test timeout of 30000ms exceeded.
  137 |   await page.reload();
  138 |   await page.getByRole("button", { name: "成长", exact: true }).click();
  139 |   await page.getByLabel("曲线时间范围").selectOption("30");
  140 |   const chart = page.getByRole("region", { name: "体重曲线与明细" });
  141 |   await chart.getByText("查看测量明细", { exact: true }).click();
  142 |   await expect(chart.getByRole("table", { name: "体重测量明细" }).getByRole("row")).toHaveCount(11);
  143 |   await expect(chart).not.toContainText("2026-06-01");
  144 |   await expect(chart.getByRole("img", { name: /主人实测体重曲线/ })).toBeVisible();
  145 |   expect(await chart.locator("svg circle").evaluateAll(elements => elements.every(el => Number.isFinite(Number(el.getAttribute("cy")))))).toBe(true);
  146 |   await page.getByLabel("曲线时间范围").selectOption("all");
  147 |   await expect(chart.getByRole("table").getByRole("row")).toHaveCount(12);
  148 | });
  149 | 
  150 | for (const width of [320, 390, 1440]) {
  151 |   test(`daily application at ${width}px stays readable and keyboard accessible`, async ({ page }, info) => {
  152 |     await page.setViewportSize({ width, height: 900 });
  153 |     await start(page);
  154 |     for (const name of ["小屋", "照护", "成长", "家庭"]) {
  155 |       await page.getByRole("navigation", { name: "App 主导航" }).getByRole("button", { name, exact: true }).focus();
  156 |       await page.keyboard.press("Enter");
  157 |       await expect(page.getByRole("navigation", { name: "App 主导航" }).getByRole("button", { name, exact: true })).toHaveAttribute("aria-current", "page");
  158 |       expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  159 |       if (name === "小屋" || name === "成长" || name === "照护") await page.screenshot({ path: info.outputPath(`${name}-${width}.png`), fullPage: true });
  160 |     }
  161 |   });
  162 | }
  163 | 
```