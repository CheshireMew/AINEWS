# AINews项目 - 当前状态

## ✅ 已完成的核心功能

### 1. 数据库层 (100%)
- ✅ 完整的PostgreSQL Schema设计
- ✅ 多阶段数据保存（raw → filtered → ai_processed → pushed）
- ✅ 处理日志记录
- ✅ 去重支持
- ✅ 统计数据收集

### 2. 爬虫系统 (100% - 8个网站)
所有爬虫已实现，支持**三种识别方法**：

#### 通用样式判断 ⭐
- 颜色检测（红色、橙色）
- 字体粗细（bold >= 600）
- 字体大小（>= 18px）

#### 已实现的爬虫
1. ✅ **深潮TechFlow** - CSS类 + 首发图标 + 样式
2. ✅ **Odaily** - 火焰图标 + 样式
3. ✅ **TheBlockBeats** - first徽章 + 样式
4. ✅ **Foresight News** - redcolor类 + 样式
5. ✅ **ChainCatcher** - 样式判断（主）
6. ✅ **PANews** - 样式判断（主）
7. ✅ **MarsBit** - 样式判断（主）
8. ✅ **Followin** - 样式判断（主）

### 3. 过滤系统 (100%)
- ✅ 正则黑名单（过滤低价值新闻）
- ✅ 正则白名单（强制保留重要新闻）
- ✅ 关键词黑白名单
- ✅ 长度过滤
- ✅ 规则命中统计

### 4. AI模块 (100%)
- ✅ **AI标签生成器**
  - 自动生成2-4个标签
  - 价值评分（0-100）
  - 一句话总结
  - 使用DeepSeek API

- ✅ **AI去重检测器**
  - 24小时窗口检测
  - 语义相似度对比
  - 自动合并来源

### 5. 主程序 (100%)
- ✅ 完整流程整合
- ✅ 每个阶段保存数据
- ✅ 详细日志记录
- ✅ 错误处理
- ✅ 测试模式（--dry-run）

---

## 📋 待完成功能

### Phase 3: Telegram推送 (0%)
- [ ] Telegram Bot集成
- [ ] 消息格式化
- [ ] 批量推送
- [ ] 定时任务（每天3次）
- [ ] 推送日志

### Phase 4: Web管理界面 (0%)
- [ ] Node.js API后端
  - [ ] 新闻列表API
  - [ ] 标签管理API
  - [ ] 统计数据API
- [ ] React前端
  - [ ] 新闻浏览页
  - [ ] 标签管理页
  - [ ] 数据统计页
  - [ ] 误杀审核功能

### Phase 5: 部署 (0%)
- [ ] Systemd服务配置
- [ ] Nginx配置
- [ ] 定时任务配置
- [ ] 监控告警

---

## 🧪 测试指南

### 前提条件
```bash
# 1. 安装PostgreSQL (Debian 13)
sudo apt update && sudo apt install -y postgresql

# 2. 创建数据库
sudo -u postgres psql
CREATE DATABASE ainews;
CREATE USER newsbot WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ainews TO newsbot;
\q

# 3. 初始化数据库
psql -U newsbot -d ainews -f database/schema.sql
psql -U newsbot -d ainews -f database/init_tags.sql
```

### 测试单个爬虫
```bash
cd crawler

# 测试深潮TechFlow
python scrapers/techflow.py

# 测试Odaily
python scrapers/odaily.py

# 测试其他爬虫...
```

### 测试关键词过滤
```bash
python filters/keyword_filter.py
```

### 测试完整流程（需要配置.env）
```bash
# 1. 配置环境变量
cp ../.env.example .env
# 编辑.env，填入：
# - DATABASE_URL
# - DEEPSEEK_API_KEY

# 2. 测试运行（不推送）
python main.py --dry-run
```

### 环境变量说明
```bash
# 必需
DATABASE_URL=postgresql://newsbot:password@localhost:5432/ainews
DEEPSEEK_API_KEY=sk-xxxxx  # 从 platform.deepseek.com 获取

# 可选（推送时需要）
TELEGRAM_BOT_TOKEN=123456:ABC-xxx
TELEGRAM_CHANNEL_ID=@your_channel
```

---

## 📊 数据流程

```
1. 抓取 (8个网站)
   ├─ 网站重要标记识别
   ├─ 样式判断（通用方法）
   └─ 保存原始数据 (stage=raw)
   
2. 关键词过滤
   ├─ 白名单优先（强制保留）
   ├─ 黑名单检查
   └─ 更新 (stage=keyword_filtered 或保持raw)
   
3. AI标签生成
   ├─ DeepSeek生成标签
   ├─ 价值评分
   ├─ 一句话总结
   └─ 更新 (stage=ai_processed)
   
4. AI去重
   ├─ 24小时窗口检测
   ├─ 相似度计算
   └─ 标记重复 + 合并来源
   
5. 推送 (TODO)
   └─ Telegram频道
```

---

## 🎯 下一步建议

### 优先级1：Telegram推送
实现基本的推送功能，让系统可用：
1. 创建 `pusher/telegram_bot.py`
2. 实现消息格式化
3. 配置定时任务

### 优先级2：测试验证
1. 在VPS上测试所有爬虫
2. 验证AI标签质量
3. 调优过滤规则

### 优先级3：Web界面
实现管理后台，方便调整和查看

---

## 💡 关键特性

1. **通用样式判断** - 即使网站改版也能识别
2. **多阶段保存** - 完整追溯每条新闻处理过程
3. **AI去重** - 自动合并不同媒体的重复报道
4. **灵活配置** - YAML配置文件，无需改代码

---

## 🔧 技术栈

- **Python 3.10+**: 爬虫和AI处理
- **Playwright**: 动态网页渲染
- **PostgreSQL**: 数据存储
- **DeepSeek**: AI标签和去重
- **Node.js + React**: Web管理界面（待实现）
- **python-telegram-bot**: 推送（待实现）
