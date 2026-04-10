# AINEWS 自动化流程说明

本文档只描述当前运行中的自动化链路。

## 总览

系统启动后会同时运行两个后台循环：

1. `scheduler_loop`
   负责按爬虫配置定时启动抓取任务。

2. `auto_pipeline_loop`
   负责在工作时间内串行推进内容处理。

工作时间判断来自系统时区配置，默认窗口为北京时间 08:00 到 24:00。非工作时间不会继续跑自动处理链路。

## 自动处理链路

`auto_pipeline_loop` 的实际执行顺序如下：

1. 等待当前抓取任务结束
2. 对 `news` 中的 `news` 类型内容做自动去重
3. 对 `news` 中的 `article` 类型内容做自动去重
4. 对 `archive_entries` 做黑名单拦截
5. 对 `review_entries` 的待审核内容执行 AI 审核
6. 将已选入且待发送的内容推送到 Telegram

这条链路对应的实现入口在 [backend/main.py](E:/Work/Code/AINEWS/backend/main.py) 和 [automation_runtime_service.py](E:/Work/Code/AINEWS/backend/app/services/automation_runtime_service.py)。

## 步骤 1：抓取与入池

爬虫抓到的新内容先写入 `news` 表。

- `news.stage = incoming`
- `news.type` 标识内容类型，当前使用 `news` 和 `article`
- 这一步只负责采集，不做归档、审核或推送

## 步骤 2：自动去重

自动去重会读取 `news` 中最近时间窗口内、仍可处理的内容，并给出两类结果：

1. 非重复内容
   直接写入 `archive_entries`，同时把 `news.stage` 更新为 `archived`

2. 重复内容
   保留在 `news`，并更新为：
   - `stage = duplicate`
   - `duplicate_of = <主内容 ID>`
   - `is_local_duplicate = 1`

这一步不会再创建额外的“中间池”表，归档池就是去重后的唯一落点。

## 步骤 3：黑名单拦截

黑名单处理只操作 `archive_entries` 中 `archive_status = ready` 的内容。

处理结果只有两种：

1. 命中黑名单
   - `archive_status = blocked`
   - 记录 `block_reason`

2. 未命中黑名单
   - 写入 `review_entries`
   - `review_status = pending`
   - 同时把归档记录改为 `archive_status = reviewed`

这一步的职责是把“可继续审核的内容”从归档池推进到审核池，而不是在多个临时表之间来回复制。

## 步骤 4：AI 审核

AI 审核只处理 `review_entries` 中 `review_status = pending` 的内容。

审核结果写回同一张表：

- 通过：`review_status = selected`
- 不通过：`review_status = discarded`

同时补充以下字段：

- `review_reason`
- `review_score`
- `review_category`
- `review_summary`
- `review_tags`

也就是说，审核前后的内容都留在同一个审核池中，只通过 `review_status` 区分阶段。

## 步骤 5：Telegram 实时发送

自动发送读取 `review_entries` 中满足以下条件的内容：

- `review_status = selected`
- `delivery_status = pending`
- 在最近时间窗口内

发送成功后：

- `delivery_status = sent`
- `delivered_at` 写入时间
- `push_logs` 记录发送日志

发送失败时不会把内容移出审核池，只会留下失败日志，后续仍可重新处理。

## 每日日报

每日日报不是 `auto_pipeline_loop` 默认每小时都会执行的步骤，它由专门的发送接口触发：

- `POST /api/delivery/daily/news`
- `POST /api/delivery/daily/article`

日报生成逻辑会：

1. 从 `review_entries` 读取最近 24 小时内已选入的内容
2. 按分数和链接去重整理成日报正文
3. 发送到 Telegram
4. 将最终结果写入 `daily_reports`

因此，`daily_reports` 是日报的唯一存储位置，不是实时发送队列。

## 运行中会看到的核心状态

### `news.stage`

- `incoming`
- `archived`
- `duplicate`

### `archive_entries.archive_status`

- `ready`
- `blocked`
- `reviewed`

### `review_entries.review_status`

- `pending`
- `selected`
- `discarded`

### `review_entries.delivery_status`

- `pending`
- `sent`

## 数据流简图

```text
news (incoming)
    ↓ 去重
news (archived | duplicate)
    ↓
archive_entries (ready)
    ↓ 黑名单拦截
archive_entries (blocked | reviewed)
    ↓
review_entries (pending)
    ↓ AI 审核
review_entries (selected | discarded)
    ↓ Telegram 实时发送
review_entries (delivery_status = sent)
    ↓ 手动触发日报
daily_reports
```

## 判断自动流程是否正常的最小检查点

1. `news` 是否持续写入新内容
2. `archive_entries` 是否出现新的 `ready` 或 `reviewed` 记录
3. `review_entries` 是否出现新的 `pending / selected / discarded`
4. `push_logs` 是否持续记录发送结果
5. `daily_reports` 是否在触发日报后产生新记录
