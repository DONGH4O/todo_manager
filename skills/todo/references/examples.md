# 发行版调用样例

以下调用均使用独立测试库。示例用 `todo` 代指技能内的可执行文件，P、S 代指前面创建的完整 ID。为便于阅读，成功样例只摘录指定结果字段，省略了长快照和重复任务对象；错误样例保留完整 JSON。

### add

输入：`todo --json add '编写周报' --status '完成中'`

```json
{"task": {"id": "9b2eb2f7-913c-4f43-9fb7-5aab5088e2e6", "title": "编写周报", "status": "完成中", "deleted": false}}
```

### sub add

输入：`todo --json sub add P '核对数据'`

```json
{"subtask": {"id": "4045def7-0de7-40b9-b870-469b9b3f0712", "title": "核对数据", "status": "未启动", "deleted": false}, "parent_id": "9b2eb2f7-913c-4f43-9fb7-5aab5088e2e6"}
```

### list

输入：`todo --json list --date 2026-11-10`

```json
{"date": "2026-11-10", "tasks": [{"id": "9b2eb2f7-913c-4f43-9fb7-5aab5088e2e6", "title": "编写周报", "status": "完成中", "deleted": false}]}
```

### show

输入：`todo --json show P --history 1`

```json
{"task": {"id": "9b2eb2f7-913c-4f43-9fb7-5aab5088e2e6", "title": "编写周报", "status": "完成中", "deleted": false}, "history_limit": 1}
```

### sub list

输入：`todo --json sub list P`

```json
{"subtasks": [{"id": "4045def7-0de7-40b9-b870-469b9b3f0712", "title": "核对数据", "status": "未启动", "deleted": false}]}
```

### sub show

输入：`todo --json sub show P S`

```json
{"subtask": {"id": "4045def7-0de7-40b9-b870-469b9b3f0712", "title": "核对数据", "status": "未启动", "deleted": false}, "history_limit": 5}
```

### search

输入：`todo --json search '核对'`

```json
{"results": [{"id": "4045def7-0de7-40b9-b870-469b9b3f0712", "title": "核对数据", "is_sub": true, "parent_id": "9b2eb2f7-913c-4f43-9fb7-5aab5088e2e6"}]}
```

### cal

输入：`todo --json cal 2026-11`

```json
{"year": 2026, "month": 11, "days": [{"date": "2026-11-10", "tasks": [{"id": "9b2eb2f7-913c-4f43-9fb7-5aab5088e2e6", "title": "编写周报", "status": "完成中", "deleted": false}]}]}
```

### stats

输入：`todo --json stats`

```json
{"total": 1, "by_status": {"完成中": 1}, "subtask_total": 1, "upcoming": [{"id": "9b2eb2f7-913c-4f43-9fb7-5aab5088e2e6", "title": "编写周报", "status": "完成中", "deleted": false}]}
```

### edit

输入：`todo --json edit P --background '周五提交'`

```json
{"task": {"id": "9b2eb2f7-913c-4f43-9fb7-5aab5088e2e6", "title": "编写周报", "status": "完成中", "deleted": false}, "changed_fields": ["background"]}
```

### sub edit

输入：`todo --json sub edit P S --status '已完成'`

```json
{"subtask": {"id": "4045def7-0de7-40b9-b870-469b9b3f0712", "title": "核对数据", "status": "已完成", "deleted": false}, "changed_fields": ["status"]}
```

下两例查询同一个子任务。第一次完成后，测试又将它重开、完成、再重开。目前状态为完成中，当天完成了 1 项、共 2 次。

### completed

输入：`todo --json completed --from 2026-11-10 --to 2026-11-10 --level subtask`

```json
{"tasks": [{"level": "subtask", "parent_id": "9b2eb2f7-913c-4f43-9fb7-5aab5088e2e6", "task_id": "4045def7-0de7-40b9-b870-469b9b3f0712", "title": "核对数据", "last_completed_at": "2026-11-10T19:10:59.053883-08:00", "completion_count": 2}]}
```

### status-history

输入：`todo --json status-history --from 2026-11-10 --to 2026-11-10 --level subtask --to-status '已完成'`

```json
{"events": [{"event_id": "19d5bded-1b8a-4a1a-8fc5-9f5b30a56998", "occurred_at": "2026-11-10T19:10:59.053883-08:00", "level": "subtask", "task_id": "4045def7-0de7-40b9-b870-469b9b3f0712", "parent_id": "9b2eb2f7-913c-4f43-9fb7-5aab5088e2e6", "title": "核对数据", "event_type": "changed", "from_status": "完成中", "to_status": "已完成"}, {"event_id": "274fcef7-454d-4034-82db-3e50b9244624", "occurred_at": "2026-11-10T19:10:58.714172-08:00", "level": "subtask", "task_id": "4045def7-0de7-40b9-b870-469b9b3f0712", "parent_id": "9b2eb2f7-913c-4f43-9fb7-5aab5088e2e6", "title": "核对数据", "event_type": "changed", "from_status": "未启动", "to_status": "已完成"}]}
```

### sub delete

输入：`todo --json sub delete P S`

```json
{"deleted": true}
```

### sub undo

输入：`todo --json sub undo P S`

```json
{"restored": true}
```

### delete

输入：`todo --json delete P`

```json
{"deleted": true}
```

### undo

输入：`todo --json undo P`

```json
{"restored": true}
```

### 非法日期

输入：`todo --json completed --from 2026-02-30 --to 2026-11-10`。退出码为 3，stderr 返回：

```json
{"ok": false, "error": {"code": "validation_error", "message": "查询开始日 格式无效或不存在: 2026-02-30"}}
```
