# AINEWS 项目技术文档

> 本文档为新AI快速了解项目而创建，包含完整的技术栈、模块结构和功能说明。
> 最后更新：2025-12-26

---

## 📋 项目概述

**AINEWS** 是一个智能加密新闻聚合与过滤系统，自动从多个区块链媒体平台抓取新闻，使用AI进行质量筛选，并提供灵活的去重、过滤和导出功能。

**核心价值：**
- 🤖 自动抓取7个主流加密媒体平台的重要新闻
- 🎯 AI智能评分筛选（DeepSeek API）
- 🔄 智能去重（基于标题相似度，阈值50%）
- 📤 多格式导出（纯文本、Markdown、Telegram格式）
- ⭐ 手动加精补充机制

---

## 🛠 技术栈

### 后端
- **框架**: FastAPI (Python 3.10+)
- **数据库**: SQLite3 (WAL模式)
- **爬虫**: Playwright (浏览器自动化)
- **AI**: DeepSeek API
- **推送**: Telegram Bot API

### 前端
- **框架**: React 18
- **UI库**: Ant Design 5.x
- **构建工具**: Vite
- **路由**: React Router
- **HTTP客户端**: Axios
- **日期处理**: Day.js

### 爬虫引擎
- **浏览器**: Playwright (Chromium)
- **去重**: difflib.SequenceMatcher
- **内容清理**: 正则表达式

---

## 📁 目录结构详解

```
AINEWS/
├── backend/                    # FastAPI后端服务
│   ├── main.py                # 主API服务 (39KB, 1098行)
│   ├── services/              # 服务层
│   │   ├── deepseek_service.py   # DeepSeek AI服务
│   │   └── telegram_service.py   # Telegram推送服务
│   └── test_api.py            # API测试文件
│
├── crawler/                    # 爬虫引擎核心
│   ├── main.py                # 爬虫主入口
│   ├── scrapers/              # 各平台爬虫实现
│   │   ├── base.py           # 爬虫基类
│   │   ├── odaily.py         # Odaily爬虫
│   │   ├── blockbeats.py     # BlockBeats爬虫
│   │   ├── panews.py         # PANews爬虫
│   │   ├── marsbit.py        # MarsBit爬虫
│   │   ├── chaincatcher.py   # ChainCatcher爬虫
│   │   ├── foresight.py      # Foresight News爬虫
│   │   └── techflow.py       # TechFlow爬虫
│   ├── filters/               # 过滤器引擎
│   │   ├── local_deduplicator.py  # 本地去重器 (阈值0.50)
│   │   ├── keyword_filter.py      # 关键词过滤器
│   │   └── blacklist_filter.py    # 黑名单过滤器
│   ├── database/              # 数据库操作层
│   │   ├── db_sqlite.py      # SQLite数据库类
│   │   └── migrations.py     # 数据库迁移脚本
│   ├── ai/                    # AI模块
│   │   └── deepseek_client.py    # DeepSeek客户端
│   └── config/                # 配置文件
│       ├── filters.yaml      # 过滤器配置
│       ├── scrapers.yaml     # 爬虫配置
│       └── blacklist.yaml    # 黑名单配置
│
├── frontend/                   # React前端
│   ├── src/
│   │   ├── pages/            # 页面组件
│   │   │   └── Dashboard.jsx # 主仪表盘 (56KB, 1435行)
│   │   ├── components/       # 可复用组件
│   │   │   └── dashboard/   # Dashboard子组件
│   │   │       ├── NewsManagementTab.jsx # 数据管理Tab
│   │   │       ├── SpiderControlTab.jsx  # 爬虫管理Tab
│   │   │       ├── ScraperCard.jsx       # 爬虫卡片子组件
│   │   │       ├── DeduplicatedTab.jsx   # 去重数据Tab
│   │   │       ├── FilterSettingsTab.jsx # 过滤设置Tab
│   │   │       ├── CuratedNewsTab.jsx    # 精选数据Tab
│   │   │       ├── ApiSettingsTab.jsx    # API配置Tab
│   │   │       ├── ExportTab.jsx         # 新闻输出Tab
│   │   │       ├── AIFilterTab.jsx       # AI筛选Tab
│   │   │       └── AIBestTab.jsx         # AI精选Tab
│   │   ├── api.js            # API封装
│   │   ├── App.jsx           # 应用入口
│   │   └── main.jsx          # React入口
│   ├── public/               # 静态资源
│   └── package.json          # 依赖配置
│
├── database/                   # 数据库文件目录
│   ├── migrations/           # 迁移脚本
│   └── backups/              # 备份文件
│
├── ainews.db                  # SQLite数据库文件 (1.1MB)
├── scraper_config.json        # 爬虫配置
├── .env.example               # 环境变量示例
└── README.md                  # 项目说明

测试文件（待清理）/
├── test_*.py                  # 22个测试文件
├── check_*.py                 # 检查脚本
├── debug_*.py                 # 调试脚本
├── clean_*.py                 # 清理脚本
└── *.txt                      # 输出文件
```

---

## 🎯 核心功能模块

### 1. 新闻抓取系统 (Crawler)

**位置**: `crawler/scrapers/*.py`

**支持的平台**:
1. Odaily (odaily.py) - 更新频率: 4.2条/小时
2. BlockBeats (blockbeats.py) - 更新频率: 3.8条/小时
3. MarsBit (marsbit.py) - 更新频率: 2.8条/小时
4. PANews (panews.py) - 更新频率: 2.2条/小时
5. ChainCatcher (chaincatcher.py) - 更新频率: 2.1条/小时
6. TechFlow (techflow.py) - 更新频率: 1.5条/小时
7. Foresight News (foresight.py) - 更新频率: 1.3条/小时

**抓取策略**:
- 建议频率: 统一30分钟
- 增量抓取: 基于URL哈希去重
- 内容清理: 自动去除平台前缀（如"PANews X月X日消息，"）
- 使用`inner_text()`获取纯文本（避免HTML标签）

### 2. 智能去重系统

**位置**: `crawler/filters/local_deduplicator.py`

**算法**: SequenceMatcher (difflib)
- **阈值**: 0.50 (50%)
- **时间窗口**: 24小时
- **逻辑**: 相似度≥50%视为重复

**示例**:
```python
# 相似度66.67% > 50% → 去重
"易理华：USD1将成为领先的稳定币，WLFI为持续重仓项目"
"易理华：USD1未来能成为领先的稳定币，将持续投资和支持"

# 相似度51.69% > 50% → 去重
"Wintermute CEO：部分宣称「退出加密」的年轻建设者和KOL其实从未真正入场"
"Wintermute CEO：30岁以下宣布退圈的加密开发者与KOL均为骗子"
```

### 3. AI筛选系统

**位置**: `backend/services/deepseek_service.py`

**功能**:
- AI模型: DeepSeek
- 评分范围: 0-10分
- 输出格式: "X分-原因 #标签"
- 状态: approved (通过) / rejected (拒绝)

**流程**:
1. 用户配置AI提示词
2. 批量提交新闻到AI
3. AI返回评分和标签
4. 自动分类到"AI精选"或"AI筛选"tab

### 4. 新闻输出系统

**位置**: `frontend/src/pages/Dashboard.jsx` (新闻输出tab)

**功能**:
- **时间筛选**: 6/12/24/48小时
- **评分筛选**: ≥4/5/6/7/8/9分
- **排序**: 按AI评分从高到低
- **手动加精**: 从其他tab临时添加新闻（带⭐标记）
- **复制格式**:
  - 纯文本: 标题+内容，新闻间用 `---` 分隔
  - Markdown: `- [标题](链接)`
  - Telegram: `<a href="链接">标题</a>`

### 5. 关键词过滤系统

**位置**: `crawler/filters/keyword_filter.py`

**功能**:
- 黑名单关键词
- 正则表达式匹配
- 被过滤的新闻进入"过滤设置"tab

---

## 💾 数据库设计

**文件**: `ainews.db` (SQLite3, WAL模式)

### 主要表结构

#### 1. `news` - 原始新闻表
```sql
CREATE TABLE news (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    source_url TEXT UNIQUE,
    source_site TEXT,
    published_at DATETIME,
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    stage TEXT DEFAULT 'raw'  -- raw/duplicate/filtered/curated
)
```

#### 2. `curated_news` - 精选新闻表
```sql
CREATE TABLE curated_news (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    source_url TEXT UNIQUE,
    source_site TEXT,
    published_at DATETIME,
    curated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ai_status TEXT,  -- approved/rejected
    ai_explanation TEXT  -- AI评分和标签
)
```

#### 3. `deduplicated_news` - 去重归档表
```sql
CREATE TABLE deduplicated_news (
    id INTEGER PRIMARY KEY,
    title TEXT,
    content TEXT,
    source_url TEXT,
    source_site TEXT,
    published_at DATETIME,
    deduplicated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    duplicate_of INTEGER,  -- 原始新闻ID
    similarity_score REAL  -- 相似度分数
)
```

#### 4. `blacklist` - 黑名单关键词表
```sql
CREATE TABLE blacklist (
    id INTEGER PRIMARY KEY,
    keyword TEXT UNIQUE NOT NULL,
    match_type TEXT DEFAULT 'exact',  -- exact/regex
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

#### 5. `telegram_config` - Telegram配置表
```sql
CREATE TABLE telegram_config (
    id INTEGER PRIMARY KEY,
    bot_token TEXT,
    chat_id TEXT,
    enabled BOOLEAN DEFAULT 0
)
```

---

## 🔌 API接口文档

**后端地址**: `http://localhost:8000`
**前端地址**: `http://localhost:5173`

### 核心API端点

#### 新闻管理
- `GET /api/news` - 获取原始新闻列表
- `GET /api/news/stats` - 获取统计信息
- `DELETE /api/news/{id}` - 删除新闻
- `POST /api/news/deduplicate` - 执行去重

#### 精选新闻
- `GET /api/curated/news` - 获取精选新闻
- `GET /api/curated/stats` - 获取统计
- `GET /api/curated/export` - 导出新闻（新闻输出功能）
- `POST /api/curated/ai_filter` - AI批量筛选
- `GET /api/curated/filtered` - 获取AI筛选结果
- `POST /api/curated/restore/{id}` - 还原新闻

#### 去重数据
- `GET /api/deduplicated/news` - 获取去重数据
- `DELETE /api/deduplicated/news/{id}` - 删除去重数据

#### 过滤设置
- `GET /api/blacklist` - 获取黑名单
- `POST /api/blacklist` - 添加关键词
- `DELETE /api/blacklist/{id}` - 删除关键词
- `GET /api/filtered/dedup/news` - 获取被过滤的新闻

#### 爬虫控制
- `GET /api/spiders` - 获取所有爬虫
- `GET /api/spiders/status` - 获取爬虫状态
- `POST /api/spiders/run/{name}` - 启动爬虫
- `POST /api/spiders/stop/{name}` - 停止爬虫
- `POST /api/spiders/config/{name}` - 更新配置

#### AI配置
- `GET /api/ai/config` - 获取AI配置
- `POST /api/ai/config` - 设置AI配置

#### Telegram配置
- `GET /api/telegram/config` - 获取配置
- `POST /api/telegram/config` - 设置配置
- `POST /api/telegram/test` - 测试推送

---

## ⚙️ 配置说明

### 环境变量 (.env)
```bash
# DeepSeek AI
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# 数据库
DATABASE_PATH=./ainews.db
```

### 爬虫配置 (scraper_config.json)
```json
{
  "odaily": {"interval": 1800, "limit": 10},
  "blockbeats": {"interval": 1800, "limit": 10},
  "marsbit": {"interval": 1800, "limit": 10},
  "panews": {"interval": 1800, "limit": 10},
  "chaincatcher": {"interval": 1800, "limit": 10},
  "techflow": {"interval": 1800, "limit": 10},
  "foresight": {"interval": 1800, "limit": 10}
}
```

### 去重配置 (crawler/config/filters.yaml)
```yaml
deduplication:
  time_window_hours: 24
  similarity_threshold: 0.50
```

---

## 🚀 启动流程

### 1. 安装依赖
```bash
# 后端
pip install -r backend/requirements.txt
pip install -r crawler/requirements.txt

# 前端
cd frontend
npm install
```

### 2. 配置环境
```bash
# 复制环境变量示例
cp .env.example .env

# 编辑配置
nano .env
```

### 3. 启动服务
```bash
# 启动后端 (PowerShell)
python backend/main.py

# 启动前端
cd frontend
npm run dev
```

### 4. 访问系统
- 前端: http://localhost:5173
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

---

## 📊 功能Tab说明

### 1. 数据管理 (Tab 1)
- 查看所有原始新闻
- 删除、过滤、转移到精选库
- 执行手动去重
- 导出数据

### 2. 爬虫管理 (Tab 2)
- 查看所有爬虫状态
- 启动/停止爬虫
- 配置抓取频率和数量
- 实时显示抓取统计

### 3. 去重数据 (Tab 3)
- 查看被去重的新闻
- **"加精"按钮**: 临时添加到新闻输出
- 还原或删除
- 按来源筛选

### 4. 过滤设置 (Tab 4)
- 添加/删除黑名单关键词
- 查看被过滤的新闻
- **"加精"按钮**: 临时添加到新闻输出
- 还原被误删的新闻

### 5. 精选数据 (Tab 5)
- 查看所有精选新闻
- **"加精"按钮**: 临时添加到新闻输出
- 删除或导出
- 按来源筛选

### 6. API配置 (Tab 6)
- Telegram机器人配置
- DeepSeek API配置
- 测试连接

### 7. 新闻输出 (Tab 7) ⭐ 核心功能
- 按时间范围和评分筛选AI精选新闻
- 显示手动加精的新闻（带⭐标记）
- **展开查看**：点击展开图标查看新闻完整内容
- 全选/反选/清空
- 多格式复制（纯文本/Markdown/TG）
- 查看已选数量

### 8. AI筛选 (Tab 8)
- 配置AI筛选提示词
- 批量提交新闻给AI评分
- 查看被拒绝的新闻
- **永久删除**：删除的新闻从所有数据库表中彻底清除

### 9. AI精选 (Tab 9)
- 查看AI通过的高质量新闻
- 显示AI评分和标签
- **永久删除**：删除的新闻从所有数据库表中彻底清除
- 导出数据

---

## 🧪 测试文件清理建议

### 可以删除的测试文件 (22个)

**根目录测试文件**:
```
test_blockbeats_scraper.py
test_cz.py
test_db_insert.py
test_dedup.py
test_dedup_case.py
test_deduplicator_fixed.py
test_foresight.py
test_foresight_save.py
test_foresight_url.py
test_full_flow.py
test_import.py
test_metaplanet.py
test_polymarket.py
test_scraper_to_file.py
test_similarity.py  # ⚠️ 保留：用于测试相似度
test_substring_logic.py
test_time_extraction.py
test_vitalik.py
```

**backend测试**:
```
backend/test_api.py  # ⚠️ 保留：API测试
```

**crawler测试**:
```
crawler/test_db_connection.py
crawler/test_single_scraper.py
crawler/test_sqlite.py
```

**检查/调试脚本**:
```
check_*.py (11个文件)
debug_*.py (6个文件)
clean_*.py (3个文件)
```

**输出文件**:
```
*.txt (各种测试输出)
*.log (日志文件)
```

### 保留的文件
```
analyze_frequency.py  # 频率分析
test_similarity.py   # 相似度测试
backend/test_api.py  # API测试
```

---

## 📝 重要注意事项

### 1. 数据库
- 使用WAL模式，注意并发写入
- 定期备份数据库文件
- 迁移脚本在 `database/migrations/`

### 2. 爬虫
- Playwright需要先安装浏览器：`playwright install chromium`
- 所有爬虫都继承自`BaseScraper`
- 内容清理在`BaseScraper.clean_content()`中统一处理

### 3. AI配置
- DeepSeek API需要先充值
- AI提示词影响筛选质量，建议详细配置
- 批量处理有速率限制

### 4. 前端
- Dashboard.jsx是单页应用，1866行
- 所有API调用集中在`api.js`
- 使用Ant Design组件库

### 5. 去重
- 阈值50%经过实际测试优化
- 时间窗口24小时
- 可在`crawler/config/filters.yaml`中调整

---

## 🔄 数据流程

```
[爬虫] → [原始新闻表news]
          ↓
    [关键词过滤]
          ↓
    [本地去重] → [去重表deduplicated_news]
          ↓
   [精选库curated_news]
          ↓
     [AI筛选]
          ↓
    ┌─────┴─────┐
[AI精选]    [AI拒绝]
    ↓            ↓
[新闻输出]   [删除]
```

---

## 📞 联系与支持

- 项目路径: `e:\Work\Code\AINEWS`
- 数据库: `ainews.db` (1.1MB)
- 前端端口: 5173
- 后端端口: 8000

**关键文件**:
- 后端主文件: `backend/main.py` (39KB)
- 前端主文件: `frontend/src/pages/Dashboard.jsx` (95KB)
- 爬虫入口: `crawler/main.py`
- 数据库操作: `crawler/database/db_sqlite.py`

---

## 🔧 常见修改场景快速指南

### 核心参数修改

| 修改内容 | 文件位置 | 具体行数/参数 | 说明 |
|---------|---------|-------------|------|
| **去重相似度阈值** | `crawler/config/filters.yaml` | `similarity_threshold: 0.50` | 当前50%，越高越严格 |
| **去重时间窗口** | `crawler/config/filters.yaml` | `time_window_hours: 24` | 当前24小时 |
| **爬虫抓取频率** | `scraper_config.json` | `interval: 1800` | 当前30分钟(1800秒) |
| **爬虫抓取数量** | `scraper_config.json` | `limit: 10` | 每次抓取条数 |
| **本地筛选默认时间** | `frontend/src/pages/Dashboard.jsx` | 搜索`timeRange: '6'` (Tab 1) | 当前6小时 |
| **AI筛选默认时间** | `frontend/src/pages/Dashboard.jsx` | 搜索`aiTimeRange: '8'` (Tab 8) | 当前8小时 |
| **新闻输出默认评分** | `frontend/src/pages/Dashboard.jsx` | 搜索`minScore: 6` (Tab 7) | 当前≥6分 |
| **DeepSeek API配置** | `.env` | `DEEPSEEK_API_KEY` | API密钥 |
| **Telegram配置** | `.env` | `TELEGRAM_BOT_TOKEN` | Bot Token |

### 功能模块定位

| 需求 | 核心文件 | 说明 |
|-----|---------|------|
| **新增爬虫平台** | `crawler/scrapers/` | 继承`BaseScraper`类 |
| **修改去重算法** | `crawler/filters/local_deduplicator.py` | 使用difflib.SequenceMatcher |
| **调整AI提示词** | `backend/services/deepseek_service.py` | 修改评分逻辑 |
| **修改前端Tab** | `frontend/src/pages/Dashboard.jsx` | 1866行单页应用 |
| **添加API端点** | `backend/main.py` | FastAPI路由定义 |
| **数据库迁移** | `crawler/database/migrations.py` | SQLite迁移脚本 |
| **修改导出格式** | `frontend/src/pages/Dashboard.jsx` | 搜索`handleCopy`函数 |

### 快速排查问题

| 问题 | 检查位置 | 常见原因 |
|-----|---------|---------|
| **爬虫不抓取** | `scraper_config.json` | interval设置过大 |
| **去重过多** | `crawler/config/filters.yaml` | threshold阈值过低 |
| **AI不返回** | `.env` | API_KEY未配置或余额不足 |
| **前端显示异常** | `frontend/src/api.js` | API地址错误(默认8000端口) |
| **数据库锁定** | `ainews.db` | WAL模式并发冲突 |

### 性能优化点

| 优化项 | 修改位置 | 建议值 |
|-------|---------|--------|
| **降低爬虫频率** | `scraper_config.json` | interval改为3600(1小时) |
| **减少单次抓取量** | `scraper_config.json` | limit改为5-8 |
| **缩短时间窗口** | `crawler/config/filters.yaml` | time_window_hours改为12 |
| **提高去重阈值** | `crawler/config/filters.yaml` | threshold改为0.60-0.70 |

---

## ⚠️ 文档更新规范

> **重要提醒**: 本文档是项目的唯一真实来源(Single Source of Truth)

**更新要求**:
- ✅ **任何代码修改都必须同步更新此文档**
- ✅ **参数调整**: 更新"常见修改场景快速指南"中的对应值
- ✅ **新增功能**: 更新"核心功能模块"和"API接口文档"
- ✅ **文件变动**: 更新"目录结构详解"
- ✅ **配置修改**: 更新"配置说明"章节
- ✅ **数据库变更**: 更新"数据库设计"和"数据流程"

**更新时机**:
1. 修改代码后立即更新文档
2. 每次Git提交前检查文档一致性
3. 重大更新后修改文档顶部的"最后更新"日期

---

*文档创建于 2025-12-26，基于项目当前状态*  
*最后更新: 2025-12-26 - 前端深度重构与死代码清理（Dashboard拆分为9个独立组件，主文件从1866行减少至约400行）。优化本地过滤逻辑（严格遵循时间范围），修复去重提示bug。*

