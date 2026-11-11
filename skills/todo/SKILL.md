---
name: todo
description: 使用本机 Todo Manager 管理待办、父任务和子任务，查询日历、期间完成清单和状态变化。适用于用户要求操作 Todo Manager 或显式调用 $todo 时。
---

# Todo Manager

使用本技能随附的 macOS arm64 发行版 CLI。下文的 `todo` 指本 SKILL.md 所在目录下的 `scripts/todo`。全局安装后通常为 `"${CODEX_HOME:-$HOME/.codex}/skills/todo/scripts/todo"`。调用时传 `--json`。默认使用桌面 APP 的任务库，跨项目共用；用户指定 `--data-dir` 时整次操作使用同一目录。

## 按问题选命令

| 用户想知道或执行什么 | 选择 |
|---|---|
| “今天安排了什么？”“下个月日历上有什么？” | 一天用 `list --date`，整月用 `cal`。逾期且仍在进行的任务可以继续显示。 |
| “现在有哪些已完成的任务？” | `list` 后筛选当前 `status`。需要含子任务时遍历 `subtasks`，排除已删除项。只问父任务各状态数量时用 `stats`。 |
| “本周完成过哪些任务？”“一共完成多少项、多少次？” | `completed --from … --to …`。项数取结果行数，次数累加 `completion_count`。同一任务完成后重开仍计入。 |
| “本周哪些任务改成了完成中？”“这个任务何时反复完成？” | `status-history --from … --to … --to-status 状态`。查看所有状态时省略状态参数。查某项时在结果中匹配 `task_id`，子任务同时核对 `parent_id`。 |
| “找一下周报”“看这个任务的详情和以前的修改” | 标题或描述定位用 `search`，根据 `is_sub` 和 ID 选 `show` 或 `sub show`。字段修改快照在 `history`，状态变化时间在 `status_events`。 |
| 新建、修改、标记完成、取消、删除、恢复 | 先确定层级。父任务用 `add/edit/delete/undo`，子任务用 `sub add/edit/delete/undo`。标记完成或取消用 `edit --status`；重开用 `edit --status 完成中`（按用户指定的目标状态调整）；`undo` 用于恢复误删项。 |

把“今天”“上周”等换算为设备本地日期。期间查询包含首尾两天，仅能回溯升级后记录的状态事件。当前状态与期间事件可能同时符合用户的问法且会给出不同答案时，先厘清他问的是哪一种。

写入时使用查询或创建返回的完整 ID；同名且上下文无法区分时再问。JSON 模式写操作直接生效。按用户要求的字段提交修改，写入结果不明时先查询核实，尤其是创建操作。成功读取 stdout 的 `result`，错误读取 stderr 和退出码。

查具体参数、默认值、返回字段和错误处理时读 [CLI 命令手册](references/cli.md)。查实际输入与输出时读 [发行版调用样例](references/examples.md)。
