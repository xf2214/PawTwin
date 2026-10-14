import { test, expect, type Page } from "@playwright/test";

async function start(page: Page) {
  await page.goto("/#app");
  await page.getByRole("button", { name: "创建本地账号", exact: true }).click();
  await page
    .getByLabel("账号名")
    .fill(`user-${Date.now()}-${Math.floor(Math.random() * 9999)}`);
  await page.getByLabel("密码", { exact: true }).fill("browser-test-password");
  await page.getByLabel("昵称").fill("试用主人");
  await page.getByRole("button", { name: "注册并登录", exact: true }).click();
  await page.getByLabel("家庭名称").fill("试用小屋");
  await page.getByRole("button", { name: "创建家庭", exact: true }).click();
  await expect(
    page.getByRole("navigation", { name: "App 主导航" }),
  ).toBeVisible();
}

test("independent account, shared navigation and refresh session", async ({
  page,
}) => {
  await start(page);
  await page.getByRole("link", { name: "产品介绍", exact: true }).click();
  await expect(page.getByRole("heading", { name: /宠物的每一天，\s*全家一起照顾。/ })).toBeVisible();
  await page.getByRole("link", { name: "进入应用", exact: true }).first().click();
  await expect(page.getByRole("navigation", { name: "App 主导航" })).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("navigation", { name: "App 主导航" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "家庭", exact: true }).click();
  await page.getByLabel("家庭称呼").fill("爸爸");
  await page.getByLabel("个人头像").selectOption("dog");
  await page.getByRole("button", { name: "保存个人设置" }).click();
  await expect(page.getByRole("status")).toContainText("已保存");
  await expect(page.getByText("本地独立账号 · 云认证未接通")).toBeVisible();
  await page.getByRole("button", { name: "生成家庭邀请" }).click();
  await expect(page.getByRole("button", { name: "撤销邀请" })).toBeVisible();
  await page.getByRole("button", { name: "撤销邀请" }).click();
  await expect(page.getByText("已撤销", { exact: true })).toBeVisible();
});

test("real weight data, weekly report and correction", async ({ page }) => {
  await start(page);
  await page.getByRole("button", { name: "成长", exact: true }).click();
  await page.getByRole("navigation", { name: "成长分区" }).getByRole("button", { name: "实测与饮食", exact: true }).click();
  await page.getByLabel("测量数值").fill("1.2");
  await page.getByLabel("测量时间").fill("2026-09-25T00:00");
  await page.getByRole("button", { name: "保存成长记录" }).click();
  await expect(
    page.getByText("1.2 kg · 主人实测", { exact: true }),
  ).toBeVisible();
  await page.getByRole("navigation", { name: "成长分区" }).getByRole("button", { name: "报告", exact: true }).click();
  await page.getByRole("button", { name: "生成周报" }).click();
  await expect(page.getByText("至少需要两次有效测量")).toBeVisible();
  await page.getByRole("navigation", { name: "成长分区" }).getByRole("button", { name: "实测与饮食", exact: true }).click();
  await page.getByRole("button", { name: "删除记录", exact: true }).click();
  await expect(page.getByText("还没有有效成长记录。")).toBeVisible();
});

test("memory confirmation shared with Alexa simulation and deletion", async ({
  page,
}) => {
  await start(page);
  await page.getByRole("button", { name: "分身", exact: true }).click();
  await page.getByLabel("偏好原文").fill("喜欢羽毛棒");
  await page.getByRole("button", { name: "保存候选记忆" }).click();
  await page.getByRole("button", { name: "确认记忆", exact: true }).click();
  await page.getByRole("link", { name: "体验 Alexa+ 网页模拟", exact: true }).click();
  await page.getByRole("button", { name: "它喜欢什么", exact: true }).click();
  await expect(page.getByRole("log", { name: "Alexa 模拟对话" })).toContainText("喜欢羽毛棒");
  await page.getByRole("navigation", { name: "App 主导航" }).getByRole("button", { name: "分身", exact: true }).click();
  await page.getByRole("button", { name: "删除记忆", exact: true }).click();
  await page.getByLabel("想了解什么").fill("它喜欢什么");
  await page.getByRole("button", { name: "询问分身", exact: true }).click();
  await expect(
    page.getByRole("article", { name: "分身回复" }),
  ).not.toContainText("喜欢羽毛棒");
});

test("care proposal needs explicit confirmation and creates manual task", async ({
  page,
}) => {
  await start(page);
  await page.getByRole("button", { name: "分身", exact: true }).click();
  await page.getByLabel("方案名称").fill("一起陪玩");
  await page.getByRole("button", { name: "建立待确认方案" }).click();
  await expect(page.getByText("一起陪玩 · 待确认")).toBeVisible();
  await page.getByRole("button", { name: "确认安排照护" }).click();
  await page.getByRole("button", { name: "照护", exact: true }).click();
  await expect(page.getByText("一起陪玩", { exact: true })).toBeVisible();
});

for (const width of [390, 1440]) {
  test(`App at ${width}px preserves room and has no horizontal overflow`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 900 });
    await start(page);
    await expect(
      page.getByRole("img", { name: /Mochi.*像素形象/ }).first(),
    ).toBeVisible();
    await page.screenshot({ path: `test-results/app-home-${width}.png`, fullPage: true });
    for (const name of ["照护", "分身", "成长", "家庭"]) {
      await page.getByRole("button", { name, exact: true }).click();
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
    }
    await page.screenshot({
      path: `test-results/family-${width}.png`,
      fullPage: true,
    });
  });
}

test("new pet selection is immediately shared with growth and delayed replies stay scoped", async ({
  page,
}) => {
  await start(page);
  await page.getByRole("button", { name: "添加宠物" }).click();
  await page.getByLabel("名字 *", { exact: true }).fill("Luna");
  let releaseSave!: () => void;
  const saveGate = new Promise<void>((resolve) => { releaseSave = resolve; });
  let confirmSaved!: (home: { pets: { id: string; name: string }[] }) => void;
  const serverSaved = new Promise<{ pets: { id: string; name: string }[] }>((resolve) => { confirmSaved = resolve; });
  await page.route("**/api/home/pets", async (route) => {
    // Save in the real backend, but hold its response until navigation unmounts
    // PetHome. The parent must receive the saved selection after that unmount.
    const response = await route.fetch();
    confirmSaved(await response.json());
    await saveGate;
    await route.fulfill({ response });
  });
  let addedPet!: { id: string; name: string };
  try {
    await page.getByRole("button", { name: "确认并保存档案" }).click();
    const saved = await serverSaved;
    addedPet = saved.pets.find((p) => p.name === "Luna")!;
    expect(addedPet).toBeTruthy();
    await page.getByRole("button", { name: "成长", exact: true }).click();
    await expect(page.getByRole("heading", { name: "成长曲线", exact: true })).toBeVisible();
  } finally {
    releaseSave();
  }
  await expect(page.locator(".fa-petbar").getByLabel("当前宠物")).toHaveValue(
    addedPet.id,
    { timeout: 1000 },
  );
  await expect(
    page.locator(".fa-petbar").getByLabel("当前宠物").locator("option:checked"),
  ).toHaveText("Luna");
  await page.getByRole("button", { name: "今日", exact: true }).first().click();
  await page.getByRole("button", { name: "编辑档案", exact: true }).click();
  await page.getByLabel("名字 *", { exact: true }).fill("Luna new");
  await page.getByLabel("预期成年体重（kg，可留空）").fill("4");
  await page.getByRole("button", { name: "确认并保存档案" }).click();
  await expect(
    page.locator(".fa-petbar").getByLabel("当前宠物").locator("option:checked"),
  ).toHaveText("Luna new");
  await page.locator(".fa-petbar").getByLabel("当前宠物").selectOption("mochi");
  await page.getByRole("button", { name: "分身", exact: true }).click();
  await page.route("**/api/family/pets/mochi/chat", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 1200));
    await route.continue();
  });
  await page.getByRole("button", { name: "询问分身", exact: true }).click();
  await page
    .locator(".fa-petbar")
    .getByLabel("当前宠物")
    .selectOption({ label: "Luna new" });
  await expect(
    page.getByRole("heading", { name: "Luna new 的个体分身" }),
  ).toBeVisible();
  await page.waitForTimeout(1700);
  await expect(page.getByRole("article", { name: "分身回复" })).toHaveCount(0);
  await page.getByRole("button", { name: "家庭", exact: true }).click();
  await page.getByText("宠物资料管理", { exact: true }).click();
  await page.getByRole("button", { name: "归档 Luna new" }).click();
  await expect(page.locator(".fa-petbar").getByLabel("当前宠物")).toHaveValue(
    "mochi",
  );
  await page.getByRole("button", { name: "恢复 Luna new" }).click();
  await expect(
    page.locator(".fa-petbar option").filter({ hasText: /^Luna new$/ }),
  ).toHaveCount(1);
});

test("owner observation and diary can be corrected and removed from shared context", async ({
  page,
}) => {
  await start(page);
  await page.getByRole("button", { name: "成长", exact: true }).click();
  await page.getByRole("button", { name: "照片日记与主人观察" }).click();
  await page.getByLabel("记录原文").fill("只喜欢羽毛棒");
  await page.getByLabel("适用范围").selectOption("preference");
  await page.getByRole("button", { name: "保存主人记录" }).click();
  const management = page.getByRole("region", { name: "观察与日记管理" });
  await management.getByText("纠正观察", { exact: true }).click();
  await management.getByLabel("修订观察原文").fill("喜欢小球");
  await management.getByRole("button", { name: "保存观察修订" }).click();
  await expect(
    management.locator("strong").filter({ hasText: /^喜欢小球$/ }),
  ).toBeVisible();
  await page.getByLabel("标题", { exact: true }).fill("今天很开心");
  await page.getByRole("button", { name: "保存日记", exact: true }).click();
  await management.getByText("纠正日记", { exact: true }).click();
  await management.getByLabel("修订日记标题").fill("今天休息");
  await management.getByRole("button", { name: "保存日记修订" }).click();
  await expect(
    management.locator("strong").filter({ hasText: /^今天休息$/ }),
  ).toBeVisible();
  await page.getByRole("button", { name: "分身", exact: true }).click();
  await page.getByLabel("想了解什么").fill("喜欢什么");
  await page.getByRole("button", { name: "询问分身", exact: true }).click();
  await expect(page.getByRole("article", { name: "分身回复" })).toContainText(
    "喜欢小球",
  );
  await expect(
    page.getByRole("article", { name: "分身回复" }),
  ).not.toContainText("只喜欢羽毛棒");
  await page.getByRole("button", { name: "成长", exact: true }).click();
  await page.getByRole("button", { name: "照片日记与主人观察" }).click();
  await management.getByText("纠正观察", { exact: true }).click();
  await management.getByRole("button", { name: "删除观察" }).click();
  await expect(
    management.locator("strong").filter({ hasText: /^喜欢小球$/ }),
  ).toHaveCount(0);
});
