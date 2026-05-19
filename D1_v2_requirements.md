# D1 v2 需求文档 — 核心数据引擎（含二级子任务）

> 版本：v2.0  
> 创建日期：2026-04-30  
> 状态：待确认

---

## 1. 变更概述

在 D1 v1（基础 CRUD + 历史快照 + 软删除 + 日历展示）之上，新增 **二级子任务** 支持。

### 核心设计决策

| 决策点 | 结论 |
|--------|------|
| 存储结构 | 子任务 **嵌套** 在主任务内（`Task.subtasks: List[SubTask]`），JSON 中直接嵌入 |
| 嵌套层级 | **仅一级**（父 → 子），子任务不可再挂子任务 |
| 日历展示 | 子任务**完全依附**父任务：父任务被展示 → 其下所有未删除子任务一并展示；子任务不可独立出现 |
| 父删除级联 | 父任务软删除后，子任务跟随隐藏（通过日历查询逻辑自动实现，无需单独标记） |
| 字段约束 | 子任务沿用与主任务**完全一致**的校验规则 |

---

## 2. 数据模型

### 2.1 SubTask（新增）

```python
@dataclass
class SubTask:
    id: str                        # UUID，自动生成
    title: str                     # ≤ 50 字符，必填
    start_date: str                # YYYY-MM-DD
    end_date: str                  # YYYY-MM-DD，必须 ≥ start_date
    status: str                    # 未启动 / 完成中 / 已完成 / 已取消
    background: str                # ≤ 500 字符
    deleted: bool = False          # 软删除标记
    created_at: str = ""           # ISO 8601
    updated_at: str = ""           # ISO 8601
    history: List[VersionRecord] = field(default_factory=list)  # 独立历史快照
```

SubTask **复用** `VersionRecord` 作为历史快照（字段完全一致），但拥有自己独立的 `history` 数组。

### 2.2 Task（修改）

```python
@dataclass
class Task:
    # ── 以下字段不变 ──
    id: str
    title: str
    start_date: str
    end_date: str
    status: str
    background: str
    deleted: bool = False
    created_at: str = ""
    updated_at: str = ""
    history: List[VersionRecord] = field(default_factory=list)

    # ── 新增 ──
    subtasks: List[SubTask] = field(default_factory=list)
```

### 2.3 JSON 存储格式

```json
{
  "version": 2,
  "tasks": [
    {
      "id": "c60f1a2b-...",
      "title": "Q2 原型开发",
      "start_date": "2026-05-01",
      "end_date": "2026-05-15",
      "status": "完成中",
      "background": "完成高保真原型",
      "deleted": false,
      "created_at": "2026-04-30T21:00:00+08:00",
      "updated_at": "2026-04-30T21:00:00+08:00",
      "history": [
        {
          "version": 1,
          "title": "Q2 原型开发",
          "start_date": "2026-05-01",
          "end_date": "2026-05-15",
          "status": "未启动",
          "background": "完成高保真原型",
          "changed_at": "2026-04-30T21:00:00+08:00"
        }
      ],
      "subtasks": [
        {
          "id": "a3f5b7c1-...",
          "title": "需求评审",
          "start_date": "2026-05-01",
          "end_date": "2026-05-03",
          "status": "已完成",
          "background": "",
          "deleted": false,
          "created_at": "2026-04-30T21:05:00+08:00",
          "updated_at": "2026-04-30T21:05:00+08:00",
          "history": [
            {
              "version": 1,
              "title": "需求评审",
              "start_date": "2026-05-01",
              "end_date": "2026-05-03",
              "status": "未启动",
              "background": "",
              "changed_at": "2026-04-30T21:05:00+08:00"
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 3. API 变更

### 3.1 新增 API

#### `create_subtask(task_id, title, start_date, end_date, status, background) -> SubTask`

在指定主任务下新建子任务。

- 自动生成 `id`（UUID）、`created_at`、`updated_at`
- 写入 `history[0]` 作为初始版本快照
- **校验规则**与 `create_task` 完全一致
- `subtasks` 列表无数量限制

**Raises:**
- `ValueError`：父任务不存在、父任务已删除、字段校验失败

---

#### `get_subtask(task_id, subtask_id) -> Optional[SubTask]`

按父任务 ID + 子任务 ID 查询子任务。

- 返回完整的 SubTask 对象（含 history）
- 不存在返回 `None`
- 父任务不存在返回 `None`

---

#### `update_subtask(task_id, subtask_id, **kwargs) -> SubTask`

更新子任务字段。

- 支持**部分字段更新**（只传变更字段）
- 更新前将当前字段快照推入 `history`
- 自动刷新 `updated_at`
- 修改父任务（Task 级别）的字段**不应**触发此函数

**Raises:**
- `ValueError`：父任务不存在、父任务已删除、子任务不存在、子任务已删除、字段校验失败

---

#### `delete_subtask(task_id, subtask_id) -> bool`

软删除子任务（`deleted = True`），不删除数据和历史。

**Returns:**
- `True`：删除成功
- `False`：父任务或子任务不存在

---

### 3.2 修改的 API

#### `get_tasks_for_date(date_str) -> List[Task]`

**原逻辑（不变）：**

> `T.deleted == False AND (date 在 [T.start_date, T.end_date] 区间内 OR T.status NOT IN ("已完成", "已取消"))`

**新增行为：**

当父任务被判定展示时，其 `subtasks` 列表中 `deleted=False` 的子任务一并随 Task 对象返回。子任务自身的时间范围和状态**不影响**

- 是否展示 —— 仅由父任务决定。

**实现方式：**

返回的 Task 对象中，`subtasks` 已过滤掉 `deleted=True` 的项，调用方无需再次过滤。

---

### 3.3 不受影响的 API

| API | 变化 |
|-----|------|
| `create_task(title, ...)` | 无变化（`subtasks` 默认为空列表） |
| `get_task(task_id)` | 无变化（返回的 Task 包含 `subtasks`，不做过滤） |
| `update_task(task_id, **kwargs)` | 不支持修改 `subtasks`，子任务有独立 API |
| `delete_task(task_id)` | 仅修改父任务 `deleted=True`，子任务 `deleted` 不变。日历查询时父任务不展示 → 子任务也不展示 |
| `list_all_tasks(include_deleted)` | 无变化（子任务嵌套在 Task 内，不扁平化） |

---

## 4. 校验规则（与主任务完全一致）

| 字段 | 规则 |
|------|------|
| `title` | 必填，≤ 50 字符，自动 trim |
| `start_date` | YYYY-MM-DD 格式，必须为有效日期 |
| `end_date` | YYYY-MM-DD 格式，必须 ≥ start_date |
| `status` | 枚举：`未启动`, `完成中`, `已完成`, `已取消` |
| `background` | ≤ 500 字符 |

---

## 5. 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `engine/models.py` | **修改** | 新增 `SubTask` dataclass；`Task` 新增 `subtasks` 字段；`to_dict()` / `from_dict()` 支持嵌套序列化 |
| `engine/task_manager.py` | **修改** | 新增 `create_subtask`, `get_subtask`, `update_subtask`, `delete_subtask`；修改 `get_tasks_for_date()` 过滤子任务 |
| `engine/storage.py` | **修改** | `version` 字段 1 → 2（JSON 向后兼容，v1 数据自动升级） |
| `engine/calendar_utils.py` | **不变** | 日期计算逻辑无变化 |
| `tests/test_task_manager.py` | **修改** | 新增子任务 CRUD 测试类（含边界和异常路径）；新增子任务日历展示测试；修复现有测试中缺少 `subtasks` 默认值的问题 |
| `tests/test_models.py` | **修改** | 新增 `SubTask` / `VersionRecord` 序列化测试；`Task` 序列化测试增加子任务场景 |
| `tests/test_storage.py` | **修改** | 新增含子任务的存储/读取测试 |

---

## 6. 向后兼容

- JSON `version` 由 1 升为 2
- 加载 v1 数据时，`subtasks` 字段缺失 → 自动设为空列表 `[]`
- v1 创建的任务可正常与新版本代码一起使用

---

## 7. 测试覆盖 (预计)

| 类别 | 测试点 | 预计用例数 |
|------|--------|----------|
| SubTask 创建 | 正常创建、父任务不存在、父任务已删除、字段校验失败 | 7 |
| SubTask 查询 | 正常查询、子任务不存在、父任务不存在 | 3 |
| SubTask 更新 | 部分字段更新、全字段更新、快照推入 history、子任务已删除、校验失败 | 8 |
| SubTask 删除 | 正常删除、重复删除、不存在、父任务不存在 | 4 |
| 日历展示 | 父任务展示时子任务出现、deleted 子任务不出现、父任务不展示时子任务不出现 | 4 |
| 模型序列化 | SubTask ↔ dict、Task 含子任务 ↔ JSON | 3 |
| 向后兼容 | v1 数据加载后 subtasks 为空列表 | 1 |
| **合计** | | **~30** |

加上 v1 已有的 66 条测试，预计总计约 **96 条测试**。

---

> **此文档等待用户确认后进入实现阶段。**
