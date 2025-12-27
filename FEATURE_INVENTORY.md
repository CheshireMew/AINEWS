# AINEWS 项目功能清单

> **生成时间**：2024-12-26  
> **最后更新**：2024-12-27  
> **基于重构后的组件结构**  
> **用途**：代码重构和功能验证的参考基线

---

## 📁 文件结构概览

### 主文件
- `Dashboard.jsx` (566 行) - 主控制面板

### Tab 组件（9个）
1. `NewsManagementTab.jsx` (195 行) - 数据管理
2. `DeduplicatedTab.jsx` (201 行) - 去重数据  
3. `FilterSettingsTab.jsx` (316 行) - 过滤设置
4. `CuratedNewsTab.jsx` (155 行) - 精选数据
5. `AIFilterTab.jsx` (380 行) - AI 筛选
6. `AIBestTab.jsx` (158 行) - AI 精选
7. `ExportTab.jsx` (236 行) - 新闻输出
8. `SpiderControlTab.jsx` (35 行) - 爬虫控制
9. `ScraperCard.jsx` (162 行) - 爬虫卡片

### 辅助组件
- `NewsToolbar.jsx` (90 行) - 通用新闻工具栏
- `NewsExpandedView.jsx` (35 行) - 新闻展开视图
- `TimeRangeSelect.jsx` (42 行) - 通用时间范围选择器

---

## 🎛️ Dashboard.jsx - 主控制面板

### 状态变量

| 变量名 | 类型 | 初始值 | 用途 | 行号 |
|--------|------|--------|------|------|
| stats | Object | {} | 统计数据 | L32 |
| news | Array | [] | 原始新闻列表 | L33 |
| pagination | Object | {current:1, pageSize:20, total:0} | News分页 | L34 |
| dedupNews | Array | [] | 去重新闻列表 | L35 |
| dedupPagination | Object | {current:1, pageSize:20, total:0} | 去重分页 | L36 |
| filteredNews | Array | [] | 已过滤新闻 | L37 |
| filteredPagination | Object | {current:1, pageSize:20, total:0} | 过滤分页 | L38 |
| curatedNews | Array | [] | 精选新闻 | L39 |
| curatedPagination | Object | {current:1, pageSize:20, total:0} | 精选分页 | L40 |
| rejectedNews | Array | [] | AI拒绝新闻 | L41 |
| rejectedPagination | Object | {current:1, pageSize:20, total:0} | 拒绝分页 | L42 |
| approvedNews | Array | [] | AI批准新闻 | L43 |
| approvedPagination | Object | {current:1, pageSize:20, total:0} | 批准分页 | L44 |
| spiders | Array | [] | 爬虫列表 | L45 |
| spiderStatus | Object | {} | 爬虫状态 | L46 |
| globalCounts | Object | {news:0, dedup:0, filtered:0, curated:0, aiFilter:0, aiBest:0} | 全局计数 | L47-54 |
| manuallyFeatured | Array | [] | 手动加精列表 | L55 |
| activeTab | String | '1' | 当前激活Tab | L57 |
| exportVisible | Boolean | false | 导出对话框 | L58 |
| exportStage | String | 'raw' | 导出阶段 | L59 |

### 核心功能函数

| 函数名 | 功能 | 参数 | 行号 |
|--------|------|------|------|
| handleAddToFeatured | 添加到加精列表 | record | L69-80 |
| fetchStats | 获取统计数据 | - | L82-89 |
| fetchNews | 获取原始新闻 | page, source | L91-106 |
| fetchDedupNews | 获取去重新闻 | page, source | L108-123 |
| fetchSpiders | 获取爬虫列表 | - | L125-132 |
| fetchSpiderStatus | 获取爬虫状态 | - | L146-153 |
| handleLogout | 退出登录 | - | L159-162 |
| fetchGlobalCounts | 获取全局计数 | - | L174-198 |
| handleRunSpider | 启动爬虫 | name, items | L207-217 |
| handleStopSpider | 停止爬虫 | name | L219-226 |
| handleConfigChange | 修改爬虫配置 | name, changes | L228-237 |
| fetchFilteredNews | 获取已过滤新闻 | page | L255-271 |
| fetchCuratedNews | 获取精选新闻 | page, source | L273-288 |
| fetchRejectedNews | 获取AI拒绝新闻 | page | L298-313 |
| fetchApprovedNews | 获取AI批准新闻 | page | L314-329 |
| handleShowExport | 显示导出对话框 | defaultStage | L343-348 |
| handleExport | 执行导出 | - | L350-386 |

### 生命周期 Hooks

| Hook | 依赖 | 功能 | 行号 |
|------|------|------|------|
| useEffect | [] | 初始加载（爬虫列表、统计） | L134-144 |
| useEffect | [] | 定时刷新爬虫状态（10秒） | L155-157 |
| useEffect | [] | 定时刷新全局计数（30秒） | L200-205 |

### Tab 配置

| Tab Key | Tab 名称 | 组件 | 行号 |
|---------|----------|------|------|
| '1' | 数据管理 | NewsManagementTab | L442-449 |
| '3' | 去重数据 | DeduplicatedTab | L450-457 |
| '4' | 过滤设置 | FilterSettingsTab | L458-462 |
| '5' | 精选数据 | CuratedNewsTab | L463-470 |
| '8' | AI 筛选 | AIFilterTab | L471-475 |
| '9' | AI 精选 | AIBestTab | L476-483 |
| '10' | 新闻输出 | ExportTab | L484-486 |
| '7' | 爬虫控制 | SpiderControlTab | L487-495 |

### Props 传递矩阵

| 组件 | Props | 行号 |
|------|-------|------|
| NewsManagementTab | onAddToFeatured, spiders, onShowExport | L442-449 |
| DeduplicatedTab | spiders, onAddToFeatured, onShowExport | L450-457 |
| FilterSettingsTab | onAddToFeatured | L458-462 |
| CuratedNewsTab | spiders, onAddToFeatured, onShowExport | L463-470 |
| AIFilterTab | onAddToFeatured | L471-475 |
| AIBestTab | spiders, onAddToFeatured, onShowExport | L476-483 |
| ExportTab | manuallyFeatured | L484-486 |
| SpiderControlTab | spiders, spiderStatus, onRunSpider, onCancelSpider, onUpdateConfig | L487-495 |

---

## 📰 Tab 1: NewsManagementTab - 数据管理

### 状态变量

| 变量名 | 类型 | 初始值 | 用途 | 行号 |
|--------|------|--------|------|------|
| news | Array | [] | 新闻列表 | L13 |
| pagination | Object | {current:1, pageSize:20, total:0} | 分页状态 | L14 |
| loading | Boolean | false | 加载状态 | L15 |
| filterSource | String | undefined | 来源筛选 | L16 |
| filterKeyword | String | '' | 搜索关键词 | L17 |
| deduplicating | Boolean | false | 去重中 | L18 |
| dedupTimeRange | Number | 6 | 去重时间范围(小时) | L21 |

### 功能按钮

| 按钮名称 | 事件函数 | 功能说明 | 位置 | 行号 |
|----------|----------|----------|------|------|
| 刷新 | fetchNews | 刷新新闻列表 | 工具栏 | L140 |
| 导出 | onShowExport | 导出数据 | 工具栏 | L138 |
| 去重范围选择 | setDedupTimeRange | 选择去重时间范围 | 独立区域 | L147 |
| 立即去重 | handleDeduplicate | 执行手动去重 | 独立区域 | L154 |
| 加精 | onAddToFeatured | 添加到精选 | 操作列 | L115 |
| 删除 | handleDeleteNews | 删除新闻 | 操作列 | L118 |

### 去重范围选项

| 值 | 标签 | 行号 |
|----|------|------|
| 0 | 全部 | L149 |
| 6 | 6小时内 | L150 |
| 12 | 12小时内 | L151 |
| 24 | 24小时内 | L152 |
| 48 | 48小时内 | L153 |
| 72 | 3天内 | L154 |
| 168 | 7天内 | L155 |

### 表格列定义

| 列名 | dataIndex | 宽度 | render 函数 | 功能 | 行号 |
|------|-----------|------|-------------|------|------|
| ID | id | 60 | - | 显示ID | L79 |
| 来源 | source_site | 100 | Tag | 来源标签 | L80 |
| 标题 | title | - | Link | 标题链接 | L86 |
| 发布时间 | published_at | 120 | formatDate | 格式化时间 | L96 |
| 抓取时间 | crawled_at | 120 | formatDate | 格式化时间 | L99 |
| 操作 | - | 120 | Buttons | 加精/删除按钮 | L102 |

### API 调用

| 函数名 | API 方法 | 参数 | 功能 | 行号 |
|--------|----------|------|------|------|
| fetchNews | getNews | page, limit, source, keyword | 获取新闻列表 | L24-40 |
| handleDeleteNews | deleteNews | id | 删除新闻 | L47-56 |
| handleDeduplicate | deduplicateNews | timeRange, action='mark' | 手动去重 | L60-71 |

### Props 接收

| Prop 名 | 类型 | 必需 | 用途 | PropTypes行号 |
|---------|------|------|------|---------------|
| onAddToFeatured | Function | 否 | 加精回调 | L184 |
| spiders | Array | 否 | 爬虫列表(来源筛选) | L185 |
| onShowExport | Function | 否 | 导出回调 | L188 |

---

## 🔄 Tab 3: DeduplicatedTab - 去重数据

### 状态变量

| 变量名 | 类型 | 初始值 | 用途 | 行号 |
|--------|------|--------|------|------|
| dedupNews | Array | [] | 去重新闻列表 | L15 |
| dedupPagination | Object | {current:1, pageSize:20, total:0} | 分页状态 | L16 |
| loadingDedup | Boolean | false | 加载状态 | L17 |
| dedupFilterSource | String | undefined | 来源筛选 | L18 |
| filterKeyword | String | '' | 搜索关键词 | L19 |

### 功能按钮

| 按钮名称 | 事件函数 | 功能说明 | 位置 | 行号 |
|----------|----------|----------|------|------|
| 刷新 | fetchDedupNews | 刷新列表 | 工具栏 | L163 |
| 导出 | onShowExport | 导出数据 | 工具栏 | L162 |
| 还原已去重数据 | handleBatchRestore | 批量还原到raw状态 | 工具栏 | L171 |
| 还原 | handleRestoreNews | 单个还原 | 操作列 | L128 |
| 删除 | handleDeleteNews | 删除记录 | 操作列 | L131 |
| 加精 | onAddToFeatured | 添加到精选 | 操作列 | L113 |

### 表格列定义

| 列名 | dataIndex | 宽度 | render 函数 | 功能 | 行号 |
|------|-----------|------|-------------|------|------|
| ID | id | 60 | - | 显示ID | L88 |
| 来源 | source_site | 100 | Tag | 来源标签 | L89 |
| 标题 | title | - | Link | 标题链接 | L95 |
| 状态 | stage | 80 | Tag(color) | 状态标签 | L105 |
| 去重时间 | deduplicated_at | 120 | formatDate | 格式化时间 | L110 |
| 操作 | - | 200 | Buttons | 加精/还原/删除 | L112 |

### API 调用

| 函数名 | API 方法 | 参数 | 功能 | 行号 |
|--------|----------|------|------|------|
| fetchDedupNews | getDeduplicatedNews | page, limit, source, keyword | 获取去重列表 | L31-48 |
| handleRestoreNews | restoreNews | id | 还原单条 | L55-64 |
| handleDeleteNews | deleteDeduplicatedNews | id | 删除记录 | L71-80 |
| handleBatchRestore | batchRestoreDeduplicated | - | 批量还原 | L89-98 |

### Props 接收

| Prop 名 | 类型 | 必需 | 用途 | PropTypes行号 |
|---------|------|------|------|---------------|
| spiders | Array | 否 | 爬虫列表 | L197 |
| onAddToFeatured | Function | 否 | 加精回调 | L198 |
| onShowExport | Function | 否 | 导出回调 | L199 |

---

## 🔧 Tab 4: FilterSettingsTab - 过滤设置

### 状态变量

| 变量名 | 类型 | 初始值 | 用途 | 行号 |
|--------|------|--------|------|------|
| blacklistKeywords | Array | [] | 黑名单列表 | L15 |
| newKeyword | String | '' | 新增关键词 | L16 |
| newMatchType | String | 'contains' | 匹配类型 | L17 |
| filtering | Boolean | false | 过滤中 | L18 |
| filterTimeRange | Number | 6 | 过滤时间范围(小时) | L19 |
| filteredNews | Array | [] | 已过滤新闻 | L21 |
| filteredPagination | Object | {current:1, pageSize:10, total:0} | 分页状态 | L22 |
| loadingFiltered | Boolean | false | 加载状态 | L23 |
| filterKeyword | String | '' | 搜索关键词 | L24 |

### 功能按钮

| 按钮名称 | 事件函数 | 功能说明 | 位置 | 行号 |
|----------|----------|----------|------|------|
| 立即执行过滤 | handleFilterNews | 执行本地过滤 | 过滤区域 | L234 |
| 还原已过滤数据 | handleBatchRestoreFiltered | 批量还原 | 过滤区域 | L239 |
| 添加关键词 | handleAddKeyword | 添加黑名单 | 黑名单区域 | L258 |
| 删除关键词 | handleDeleteKeyword | 删除黑名单 | 黑名单表格 | L218 |
| 还原 | handleRestoreNews | 单个还原 | 已过滤列表 | L207 |
| 删除 | handleDeleteFilteredNews | 删除记录 | 已过滤列表 | L214 |
| 加精 | onAddToFeatured | 添加到精选 | 已过滤列表 | L192 |

### 过滤时间范围选项

| 值 | 标签 | 行号 |
|----|------|------|
| 6 | 6小时内 | L229 |
| 12 | 12小时内 | L230 |
| 24 | 24小时内 | L231 |
| 48 | 48小时内 | L232 |

### 匹配类型选项

| 值 | 标签 | 行号 |
|---------|------|------|
| contains | 包含 | L248 |
| regex | 正则 | L249 |

### 黑名单表格列

| 列名 | dataIndex | 功能 | 行号 |
|------|-----------|------|------|
| 关键词 | keyword | 显示关键词 | L149 |
| 匹配类型 | match_type | 显示匹配类型 | L150 |
| 操作 | - | 删除按钮 | L151 |

### 已过滤新闻表格列

| 列名 | dataIndex | 宽度 | render 函数 | 功能 | 行号 |
|------|-----------|------|-------------|------|------|
| ID | id | 60 | - | 显示ID | L166 |
| 来源 | source_site | 100 | Tag | 来源标签 | L167 |
| 标题 | title | - | Link | 标题链接 | L173 |
| 过滤时间 | filtered_at | 120 | formatDate | 格式化时间 | L183 |
| 操作 | - | 200 | Buttons | 加精/还原/删除 | L186 |

### API 调用

| 函数名 | API 方法 | 参数 | 功能 | 行号 |
|--------|----------|------|------|------|
| fetchBlacklist | getBlacklist | - | 获取黑名单 | L32-40 |
| handleAddKeyword | addBlacklist | keyword, matchType | 添加黑名单 | L47-58 |
| handleDeleteKeyword | deleteBlacklist | id | 删除黑名单 | L65-74 |
| handleFilterNews | filterNews | timeRange | 执行过滤 | L90-100 |
| handleBatchRestoreFiltered | batchRestoreFiltered | - | 批量还原 | L104-113 |
| fetchFilteredNews | getFilteredDedupNews | page, limit, keyword | 获取已过滤列表 | L118-132 |
| handleRestoreNews | restoreNews | id | 还原单条 | L139-148 |
| handleDeleteFilteredNews | deleteDeduplicatedNews | id | 删除记录 | L155-164 |

### Props 接收

| Prop 名 | 类型 | 必需 | 用途 | PropTypes行号 |
|---------|------|------|------|---------------|
| onAddToFeatured | Function | 否 | 加精回调 | L314 |

---

## ⭐ Tab 5: CuratedNewsTab - 精选数据

### 状态变量

| 变量名 | 类型 | 初始值 | 用途 | 行号 |
|--------|------|--------|------|------|
| curatedNews | Array | [] | 精选新闻列表 | L15 |
| curatedPagination | Object | {current:1, pageSize:20, total:0} | 分页状态 | L16 |
| loading | Boolean | false | 加载状态 | L17 |
| filterSource | String | undefined | 来源筛选 | L18 |
| filterKeyword | String | '' | 搜索关键词 | L19 |

### 功能按钮

| 按钮名称 | 事件函数 | 功能说明 | 位置 | 行号 |
|----------|----------|----------|------|------|
| 刷新 | fetchCuratedNews | 刷新列表 | 工具栏 | L128 |
| 导出 | onShowExport | 导出数据 | 工具栏 | L127 |
| 加精 | onAddToFeatured | 添加到精选 | 操作列 | L94 |
| 删除 | handleDeleteNews | 删除记录 | 操作列 | L97 |

### 表格列定义

| 列名 | dataIndex | 宽度 | render 函数 | 功能 | 行号 |
|------|-----------|------|-------------|------|------|
| ID | id | 60 | - | 显示ID | L69 |
| 来源 | source_site | 100 | Tag | 来源标签 | L70 |
| 标题 | title | - | Link | 标题链接 | L76 |
| 精选时间 | curated_at | 120 | formatDate | 格式化时间 | L86 |
| 操作 | - | 150 | Buttons | 加精/删除 | L89 |

### API 调用

| 函数名 | API 方法 | 参数 | 功能 | 行号 |
|--------|----------|------|------|------|
| fetchCuratedNews | getCuratedNews | page, limit, source, keyword | 获取精选列表 | L27-43 |
| handleDeleteNews | deleteCuratedNews | id | 删除记录 | L50-59 |

### Props 接收

| Prop 名 | 类型 | 必需 | 用途 | PropTypes行号 |
|---------|------|------|------|---------------|
| spiders | Array | 否 | 爬虫列表 | L141 |
| onAddToFeatured | Function | 否 | 加精回调 | L142 |
| onShowExport | Function | 否 | 导出回调 | L143 |

---

## 🤖 Tab 8: AIFilterTab - AI 筛选

### 状态变量

| 变量名 | 类型 | 初始值 | 用途 | 行号 |
|--------|------|--------|------|------|
| rejectedNews | Array | [] | AI拒绝列表 | L17 |
| rejectedPagination | Object | {current:1, pageSize:20, total:0} | 分页状态 | L18 |
| loadingRejected | Boolean | false | 加载状态 | L19 |
| filtering | Boolean | false | AI筛选中 | L20 |
| filterKeyword | String | '' | 搜索关键词 | L21 |
| aiPrompt | String | '' | AI提示词 | L22 |
| filterTimeRange | Number | 8 | 筛选时间范围(小时) | L23 |
| batchSize | Number | 10 | 批处理大小 | L24 |
| loadingConfig | Boolean | false | 配置加载中 | L25 |

### 功能按钮

| 按钮名称 | 事件函数 | 功能说明 | 位置 | 行号 |
|----------|----------|----------|------|------|
| 开始 AI 筛选 | handleAIFilter | 执行AI筛选 | 筛选区域 | L282 |
| 刷新 | fetchRejectedNews | 刷新列表 | 工具栏 | L314 |
| 批量还原 | handleBatchRestore | 批量还原 | Card标题 | L319 |
| 清除所有AI状态 | handleClearAllAiStatus | 清除AI状态 | Card标题 | L329 |
| 还原 | handleRestoreNews | 单个还原 | 操作列 | L208 |
| 删除 | handleDeleteNews | 删除记录 | 操作列 | L213 |
| 加精 | onAddToFeatured | 添加到精选 | 操作列 | L191 |

### AI 配置项

| 配置项 | 状态变量 | UI 组件 | 行号 |
|--------|----------|---------|------|
| AI 提示词 | aiPrompt | Input.TextArea | L242-248 |
| 筛选范围 | filterTimeRange | Select(2/4/6/8/12小时) | L251-258 |
| 批处理大小 | batchSize | InputNumber(1-50) | L261-271 |

### 表格列定义

| 列名 | dataIndex | 宽度 | render 函数 | 功能 | 行号 |
|------|-----------|------|-------------|------|------|
| ID | id | 60 | - | 显示ID | L169 |
| 来源 | source_site | 100 | Tag | 来源标签 | L170 |
| 标题 | title | - | Link | 标题链接 | L176 |
| AI 标签 | ai_tag | 120 | Tag | AI标签 | L186 |
| 操作 | - | 200 | Buttons | 加精/还原/删除 | L189 |

### API 调用

| 函数名 | API 方法 | 参数 | 功能 | 行号 |
|--------|----------|------|------|------|
| loadConfig | getAiConfig | - | 加载AI配置 | L33-51 |
| saveConfig | setAiConfig | prompt, timeRange, batchSize | 保存配置 | L58-71 |
| fetchRejectedNews | getFilteredCurated | status='rejected', page, limit, keyword | 获取拒绝列表 | L78-94 |
| handleAIFilter | filterCuratedNews | - | 执行AI筛选 | L102-151 |
| handleRestoreNews | restoreCuratedNews | id | 还原单条 | L158-167 |
| handleDeleteNews | deleteCuratedNews | id | 删除记录 | L174-182 |
| handleBatchRestore | batchRestoreCurated | - | 批量还原 | L189-199 |
| handleClearAllAiStatus | clearAllAiStatus | - | 清除AI状态 | L206-216 |

### Props 接收

| Prop 名 | 类型 | 必需 | 用途 | PropTypes行号 |
|---------|------|------|------|---------------|
| onAddToFeatured | Function | 否 | 加精回调 | L372 |

---

## ✨ Tab 9: AIBestTab - AI 精选

### 状态变量

| 变量名 | 类型 | 初始值 | 用途 | 行号 |
|--------|------|--------|------|------|
| approvedNews | Array | [] | AI批准列表 | L15 |
| approvedPagination | Object | {current:1, pageSize:20, total:0} | 分页状态 | L16 |
| loading | Boolean | false | 加载状态 | L17 |
| filterSource | String | undefined | 来源筛选 | L18 |
| filterKeyword | String | '' | 搜索关键词 | L19 |

### 功能按钮

| 按钮名称 | 事件函数 | 功能说明 | 位置 | 行号 |
|----------|----------|----------|------|------|
| 刷新 | fetchApprovedNews | 刷新列表 | 工具栏 | L123 |
| 导出 | onShowExport | 导出数据 | 工具栏 | L122 |
| 加精 | onAddToFeatured | 添加到精选 | 操作列 | L93 |
| 删除 | handleDeleteNews | 删除记录 | 操作列 | L96 |

### 表格列定义

| 列名 | dataIndex | 宽度 | render 函数 | 功能 | 行号 |
|------|-----------|------|-------------|------|------|
| ID | id | 60 | - | 显示ID | L68 |
| 来源 | source_site | 100 | Tag | 来源标签 | L69 |
| 标题 | title | - | Link | 标题链接 | L75 |
| AI 标签 | ai_tag | 120 | Tag | AI标签 | L85 |
| 操作 | - | 150 | Buttons | 加精/删除 | L88 |

### API 调用

| 函数名 | API 方法 | 参数 | 功能 | 行号 |
|--------|----------|------|------|------|
| fetchApprovedNews | getFilteredCurated | status='approved', page, limit, source, keyword | 获取批准列表 | L27-45 |
| handleDeleteNews | deleteCuratedNews | id | 删除记录 | L52-61 |

### Props 接收

| Prop 名 | 类型 | 必需 | 用途 | PropTypes行号 |
|---------|------|------|------|---------------|
| spiders | Array | 否 | 爬虫列表 | L155 |
| onAddToFeatured | Function | 否 | 加精回调 | L156 |
| onShowExport | Function | 否 | 导出回调 | L157 |

---

## 📤 Tab 10: ExportTab - 新闻输出

### 状态变量

| 变量名 | 类型 | 初始值 | 用途 | 行号 |
|--------|------|--------|------|------|
| exportStage | String | 'curated' | 导出阶段 | L10 |
| exportTimeRange | Number | 2 | 导出时间范围(小时) | L11 |
| customStartDate | Dayjs/null | null | 自定义开始日期 | L12 |
| customEndDate | Dayjs/null | null | 自定义结束日期 | L13 |
| exportList | Array | [] | 导出预览列表 | L14 |
| loadingExport | Boolean | false | 加载中 | L15 |

### 功能按钮

| 按钮名称 | 事件函数 | 功能说明 | 位置 | 行号 |
|----------|----------|----------|------|------|
| 查询 | handleQuery | 查询预览 | 查询区域 | L41 |
| 导出 | handleExport | 执行导出 | 导出区域 | L135 |

### 导出阶段选项

| 值 | 标签 | 行号 |
|----|------|------|
| raw | 原始新闻 | L57 |
| deduplicated | 去重新闻 | L58 |
| curated | 精选新闻 | L59 |
| ai_approved | AI 精选 | L60 |
| manual_featured | 手动加精 | L61 |

### 时间范围选项

| 值 | 标签 | 行号 |
|----|------|------|
| 2 | 2小时内 | L75 |
| 6 | 6小时内 | L76 |
| 12 | 12小时内 | L77 |
| 24 | 24小时内 | L78 |
| 168 | 7天内 | L79 |
| 720 | 30天内 | L80 |
| 0 | 自定义 | L81 |

### API 调用

| 函数名 | API 方法 | 参数 | 功能 | 行号 |
|--------|----------|------|------|------|
| handleQuery | getExportNews | stage, timeRange, startDate, endDate | 查询预览 | L22-38 |
| handleExport | exportNews | stage, timeRange, startDate, endDate | 执行导出 | L100-132 |

### Props 接收

| Prop 名 | 类型 | 必需 | 用途 | PropTypes行号 |
|---------|------|------|------|---------------|
| manuallyFeatured | Array | 否 | 手动加精列表 | L228 |

---

## 🕷️ Tab 7: SpiderControlTab - 爬虫控制

### 功能按钮

| 按钮名称 | 事件函数 | 功能说明 | 位置 | 行号 |
|----------|----------|----------|------|------|
| 启动/停止 | onRunSpider/onCancelSpider | 控制爬虫 | 卡片内 | ScraperCard |

### Props 接收

| Prop 名 | 类型 | 必需 | 用途 | PropTypes行号 |
|---------|------|------|------|---------------|
| spiders | Array | 是 | 爬虫列表 | L25 |
| spiderStatus | Object | 是 | 爬虫状态 | L26 |
| onRunSpider | Function | 是 | 启动爬虫 | L27 |
| onCancelSpider | Function | 是 | 停止爬虫 | L28 |
| onUpdateConfig | Function | 是 | 更新配置 | L29 |

---

## 🎴 ScraperCard - 爬虫卡片

### 状态变量

| 变量名 | 类型 | 初始值 | 用途 | 行号 |
|--------|------|--------|------|------|
| interval | Number | spider.interval | 抓取间隔 | L15 |
| limit | Number | spider.limit | 抓取数量 | L16 |

### 功能按钮

| 按钮名称 | 事件函数 | 功能说明 | 位置 | 行号 |
|----------|----------|----------|------|------|
| 启动 | handleRun | 启动爬虫 | 卡片按钮 | L91-95 |
| 停止 | handleCancel | 停止爬虫 | 卡片按钮 | L99-103 |

### 配置项

| 配置项 | 类型 | 范围 | 默认值 | 行号 |
|--------|------|------|--------|------|
| 抓取间隔 | Number | 1-60秒 | 30 | L39-48 |
| 抓取数量 | Number | 1-100条 | 30 | L52-60 |

### Props 接收

| Prop 名 | 类型 | 必需 | 用途 | PropTypes行号 |
|---------|------|------|------|---------------|
| spider | Object | 是 | 爬虫配置 | L148-153 |
| status | Object | 否 | 爬虫状态 | L154 |
| onRun | Function | 是 | 启动回调 | L155 |
| onCancel | Function | 是 | 停止回调 | L156 |
| onUpdateConfig | Function | 是 | 更新回调 | L157 |

---

## 🧰 辅助组件

### NewsToolbar - 通用新闻工具栏

**Props**:
- `onSearch` (Function) - 搜索回调
- `searchPlaceholder` (String) - 搜索提示
- `spiders` (Array) - 爬虫列表
- `selectedSource` (String) - 选中来源
- `onSourceChange` (Function) - 来源变更
- `onExport` (Function) - 导出回调
- `onRefresh` (Function) - 刷新回调
- `loading` (Boolean) - 加载状态
- `children` (ReactNode) - 额外按钮

### NewsExpandedView - 新闻展开视图

**Props**:
- `record` (Object) - 新闻记录
- `showAiTag` (Boolean) - 显示AI标签
- `showStage` (Boolean) - 显示状态

### TimeRangeSelect - 通用时间范围选择器

**功能**: 提供统一的时间范围选择下拉框,用于各个Tab的时间筛选功能。

**选项**: 
- 2小时内 (value: 2)
- 6小时内 (value: 6)
- 8小时内 (value: 8)
- 12小时内 (value: 12)
- 24小时内 (value: 24)
- 3天内 (value: 72)
- 7天内 (value: 168)
- 全部时间 (value: 0)

**Props**:
- `value` (Number) - 当前选中值 (默认: 8)
- `onChange` (Function, 必需) - 值变更回调
- `style` (Object) - 自定义样式
- `title` (String) - 默认悬停提示: "筛选基于新闻发布时间 (北京时间)"

**使用组件**:
- AIFilterTab (AI筛选时间范围)
- ExportTab (新闻输出时间范围)  
- FilterSettingsTab (本地过滤时间范围)
- NewsManagementTab (去重时间范围)

**重要说明**: 
- 所有时间筛选均基于 **`published_at`** (新闻发布时间)
- 采用 **北京时间** (UTC+8)
- 后端使用 `datetime.now()` 计算时间范围

---

## 📊 API 方法汇总

| API 方法 | 路径 | 功能 | 使用组件 |
|----------|------|------|----------|
| getNews | GET /api/news | 获取原始新闻 | Dashboard, NewsManagementTab |
| deleteNews | DELETE /api/news/:id | 删除原始新闻 | NewsManagementTab |
| deduplicateNews | POST /api/deduplicate | 手动去重 | NewsManagementTab |
| getDeduplicatedNews | GET /api/deduplicated/news | 获取去重新闻 | Dashboard, DeduplicatedTab |
| restoreNews | POST /api/deduplicated/:id/restore | 还原单条 | DeduplicatedTab, FilterSettingsTab |
| deleteDeduplicatedNews | DELETE /api/deduplicated/:id | 删除去重记录 | DeduplicatedTab, FilterSettingsTab |
| batchRestoreDeduplicated | POST /api/deduplicated/batch_restore_all | 批量还原到raw | DeduplicatedTab |
| getCuratedNews | GET /api/curated/news | 获取精选新闻 | Dashboard, CuratedNewsTab |
| deleteCuratedNews | DELETE /api/curated/:id | 删除精选记录 | CuratedNewsTab, AIFilterTab, AIBestTab |
| getBlacklist | GET /api/blacklist | 获取黑名单 | FilterSettingsTab |
| addBlacklist | POST /api/blacklist | 添加黑名单 | FilterSettingsTab |
| deleteBlacklist | DELETE /api/blacklist/:id | 删除黑名单 | FilterSettingsTab |
| filterNews | POST /api/filter | 执行本地过滤 | FilterSettingsTab |
| batchRestoreFiltered | POST /api/filtered/batch_restore_all | 批量还原到deduplicated | FilterSettingsTab |
| getFilteredDedupNews | GET /api/filtered/dedup/news | 获取已过滤新闻 | Dashboard, FilterSettingsTab |
| getFilteredCurated | GET /api/curated/filtered | 获取AI筛选结果 | Dashboard, AIFilterTab, AIBestTab |
| filterCuratedNews | POST /api/curated/ai_filter | 执行AI筛选 | AIFilterTab |
| restoreCuratedNews | POST /api/curated/:id/restore | 还原AI筛选 | AIFilterTab |
| batchRestoreCurated | POST /api/curated/batch_restore | 批量还原AI筛选 | AIFilterTab |
| clearAllAiStatus | POST /api/curated/clear_ai_status | 清除AI状态 | AIFilterTab |
| getAiConfig | GET /api/ai/config | 获取AI配置 | AIFilterTab |
| setAiConfig | POST /api/ai/config | 保存AI配置 | AIFilterTab |
| getExportNews | GET /api/export | 查询导出预览 | ExportTab |
| exportNews | POST /api/export | 执行导出 | Dashboard, ExportTab |
| getSpiders | GET /api/spiders | 获取爬虫列表 | Dashboard |
| getSpiderStatus | GET /api/spiders/status | 获取爬虫状态 | Dashboard |
| runSpider | POST /api/spiders/:name/run | 启动爬虫 | Dashboard |
| stopSpider | POST /api/spiders/:name/stop | 停止爬虫 | Dashboard |
| updateSpiderConfig | POST /api/spiders/:name/config | 更新爬虫配置 | Dashboard |
| getStats | GET /api/stats | 获取统计数据 | Dashboard |

---

## 🔄 数据流图

```
原始新闻 (news) 
    ↓ [去重]
去重数据 (deduplicated_news, stage='deduplicated')
    ↓ [本地黑名单过滤]
    ├─→ 被过滤 (stage='filtered')
    └─→ 精选数据 (curated_news, ai_status='pending')
            ↓ [AI筛选]
            ├─→ AI拒绝 (ai_status='rejected')
            └─→ AI精选 (ai_status='approved')
```

---

## ✨ 重要功能特性

### 1. 批量还原功能
- **去重数据 Tab**: 还原到 `raw` 状态（清空去重和精选记录）
- **过滤设置 Tab**: 还原到 `deduplicated` 状态（清空精选记录）
- **AI 筛选 Tab**: 还原 AI 状态为 `pending`

### 2. 全局计数自动刷新
- 所有 Tab 标题显示实时计数
- 每 30 秒自动刷新一次
- Tab 切换时立即刷新

### 3. 通用组件复用
- **NewsToolbar**: 统一的工具栏（搜索、筛选、导出、刷新）
- **NewsExpandedView**: 统一的展开视图

### 4. PropTypes 类型检查
- 所有组件都添加了 PropTypes 定义
- 提供运行时类型检查和文档

---

## 🔥 最近更新 (2024-12-27)

### 时间筛选逻辑优化
**影响范围**: AIFilterTab, ExportTab, 后端API

**变更内容**:
1. **AI 筛选 (`ai_filter_curated`)**: 
   - ✅ 从 `curated_at` (入库时间) 切换为 `published_at` (发布时间)
   - ✅ 修复时间计算从 `datetime.utcnow()` 变更为 `datetime.now()` (北京时间)
   
2. **新闻输出 (`get_export_news`)**: 
   - ✅ 从 `curated_at` (入库时间) 切换为 `published_at` (发布时间)
   - ✅ 修复时间计算从 `datetime.utcnow()` 变更为 `datetime.now()` (北京时间)

**用户体验改善**:
- 选择 "8小时内" 现在表示**新闻发布时间在过去8小时内**
- 避免将旧新闻(补录)误判为新新闻
- 所有时间筛选统一使用**北京时间 (UTC+8)**

### AI 筛选进度显示修复
**影响范围**: AIFilterTab.jsx

**问题**: 进度显示超过 100% (例如: `113%`, `183%`)

**根本原因**: 后端返回的 `total` 是"当前剩余待处理总数" (动态减少), 前端误将其当作"初始总数" (固定值)

**解决方案**:
- 动态计算: `estimatedTotal = remainingTotal + itemsProcessedBeforeThisBatch`
- 正确公式: `progress = totalProcessed / estimatedTotal * 100`

**效果**: 进度条正常显示为 `10/100 (10%)`, `20/100 (20%)` ...

### Telegram 富文本复制功能
**影响范围**: ExportTab.jsx

**新增功能**: "TG格式" 按钮支持富文本复制

**技术实现**:
- 使用 `navigator.clipboard.write()` API
- 写入 `text/html` MIME 类型 (可点击的蓝色链接)
- 写入 `text/plain` MIME 类型 (纯文本 fallback)

**用户体验**:
- 复制后粘贴到 Telegram → 显示为**可点击的蓝色链接**
- 不再是 `<a href="...">标题</a>` 原始代码

### 通用组件统一
**影响范围**: ExportTab.jsx, TimeRangeSelect.jsx

**变更内容**:
1. `ExportTab` 使用通用 `TimeRangeSelect` 组件
2. `TimeRangeSelect` 添加悬停提示: "筛选基于新闻发布时间 (北京时间)"
3. 移除重复的时间范围选择器代码

**代码优化**: 减少冗余代码, 统一UI/UX体验

### Bug 修复
1. **ExportTab.jsx**: 补充缺失的 `Tag` 导入 (`import { Tag } from 'antd'`)
2. **AIFilterTab.jsx**: 确认 `logs` 状态和 `addLog` 函数定义正常 (热更新缓存问题)

---

**文档结束** - 如需更新，请同步修改代码和本文档
