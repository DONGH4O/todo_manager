# Todo Manager CLI 契约

> 版本：v0.1  
> 日期：2026-05-19  
> 对应里程碑：M3 CLI agent 契约

## 1. 入口与全局参数

源码入口：

```powershell
python -m todo_manager.cli <command> [args...]
```

安装后入口：

```powershell
todo <command> [args...]
```

全局参数：

- `--data-dir <path>`：指定数据目录。
- `--json`：启用机器可读 JSON 输出。

全局参数可以放在命令前或命令后。以下两种写法等价：

```powershell
todo --data-dir C:\tmp\todo-data --json stats
todo stats --json --data-dir C:\tmp\todo-data
```

## 2. 输出规则

- 成功结果写入 stdout。
- 错误和诊断信息写入 stderr。
- JSON 模式下，stdout 只包含一个成功 JSON 对象。
- JSON 模式下，stderr 只包含一个错误 JSON 对象。
- 文本模式保持面向人类的中文表格和提示。
- JSON 模式为非交互模式；`edit`、`delete`、`undo`、`sub edit`、`sub delete`、`sub undo` 不弹确认输入，直接执行命令。

建议 agent 始终显式传入：

```powershell
todo --json --data-dir <agent-data-dir> <command> ...
```

## 3. 退出码

| 退出码 | code | 含义 |
|---|---|---|
| 0 | success | 成功 |
| 2 | usage_error | 参数或命令用法错误 |
| 3 | validation_error | 字段校验失败，例如标题为空、日期无效、状态无效 |
| 4 | not_found | 任务或子任务不存在 |
| 5 | data_file_error | 数据文件读取或结构错误，例如损坏 JSON |
| 6 | internal_error | 未预期内部错误或写入异常 |
| 130 | internal_error | 用户中断 |

## 4. JSON 成功 schema

所有成功响应使用统一 envelope：

```json
{
  "ok": true,
  "command": "add",
  "result": {}
}
```

常见 `result` 形状：

- `add`：`{"task": <task>}`
- `list`：`{"tasks": [<task>], "include_deleted": false}` 或 `{"date": "YYYY-MM-DD", "tasks": [<task>]}`
- `show`：`{"task": <task>, "history_limit": 5}`
- `edit`：`{"task": <task>, "changed_fields": ["status"]}`
- `delete`：`{"deleted": true, "task": <task>}`
- `undo`：`{"restored": true, "task": <task>}`
- `sub add`：`{"subtask": <subtask>, "parent_id": "<task-id>"}`
- `sub list`：`{"task": <task>, "subtasks": [<subtask>]}`
- `sub show`：`{"task": <task>, "subtask": <subtask>, "history_limit": 5}`
- `sub edit`：`{"subtask": <subtask>, "changed_fields": ["status"]}`
- `sub delete`：`{"deleted": true, "subtask": <subtask>}`
- `sub undo`：`{"restored": true, "subtask": <subtask>}`
- `cal`：`{"year": 2026, "month": 5, "days": [{"date": "2026-05-19", "tasks": [<task>]}]}`
- `search`：`{"keyword": "关键字", "results": [<flat-task>]}`
- `stats`：`{"total": 1, "by_status": {"未启动": 1}, "subtask_total": 0, "upcoming": [<task>]}`

## 5. JSON 错误 schema

所有错误响应使用统一 envelope：

```json
{
  "ok": false,
  "error": {
    "code": "validation_error",
    "message": "任务标题不能为空"
  }
}
```

可选字段：

```json
{
  "ok": false,
  "error": {
    "code": "internal_error",
    "message": "命令执行失败",
    "details": {
      "type": "RuntimeError"
    }
  }
}
```

## 6. 数据模型摘要

`task`：

```json
{
  "id": "uuid",
  "title": "任务标题",
  "start_date": "2026-05-19",
  "end_date": "2026-05-20",
  "status": "未启动",
  "background": "",
  "deleted": false,
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "history": [],
  "subtasks": []
}
```

`subtask` 字段与 `task` 基本一致，但不包含 `subtasks`。

合法状态：

- `未启动`
- `完成中`
- `已完成`
- `已取消`

`flat-task` 用于 `search`：

```json
{
  "id": "uuid",
  "title": "任务标题",
  "start_date": "2026-05-19",
  "end_date": "2026-05-20",
  "status": "未启动",
  "background": "",
  "created_at": "ISO-8601",
  "deleted": false,
  "is_sub": false,
  "parent_id": null,
  "parent_title": null,
  "parent_start_date": null
}
```

## 7. Agent 调用示例

创建任务：

```powershell
todo --json --data-dir C:\tmp\todo-agent add "写周报" -s 2026-05-19 -e 2026-05-19 --status 未启动
```

查询任务：

```powershell
todo --json --data-dir C:\tmp\todo-agent list
todo --json --data-dir C:\tmp\todo-agent show <task-id>
```

编辑任务：

```powershell
todo --json --data-dir C:\tmp\todo-agent edit <task-id> --status 完成中
```

删除并撤销：

```powershell
todo --json --data-dir C:\tmp\todo-agent delete <task-id>
todo --json --data-dir C:\tmp\todo-agent undo <task-id>
```

子任务：

```powershell
todo --json --data-dir C:\tmp\todo-agent sub add <task-id> "补充数据" -s 2026-05-19 -e 2026-05-19
todo --json --data-dir C:\tmp\todo-agent sub list <task-id>
```

错误处理建议：

1. 先看进程退出码。
2. 若退出码非 0，解析 stderr 中的 JSON。
3. 按 `error.code` 分支处理。
4. `data_file_error` 时不要继续写入同一数据目录，先提示用户处理备份和原文件。
