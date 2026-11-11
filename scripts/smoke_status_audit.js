// Invoked by smoke_status_audit.py inside the real Qt renderer on isolated data.
async function checkDesktop(phase) {
  const detail = () => document.querySelectorAll("aside")[1];
  const label = (name, root = document) => root.querySelector(`[aria-label="${name}"]`);
  const pause = () => new Promise(resolve => setTimeout(resolve, 20));
  async function until(check, message) {
    const deadline = Date.now() + 5000;
    while (!check()) {
      if (Date.now() > deadline) throw Error(message);
      await pause();
    }
  }
  function equal(actual, expected, message) {
    if (actual !== expected) throw Error(message + ": " + JSON.stringify({actual, expected}));
  }
  function setInput(input, value) {
    Object.getOwnPropertyDescriptor(Object.getPrototypeOf(input), "value").set.call(input, value);
    input.dispatchEvent(new Event("input", {bubbles: true}));
  }
  const title = () => detail()?.querySelector("input");
  const save = () => label("保存修改", detail()).click();
  const children = () => [...detail().querySelectorAll('[aria-label="设置子任务状态"]')];
  const hasText = text => document.body.innerText.includes(text);
  await until(() => title()?.value === "父任务", "未加载测试父任务");
  if (phase === "restart") {
    await until(() => children().length === 2, "重启后子任务数量错误");
    equal(children()[0].textContent.includes("已完成"), true, "重启后 A 状态");
    equal(children()[1].textContent.includes("未启动"), true, "重启后 B 状态");
    equal(detail().innerText.includes("子任务 B"), true, "重启后 B 标题");
    equal(detail().querySelector("textarea").value, "刷新失败前已写入", "重启后未读到保存的备注");
    return;
  }

  setInput(title(), "临时草稿");
  children()[0].click();
  await until(() => document.querySelector('[role="listbox"]'), "未打开状态菜单");
  [...document.querySelectorAll('[role="option"]')].find(el => el.textContent === "已完成").click();
  document.querySelector('[title="筛选进行"]').click();
  await pause();
  equal(title().value, "临时草稿", "筛选清除了标题草稿");
  equal(children()[0].textContent.includes("已完成"), true, "筛选清除了状态草稿");
  setInput(title(), "父任务");

  label("新增子任务").click();
  await until(() => document.querySelector('[role="dialog"] input'), "未打开创建窗口");
  setInput(document.querySelector('[role="dialog"] input'), "子任务 B");
  label("添加子任务").click();
  await until(() => children().length === 2, "B 未显示");
  const result = await window.todoBridge.request({action: "listTasks"});
  equal(result.result[0].subtasks[0].status, "完成中", "保存前 A 不应已写入");
  save();
  await until(() => hasText("修改已保存"), "首次保存未成功");
  equal(children()[0].textContent.includes("已完成"), true, "保存后 A 被还原");

  const original = window.todoBridge.request.bind(window.todoBridge);
  let failRead = true;
  let holdDate = false;
  let release;
  window.todoBridge.request = async request => {
    if (failRead && request.action === "listTasks") {
      return {ok: false, error: {code: "read_error", message: "模拟重读失败"}};
    }
    const response = await original(request);
    if (holdDate && request.action === "listTasksForDates" && request.payload.dates.length === 1) {
      holdDate = false;
      await new Promise(resolve => { release = resolve; });
    }
    return response;
  };
  setInput(detail().querySelector("textarea"), "刷新失败前已写入");
  save(); // Retry the same state. The history must still contain one completion.
  await until(() => hasText("已保存，界面刷新失败") && hasText("模拟重读失败"), "保存提示遮盖了刷新错误");
  equal(hasText("修改已保存"), false, "出现了误导的成功提示");
  failRead = false;
  label("刷新数据").click();
  await until(() => hasText("数据已刷新"), "手动刷新未恢复");

  holdDate = true;
  label("回到今天").click();
  await until(() => release, "未捕获待返回的日期请求");
  detail().querySelector('[title="设置为已完成"]').click();
  await until(() => !title() && hasText("这一天还没有任务"), "完成后筛选列表或详情未清空");
  release();
  // Wait through the released promise, React's commit, and the next paint.
  await pause();
  await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  equal(Boolean(title()), false, "旧请求恢复了已移出筛选的详情");
  equal(hasText("这一天还没有任务"), true, "旧请求恢复了列表");
}
