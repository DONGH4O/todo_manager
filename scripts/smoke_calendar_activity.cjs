// Run after build:desktop with Playwright and Chromium available to Node.
// The browser uses a fresh, isolated preview store. No desktop data is opened.
const { chromium } = require("playwright");
const assert = require("node:assert/strict");
const path = require("node:path");

async function run() {
  const browser = await chromium.launch({ executablePath: process.env.CHROME_BIN });
  try {
    const page = await browser.newPage({ timezoneId: "America/Los_Angeles" });
    page.setDefaultTimeout(15000);
    const output = path.resolve(__dirname, "../frontend/out");
    await page.route("**/*", async (route) => {
      const url = new URL(route.request().url());
      if (url.hostname !== "todo.test") return route.abort();
      const resource = url.pathname === "/" ? "index.html" : url.pathname.slice(1);
      await route.fulfill({ path: path.join(output, resource) });
    });
    await page.clock.install({ time: new Date("2026-11-30T23:59:15-08:00") });
    await page.addInitScript(() => {
      const fields = { title: "跨日验收", start_date: "2026-11-01", end_date: "2026-11-03",
        background: "", status: "完成中" };
      localStorage.setItem("todo-manager-preview-tasks", JSON.stringify([
        { ...fields, id: "parent", subtasks: [{ ...fields, id: "child", title: "子任务" }] }
      ]));
    });
    await page.goto("http://todo.test/");
    const detail = page.locator('aside').last();
    const title = detail.getByLabel("标题", { exact: true });
    await title.fill("尚未保存");
    await page.getByRole("button", { name: "新建任务", exact: true }).click();
    const dialog = page.getByRole("dialog");
    await dialog.locator("input").first().fill("新建草稿");
    await page.clock.setSystemTime(new Date("2026-12-01T00:00:00-08:00"));
    await page.clock.runFor(31000);
    const cell = (date) => page.getByRole("button", { name: "查看 " + date, exact: true });
    const selected = (date) => page.locator('[aria-label="查看 ' + date + '"].shadow-focus');
    assert.match(await cell("2026-12-01").getAttribute("class"), /linear-gradient/);
    assert.equal(await selected("2026-11-30").count(), 1);
    assert.equal(await page.getByLabel("选择月份").inputValue(), "10");
    assert.equal(await dialog.locator("input").first().inputValue(), "新建草稿");
    await dialog.getByRole("button", { name: "取消", exact: true }).click();
    assert.equal(await title.inputValue(), "尚未保存");
    // An overdue ongoing task now extends to December 1.
    await cell("2026-12-01").getByText("跨日验收").waitFor();
    await page.clock.setSystemTime(new Date("2026-12-02T08:00:00-08:00"));
    await page.evaluate(() => window.dispatchEvent(new Event("focus")));
    assert.match(await cell("2026-12-02").getAttribute("class"), /linear-gradient/);
    await page.getByRole("button", { name: "回到今天" }).click();
    await selected("2026-12-02").waitFor();
    assert.equal(await page.getByLabel("选择月份").inputValue(), "11");
    await page.waitForFunction(() => document.querySelector('aside:last-of-type input')?.value === "跨日验收");
    await detail.getByLabel("设置子任务状态").click();
    await page.getByRole("option", { name: "已完成" }).click();
    await detail.getByLabel("保存修改").click();
    await page.getByText("修改已保存", { exact: true }).waitFor();
    assert.equal(await selected("2026-12-02").count(), 1);
    assert.match(await detail.getByLabel("设置子任务状态").textContent(), /已完成/);
    await detail.getByTitle("设置为已完成").click();
    await detail.getByText("选中任务后编辑").waitFor();
    assert.equal(await selected("2026-12-02").count(), 1);
    await page.getByLabel("刷新数据").click();
    await page.getByText("数据已刷新").waitFor();
    assert.equal(await selected("2026-12-02").count(), 1);
    // On the scheduled date the completed task remains until filtered out.
    await page.getByText("数据已刷新").waitFor({ state: "hidden" });
    await page.getByLabel("上个月").click();
    await page.getByLabel("刷新数据").click();
    await cell("2026-11-03").click();
    await page.getByText("数据已刷新").waitFor();
    await title.waitFor();
    await page.getByTitle("筛选进行").click();
    await detail.getByText("选中任务后编辑").waitFor();
    assert.equal(await selected("2026-11-03").count(), 1);
    console.log("Calendar rollover, wake, drafts, status saves, filters and refresh passed.");
  } finally {
    await browser.close();
  }
}
run().catch((error) => { console.error(error); process.exitCode = 1; });
