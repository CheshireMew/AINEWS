# AINews - 智能新闻聚合与AI筛选系统

> 🚀 基于 Python + FastAPI + React 的全栈新闻聚合系统，支持多源爬取、AI智能筛选、自动去重和Web管理

## ✨ 核心特性

- **🕷️ 多源智能爬虫**
  - 支持多个主流区块链/加密货币新闻网站
  - 自动识别网站重要标记（如"只看精选"）
  - 增量爬取，避免重复抓取
  - 基于 Playwright 实现动态网页抓取

- **� 7x24h 自动化流水线**
  - **自动循环**: 每15分钟执行一次完整流程（抓取 -> 去重 -> 过滤 -> AI评分 -> 推送）
  - **智能去重**: 基于标题语义相似度 + 时间窗口（默认4小时）去重，避免重复内容干扰，同时保留重要更新
  - **自动过滤**: 本地关键词黑名单 + 网站原生标记预筛选

- **🧠 DeepSeek AI 深度分析**
  - **语义打分**: 根据新闻重要性进行 0-10 分打分
  - **内容分类**: 自动分类为 "Flash" (快讯) 或 "Article" (深度文章)
  - **摘要生成**: 自动生成并在 Telegram 推送中附带精炼摘要

- **� 双端展示架构**
  - **前台 (/news)**: 面向公众的精选快讯与深度文章展示，支持无限滚动、吸顶导航
  - **后台 (/admin)**: 完整的管理仪表盘，包含数据管理、爬虫控制、AI 配置、黑名单管理等

- **🤖 Telegram 智能推送**
  - **实时推送**: 高分快讯自动推送到频道
  - **每日日报**: 每天定时生成精选日报（图文/HTML格式）和深度文章日报

## 🛠️ 技术栈

### 后端
- **爬虫引擎**: Python 3.10+ + Playwright
- **Web框架**: FastAPI (Python)
- **AI服务**: DeepSeek API (OpenAI SDK兼容)
- **数据库**: SQLite

### 前端
- **框架**: React 18
- **UI库**: Ant Design
- **构建工具**: Vite
- **状态管理**: React Hooks

## 📦 快速开始

### 1. 环境要求

- Python 3.10+
- Node.js 18+
- Git

### 2. 安装步骤

```bash
# 克隆项目
git clone https://github.com/your-username/AINEWS.git
cd AINEWS

# 后端设置
cd crawler
pip install -r requirements.txt
playwright install chromium

# 前端设置
cd ../frontend
npm install

# 后端API设置
cd ../backend
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入以下配置：
# - DEEPSEEK_API_KEY: DeepSeek API密钥
# - DEEPSEEK_BASE_URL: DeepSeek API地址（可选，默认官方地址）
```

### 4. 运行项目

```bash
# 启动后端API（默认端口：8000）
cd backend
python main.py

# 启动前端（开发模式，默认端口：5173）
cd frontend
npm run dev

# 手动运行爬虫（可选）
cd crawler
python main.py
```

访问 http://localhost:5173 即可使用Web界面。

### 5. 访问系统

**前台（公开访问）**:
- 访问 http://localhost:5173/news 查看精选快讯和深度文章
- 支持无限滚动、搜索、日报查看等功能

**后台（管理员）**:
- 访问 http://localhost:5173/login 登录
- 默认账号密码在首次运行时会在控制台输出
- 登录后可访问完整的管理仪表盘 (http://localhost:5173/admin)

## 📁 项目结构

```
AINEWS/
├── crawler/                 # 爬虫模块
│   ├── scrapers/           # 各网站爬虫实现
│   │   ├── base.py        # 基础爬虫类
│   │   ├── odaily.py      # Odaily爬虫
│   │   ├── panews.py      # PANews爬虫
│   │   ├── foresight.py   # Foresight News爬虫
│   │   └── ...            # 其他网站爬虫
│   ├── filters/            # 过滤和去重逻辑
│   │   └── local_deduplicator.py
│   ├── database/           # 数据库操作
│   │   └── db_sqlite.py
│   └── main.py             # 爬虫主入口
│
├── backend/                # FastAPI后端
│   ├── core/              # 核心模块
│   │   ├── db_base.py     # 数据库基类
│   │   └── exceptions.py  # 自定义异常
│   ├── services/          # 业务服务
│   │   └── deepseek.py    # DeepSeek AI服务
│   └── main.py            # FastAPI主应用
│
├── frontend/              # React前端
│   ├── src/
│   │   ├── components/   # React组件
│   │   │   └── dashboard/ # 控制面板组件
│   │   ├── pages/        # 页面组件
│   │   │   ├── PublicNews.jsx    # 前台公开展示页
│   │   │   ├── Dashboard.jsx     # 后台管理主页
│   │   │   └── Login.jsx         # 登录页
│   │   ├── api/          # API调用封装
│   │   └── App.jsx       # 应用主入口
│   └── vite.config.js    # Vite配置
│
├── ainews.db              # SQLite数据库（.gitignore已排除）
├── .env.example           # 环境变量模板
├── .gitignore            # Git忽略规则
└── README.md             # 本文件
```

## 🔁 工作流程

### 全自动模式（推荐）

启动 `backend/main.py` 后，系统会自动运行以下流程：

1. **定时爬取（8:00-24:00，15分钟/次）**
   - 自动运行所有启用的爬虫
   - 智能超时保护（最多等待5分钟）
   - 抓取的数据存入 `news` 表（stage='raw'）

2. **智能去重（每轮自动执行）**
   - 检查最近12小时的原始数据
   - 基于标题语义相似度计算（默认阈值 0.50）
   - **时间窗口保护**：相似新闻如果间隔 >2小时，视为独立更新
   - 去重后的数据移入 `deduplicated_news` 表

3. **黑名单过滤（每轮自动执行）**
   - 应用本地配置的关键词黑名单
   - 支持精确匹配和正则表达式
   - 过滤后的数据移入 `curated_news` 表（stage='verified'）

4. **AI 智能评分（每轮自动执行）**
   - 调用 DeepSeek API 对精选内容打分（0-10分）
   - 自动分类：Flash（快讯）或 Article（深度文章）
   - 生成简短摘要和评分理由
   - 更新 `ai_status` 和 `ai_explanation` 字段

5. **Telegram 自动推送（每轮自动执行）**
   - Score >= 5 的快讯/文章自动推送到 Telegram 频道
   - 推送间隔：30-60秒（避免频道限流）
   - 推送后更新 `push_status` 和 `pushed_at`

6. **每日日报生成（定时任务）**
   - **精选日报**: 每天 18:00 生成（Score >= 6 的快讯）
   - **文章日报**: 每天 21:00 生成（Score > 0 的深度文章）
   - 保存到 `daily_reports` 表，并推送到 Telegram

### 手动模式

通过后台管理界面 (http://localhost:5173/admin)：
- **爬虫控制**: 手动启动/停止特定爬虫
- **批量去重**: 自定义时间范围和阈值
- **AI筛选**: 自定义Prompt和筛选范围
- **数据导出**: 导出为文本、Markdown 或 Telegram HTML 格式

## 📝 配置说明

### 环境变量（.env）

参考 `.env.example` 文件：

```env
# DeepSeek AI配置
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 可选：Telegram推送配置
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL_ID=@your_channel
```

### 爬虫配置

爬虫配置存储在数据库中，可通过Web界面的"爬虫控制"Tab进行配置：
- 抓取间隔（秒）
- 单次抓取数量
- 启用/禁用特定爬虫

### 黑名单过滤

在Web界面的"过滤设置"Tab中配置：
- 支持精确匹配和正则表达式
- 实时生效，自动应用到新抓取的内容

### AI筛选配置

在Web界面的"AI筛选"Tab中配置：
- 自定义筛选提示词（Prompt）
- 设置筛选时间范围
- 调整批处理大小

### 自动化配置

系统自动化由 `backend/main.py` 的两个后台循环管理：

**自动流水线 (`auto_pipeline_loop`)**:
- 运行间隔：15分钟
- 工作时间：08:00-24:00（北京时间）
- 包含：爬虫等待 → 去重 → 过滤 → AI评分 → 推送

**定时调度器 (`scheduler_loop`)**:
- 运行间隔：1分钟
- 负责触发每日日报推送
- 精选日报时间：可在"全局API配置"Tab自定义（默认18:00）
- 文章日报时间：可在"全局API配置"Tab自定义（默认21:00）

### 去重配置

去重参数存储在数据库 `system_config` 表中：
- `dedup_threshold`: 相似度阈值（默认 0.50，范围 0-1）
- `auto_dedup_hours`: 自动去重时间范围（默认 12 小时）
- 时间窗口硬编码为 **2小时**（`backend/main.py` 第1688行）

> **注意**: 如需调整时间窗口，需修改代码中的 `time_window_hours` 参数

## 🤝 贡献指南

欢迎贡献代码！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细的贡献流程。

## 📄 许可证

本项目采用 MIT License - 详见 [LICENSE](LICENSE) 文件

## ❓ 常见问题

**Q: 为什么有些新闻没有被去重？**
A: 检查以下情况：
1. 新闻发布时间相差是否超过2小时（超过则不会去重）
2. 标题相似度是否低于阈值（默认0.50）
3. 查看 `local_deduplicator.py` 的日志输出

**Q: AI评分为什么失败？**
A: 检查：
1. DeepSeek API密钥是否正确配置
2. 网络连接是否正常
3. 查看后台日志中的错误信息

**Q: 定时任务没有运行？**
A: 确认：
1. `backend/main.py` 是否正在运行
2. 系统时间是否在工作时段（08:00-24:00）
3. 查看控制台日志中的 `[Auto-Pipeline]` 消息

**Q: 如何修改去重时间窗口？**
A: 编辑 `backend/main.py` 第1688行的 `time_window_hours` 参数，然后重启后端。

## 🙏 致谢

- [Playwright](https://playwright.dev/) - Web自动化框架
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架
- [React](https://react.dev/) - UI框架
- [Ant Design](https://ant.design/) - UI组件库
- [DeepSeek](https://www.deepseek.com/) - AI语言模型服务

## 📮 联系方式

如有问题或建议，欢迎：
- 提交 [Issue](https://github.com/your-username/AINEWS/issues)
- 发起 [Pull Request](https://github.com/your-username/AINEWS/pulls)

---

**⭐ 如果这个项目对你有帮助，欢迎点个Star！**
