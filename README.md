# AINews - 智能新闻聚合与AI筛选系统

> 🚀 基于 Python + FastAPI + React 的全栈新闻聚合系统，支持多源爬取、AI智能筛选、自动去重和Web管理

## ✨ 核心特性

- **🕷️ 多源智能爬虫**
  - 支持多个主流区块链/加密货币新闻网站
  - 自动识别网站重要标记（如"只看精选"）
  - 增量爬取，避免重复抓取
  - 基于 Playwright 实现动态网页抓取

- **🔍 三级智能筛选**
  1. **网站原生标记**: 优先抓取网站自带的"重要"/"精选"标记
  2. **本地黑名单过滤**: 可配置关键词黑名单（支持正则表达式）
  3. **AI智能评分**: 基于DeepSeek的语义分析和评分

- **🎯 智能去重**
  - 基于标题相似度的自动去重
  - 支持手动调整去重阈值
  - 完整保留去重历史记录

- **💻 Web管理界面**
  - 数据管理：原始新闻、去重数据、精选数据
  - AI筛选：批量AI评分、查看拒绝/通过原因
  - 配置管理：黑名单管理、爬虫配置
  - 数据导出：支持多种格式（纯文本、Markdown、Telegram富文本）

- **📦 完整数据追溯**
  - 记录新闻从抓取到发布的完整流程
  - 支持数据回滚和批量还原

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
│   │   ├── api/          # API调用封装
│   │   └── App.jsx       # 应用主入口
│   └── vite.config.js    # Vite配置
│
├── ainews.db              # SQLite数据库（.gitignore已排除）
├── .env.example           # 环境变量模板
├── .gitignore            # Git忽略规则
└── README.md             # 本文件
```

## 🎯 使用流程

1. **爬虫抓取**: 运行 `crawler/main.py`，自动抓取各网站重要新闻
2. **自动去重**: 系统自动识别重复新闻并合并
3. **本地过滤**: 在Web界面配置黑名单，过滤不需要的内容
4. **AI筛选**: 使用DeepSeek AI对精选新闻进行评分和分类
5. **数据导出**: 导出符合条件的新闻（支持多种格式）

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

## 🤝 贡献指南

欢迎贡献代码！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细的贡献流程。

## 📄 许可证

本项目采用 MIT License - 详见 [LICENSE](LICENSE) 文件

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
