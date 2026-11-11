# CLI 命令手册

适用发行版为 2026-11-10 macOS arm64。基本形式为 `todo --json [--data-dir 目录] 命令 参数`。全局参数可放在子命令前后。所有命令均支持 `-h/--help`。下表中的 P、S 分别为父任务和子任务 ID，方括号表示可选项。

| 命令及参数 | 用途和 result 字段 |
|---|---|
| `add 标题 [创建字段]` | 创建父任务。从 `task.id` 取得新 ID。 |
| `list [-d 日期] [--deleted]` | 无日期时返回 `tasks, include_deleted`；指定日期时返回 `tasks, date`，按月历规则展示，日期模式优先于 `--deleted`。 |
| `show P [--history N]` | 父任务详情，返回 `task, history_limit`。 |
| `edit P [修改字段] [-f]` | 修改父任务，返回 `task, changed_fields`。后者列出提交的字段；状态是否实际变化看事件。 |
| `delete P [-f]` | 软删除，返回 `task, deleted`。已删除时 `deleted=false, already_deleted=true`。 |
| `undo P [-f]` | 恢复软删除的父任务，返回 `task, restored`。尚未删除时 `restored=false, not_deleted=true`。 |
| `sub add P 标题 [创建字段]` | 在 P 下新建子任务，返回 `subtask, parent_id`。 |
| `sub list P` | 返回 `task, subtasks`。JSON 包含软删除子项，展示当前子项时按 `deleted=false` 筛选。 |
| `sub show P S [--history N]` | 子任务详情，返回 `task, subtask, history_limit`。 |
| `sub edit P S [修改字段] [-f]` | 修改子任务，返回 `subtask, changed_fields`。 |
| `sub delete P S [-f]` | 软删除子项，读取 `subtask, deleted`，重复删除时检查 `already_deleted`。 |
| `sub undo P S [-f]` | 恢复子项，读取 `subtask, restored`，重复恢复时检查 `not_deleted`。 |
| `search 关键词` | 返回 `keyword, results`。跨父子任务搜索标题、背景、状态、起止日期。去空格后少于两个字符会列出所有有效项，需要在结果中再过滤。 |
| `cal [YYYY-MM]` | 默认本月，返回 `year, month, days`，每一天有 `date, tasks`。同一任务可出现在多天。 |
| `stats` | 返回有效父任务数 `total`、父任务状态分布 `by_status`、有效子任务数 `subtask_total`、今日至三天后（含）到期且仍未完成或取消的父任务 `upcoming`。 |
| `completed --from 日期 --to 日期 [--level 层级]` | 返回 `tasks`，按最近一次完成时间倒序。每行有 `task_id, level, parent_id, title, completion_count, last_completed_at`。 |
| `status-history --from 日期 --to 日期 [--level 层级] [--to-status 状态]` | 返回 `events`，按发生时间倒序。每行有 `event_id, occurred_at, task_id, level, parent_id, title, event_type, from_status, to_status`。 |

## 字段和默认值

- 创建字段为 `-s/--start`、`-e/--end`、`--status`、`-b/--background`。父、子任务的开始和截止日各自默认今天。创建未来某天的任务时同时给出起止日。起止日用 YYYY-MM-DD，截止日应大于等于开始日。
- 修改字段在创建字段基础上增加 `-t/--title`，至少提供一个字段。标题必填，最多 50 字，背景最多 500 字，创建时背景默认为空。合法状态为 `未启动`（创建默认）、`完成中`、`已完成`、`已取消`。
- `-d` 是 `--date` 的简写。`-f/--force` 在交互模式跳过确认，JSON 模式本身即为非交互。`--history N` 范围 1–50，默认 5，控制文本详情中的快照展示条数；JSON 返回完整任务及 `history_limit`，需要截取时自行取最近 N 条。
- 层级 `--level` 可取 `all`（默认）、`parent`、`subtask`；`--to-status` 取上述四种合法状态。创建即完成计一次；重开后再次完成另计一次。后来改名或软删除仍可查到原事件，事件内标题为发生时的标题。创建事件为 `created`，`from_status=null`；真实状态变化为 `changed`。只查“从某状态改到另一状态”时再筛 `from_status` 和 `event_type`。
- 按日查看时展示计划期覆盖当天的父任务，以及从开始日延续到今天的未启动或完成中父任务。其有效子项随父任务显示。按截止日回答时需另筛 `end_date`。

## 返回与失败处理

成功对象含 `ok=true, command, result`，无匹配时对应数组为空。任务的 `start_date/end_date` 表示计划期；`updated_at` 会因普通编辑改变。要回答完成时间，请读取完成事件或汇总的 `last_completed_at`。

失败时读取 stderr 中的 `error.code` 和 `error.message`。退出码 2 为用法错误，3 为校验失败，4 为对象不存在，5 为数据文件错误，6 为内部错误，130 为中断。若在 CLI 启动前即报临时目录或信号量权限错误，按当前执行环境的授权流程运行同一个随附程序。查询失败时向用户说明错误；只有成功返回的空数组才表示没有匹配记录。
