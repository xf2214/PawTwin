import { expect, test, type Page } from "@playwright/test";
import { login } from "./helpers";

async function family(page: Page) {
  await page.goto("/#app/home");
  await page.getByRole("button", { name: "创建本地账号", exact: true }).click();
  await page.getByLabel("账号名").fill(`pet-ui-${Date.now()}-${Math.floor(Math.random() * 99999)}`);
  await page.getByLabel("密码", { exact: true }).fill("browser-test-password");
  await page.getByLabel("昵称").fill("小屋主人");
  await page.getByRole("button", { name: "注册并登录", exact: true }).click();
  await page.getByLabel("家庭名称").fill("形象与记录家庭");
  await page.getByRole("button", { name: "创建家庭", exact: true }).click();
  await expect(page.getByRole("navigation", { name: "App 主导航" })).toBeVisible();
}

test("a saved dog's editable coat, pattern and size appear in its accessible pet avatar after refresh", async ({ page }) => {
  await login(page);
  await page.goto("/#home");
  await page.getByRole("button", { name: "＋ 添加宠物", exact: true }).click();
  const name = `小麦-${Date.now()}`;
  await page.getByLabel("名字 *", { exact: true }).fill(name);
  await page.getByLabel("种类").selectOption("dog");
  await page.getByText("像素形象与个体喜好", { exact: true }).click();
  await page.getByLabel("毛色").selectOption("black");
  await page.getByLabel("花纹").selectOption("spots");
  await page.getByLabel("形象大小").selectOption("large");
  await page.getByRole("button", { name: "确认并保存档案", exact: true }).click();
  await expect(page.getByRole("heading", { name: `${name} 的档案与物品`, exact: true })).toBeVisible();
  const avatar = page.getByRole("img", { name: `${name} 的黑色斑块狗狗像素形象`, exact: true }).first();
  await expect(avatar).toBeVisible();
  expect(await avatar.evaluate(element => element.tagName.toLowerCase())).toBe("svg");
  await expect(avatar).toHaveClass(/large/);
  await page.reload();
  await expect(page.getByRole("img", { name: `${name} 的黑色斑块狗狗像素形象`, exact: true }).first()).toBeVisible();
  const state = await (await page.request.get("/api/home/state")).json();
  expect(state.pets.find((pet: { name: string }) => pet.name === name)).toMatchObject({ species: "dog", coat: "black", pattern: "spots", size: "large" });
});

test("the embedded home has one pet selector and keeps object editing connected to family care", async ({ page }) => {
  await family(page);
  await expect(page.getByRole("navigation", { name: "小屋功能" })).toHaveCount(0);
  await expect(page.locator(".fa-petbar").getByLabel("当前宠物")).toHaveCount(1);
  await expect(page.getByRole("button", { name: "编辑档案", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "布置小屋", exact: true }).first().click();
  await page.getByLabel("物品类型").selectOption("toy");
  await page.getByLabel("名称", { exact: true }).fill("陪玩小球");
  await page.getByRole("button", { name: "添加到小屋", exact: true }).click();
  await page.getByRole("button", { name: "查看陪玩小球", exact: true }).click();
  await page.getByRole("button", { name: "安排相关照护", exact: true }).click();
  await expect(page).toHaveURL(/#app\/care$/);
  await expect(page.getByLabel("照护类型")).toHaveValue("play");
});

test("switching pets clears unsaved observation and diary fields before writing to the new pet", async ({ page }) => {
  await login(page);
  await page.goto("/#home");
  await page.getByRole("button", { name: "＋ 添加宠物", exact: true }).click();
  const name = `记录伙伴-${Date.now()}`;
  await page.getByLabel("名字 *", { exact: true }).fill(name);
  await page.getByRole("button", { name: "确认并保存档案", exact: true }).click();
  await expect(page.getByRole("heading", { name: `${name} 的档案与物品`, exact: true })).toBeVisible();
  const petSelector = page.locator(".ph-toolbar").getByLabel("当前宠物");
  const newPet = await petSelector.inputValue();
  await petSelector.selectOption("mochi");
  await page.getByRole("button", { name: "成长日记", exact: true }).click();
  await page.getByLabel("记录原文", { exact: true }).fill("属于 Mochi 的未保存观察");
  await page.getByLabel("标题", { exact: true }).fill("属于 Mochi 的未保存日记");
  await page.getByLabel("内容", { exact: true }).fill("不可自动带给另一只宠物");
  await petSelector.selectOption(newPet);
  await expect(page.getByLabel("记录原文", { exact: true })).toHaveValue("");
  await expect(page.getByLabel("标题", { exact: true })).toHaveValue("");
  await expect(page.getByLabel("内容", { exact: true })).toHaveValue("");
  await page.getByLabel("记录原文", { exact: true }).fill("新伙伴今天喜欢陪玩");
  await page.getByRole("button", { name: "保存主人记录", exact: true }).click();
  await expect(page.locator("blockquote").filter({ hasText: "新伙伴今天喜欢陪玩" })).toBeVisible();
  const state = await (await page.request.get("/api/home/state")).json();
  expect(state.notes.some((note: { pet_id: string; text: string }) => note.pet_id === newPet && note.text === "新伙伴今天喜欢陪玩")).toBe(true);
  expect(state.diary.some((diary: { pet_id: string; title: string }) => diary.pet_id === newPet && diary.title === "属于 Mochi 的未保存日记")).toBe(false);
});

for (const savingOtherPet of [false, true]) {
  test(`a late profile save ${savingOtherPet ? "cannot unlock another pet's pending observation save" : "preserves another pet's unsaved profile draft"}`, async ({ page }) => {
    await login(page);
    await page.goto("/#home");
    await page.getByRole("button", { name: "＋ 添加宠物", exact: true }).click();
    const otherName = `回执伙伴-${Date.now()}`;
    await page.getByLabel("名字 *", { exact: true }).fill(otherName);
    await page.getByRole("button", { name: "确认并保存档案", exact: true }).click();
    await expect(page.getByRole("heading", { name: `${otherName} 的档案与物品`, exact: true })).toBeVisible();
    const selector = page.locator(".ph-toolbar").getByLabel("当前宠物");
    const otherId = await selector.inputValue();
    await selector.selectOption("mochi");
    await page.getByRole("button", { name: "编辑档案", exact: true }).click();
    await page.getByText("像素形象与个体喜好", { exact: true }).click();
    const savedPreference = `已经保存，等待回执-${Date.now()}`;
    await page.getByLabel("喜欢的食物 / 互动").fill(savedPreference);

    let releaseFirst!: () => void, releaseSecond!: () => void;
    const firstGate = new Promise<void>(resolve => { releaseFirst = resolve; });
    const secondGate = new Promise<void>(resolve => { releaseSecond = resolve; });
    let firstSaved!: () => void, secondSaved!: () => void;
    const firstCommitted = new Promise<void>(resolve => { firstSaved = resolve; });
    const secondCommitted = new Promise<void>(resolve => { secondSaved = resolve; });
    await page.route("**/api/home/pets/mochi", async route => {
      // The real API commits A; only delivery of its response is delayed.
      const response = await route.fetch();
      expect(response.ok()).toBe(true);
      firstSaved();
      await firstGate;
      await route.fulfill({ response });
    });
    if (savingOtherPet) await page.route(`**/api/home/pets/${otherId}/notes`, async route => {
      const response = await route.fetch();
      expect(response.ok()).toBe(true);
      secondSaved();
      await secondGate;
      await route.fulfill({ response });
    });
    try {
      await page.getByRole("button", { name: "确认并保存档案", exact: true }).click();
      await firstCommitted;
      const committed = await (await page.request.get("/api/home/state")).json();
      expect(committed.pets.find((pet: { id: string }) => pet.id === "mochi").likes).toBe(savedPreference);
      await selector.selectOption(otherId);
      if (savingOtherPet) {
        await page.getByRole("button", { name: "成长日记", exact: true }).click();
        await page.getByLabel("记录原文", { exact: true }).fill("B 的保存仍在等待回执");
        await page.getByRole("button", { name: "保存主人记录", exact: true }).click();
        await secondCommitted;
        await expect(page.getByLabel("记录原文", { exact: true })).toBeDisabled();
      } else {
        await page.getByRole("button", { name: "编辑档案", exact: true }).click();
        await page.getByLabel("名字 *", { exact: true }).fill("B 的未保存新名字");
      }
      const firstReceived = page.waitForResponse(response => response.url().endsWith("/api/home/pets/mochi") && response.request().method() === "PUT");
      releaseFirst();
      await (await firstReceived).finished();
      await expect(selector).toHaveValue(otherId);
      if (savingOtherPet) {
        await expect(page.getByRole("button", { name: "保存主人记录", exact: true })).toBeDisabled();
        await expect(page.getByLabel("记录原文", { exact: true })).toBeDisabled();
        releaseSecond();
        await expect(page.locator("blockquote").filter({ hasText: "B 的保存仍在等待回执" })).toBeVisible();
      } else {
        await expect(page.getByLabel("名字 *", { exact: true })).toHaveValue("B 的未保存新名字");
        await expect(page.getByLabel("名字 *", { exact: true })).toBeEnabled();
      }
    } finally {
      releaseFirst();
      releaseSecond();
    }
  });
}
