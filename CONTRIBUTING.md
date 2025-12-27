# Contributing to AINews

感谢你考虑为 AINews 做出贡献！我们欢迎任何形式的贡献，包括但不限于：

- 🐛 报告Bug
- 💡 提出新功能建议
-  📝 改进文档
- 🔧 提交代码修复或新功能
- 🌐 添加新的爬虫支持

## 📋 行为准则

请确保在参与本项目时保持友好和尊重的态度。我们致力于营造一个开放和包容的社区环境。

## 🐛 报告Bug

如果你发现了Bug，请遵循以下步骤：

1. **检查现有Issues**: 在提交新Issue前，请先搜索[现有Issues](https://github.com/your-username/AINEWS/issues)，避免重复
2. **使用Issue模板**: 创建新Issue时，请提供以下信息：
   - Bug的详细描述
   - 复现步骤
   - 预期行为 vs 实际行为
   - 环境信息（操作系统、Python版本、Node版本等）
   - 相关日志或截图

### Bug报告示例

```markdown
**描述**
简洁描述Bug是什么

**复现步骤**
1. 启动爬虫 `python crawler/main.py`
2. 访问某个特定URL
3. 观察到错误...

**预期行为**
应该正常抓取新闻...

**实际行为**
出现错误: xxx

**环境**
- OS: Windows 11
- Python: 3.10.5
- Node: 18.16.0
```

## 💡 功能建议

我们欢迎新功能建议！请通过Issue描述你的想法：

1. **功能的使用场景**: 为什么需要这个功能？
2. **预期实现方式**: 你希望它如何工作？
3. **替代方案**: 是否有其他解决方法？

## 🔧 提交代码

### 开发环境设置

```bash
# 1. Fork 本仓库到你的GitHub账号

# 2. Clone你的Fork
git clone https://github.com/YOUR_USERNAME/AINEWS.git
cd AINEWS

# 3. 添加上游仓库
git remote add upstream https://github.com/original-owner/AINEWS.git

# 4. 安装开发依赖
cd crawler && pip install -r requirements.txt
cd ../backend && pip install -r requirements.txt
cd ../frontend && npm install
```

### 开发流程

1. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/bug-description
   ```

2. **编写代码**
   - 遵循项目的代码规范（见下方）
   - 添加必要的注释
   - 如果修改了API，请更新文档

3. **测试你的修改**
   ```bash
   # 测试爬虫
   cd crawler && python main.py --dry-run
   
   # 测试后端
   cd backend && python main.py
   
   # 测试前端
   cd frontend && npm run dev
   ```

4. **提交更改**
   ```bash
   git add .
   git commit -m "feat: 添加XXX功能" 
   # 或
   git commit -m "fix: 修复XXX问题"
   ```

5. **推送到你的Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **创建Pull Request**
   - 在GitHub上从你的分支创建PR到上游仓库的 `main` 分支
   - 在PR描述中清楚说明你的修改
   - 链接相关的Issue（如果有）

### Commit Message规范

我们建议使用语义化的commit message：

- `feat: 添加新功能`
- `fix: 修复Bug`
- `docs: 更新文档`
- `style: 代码格式调整（不影响功能）`
- `refactor: 代码重构`
- `test: 添加测试`
- `chore: 构建/工具相关的更改`

**示例**:
```
feat: 添加Binance爬虫支持

- 实现Binance新闻页面的爬取逻辑
- 添加内容清理和时间解析
- 更新文档说明

Closes #123
```

## 📝 代码规范

### Python代码规范（爬虫/后端）

- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 风格指南
- 使用有意义的变量名和函数名
- 添加类型提示（Type Hints）
- 为复杂逻辑添加注释
- 模块开头添加docstring说明

**示例**:
```python
from typing import List, Dict

class NewsScraper:
    \"\"\"新闻爬虫基类\"\"\"
    
    def fetch_news(self, limit: int = 10) -> List[Dict]:
        \"\"\"抓取新闻列表
        
        Args:
            limit: 最多抓取的新闻数量
            
        Returns:
            新闻字典列表，包含title、url、published_at等字段
        \"\"\"
        pass
```

### JavaScript/React代码规范（前端）

- 使用函数式组件和Hooks
- 变量和函数名使用camelCase
- 组件名使用PascalCase
- 为Props添加PropTypes验证
- 提取可复用的组件和逻辑

**示例**:
```javascript
import PropTypes from 'prop-types';

const NewsCard = ({ title, url, publishedAt }) => {
    // ...implementation
};

NewsCard.propTypes = {
    title: PropTypes.string.isRequired,
    url: PropTypes.string.isRequired,
    publishedAt: PropTypes.string
};

export default NewsCard;
```

### 数据库操作规范

- 所有数据库操作应在 `database/` 目录中实现
- 使用参数化查询，避免SQL注入
- 为事务性操作添加错误处理
- 记录重要操作的日志

## 🕷️ 添加新爬虫

如果你想为新的新闻网站添加爬虫支撑，请遵循以下步骤：

1. **继承BaseScraper类**
   ```python
   # crawler/scrapers/your_site.py
   from .base import BaseScraper
   
   class YourSiteScraper(BaseScraper):
       def __init__(self):
           super().__init__(
               name="yoursite",
               base_url="https://example.com",
               list_url="https://example.com/news"
           )
       
       async def parse_list(self, page):
           # 实现列表页解析
           pass
       
       async def fetch_full_content(self, url):
           # 实现详情页抓取
           pass
   ```

2. **注册爬虫**
   在 `crawler/main.py` 中添加你的爬虫

3. **测试爬虫**
   ```bash
   python crawler/main.py --scraper=yoursite --dry-run
   ```

4. **更新文档**
   - 在README.md中添加支持的网站说明
   - 如果有特殊配置，更新配置文档

## ❓ 获取帮助

如果你在开发过程中遇到问题：

1. **查看文档**:
   - [README.md](README.md) - 项目概览
   - [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md) - 详细文档
   - [VIBE_CODING_GUIDE.md](VIBE_CODING_GUIDE.md) - 编码指南

2. **搜索Issues**: 可能已有人遇到过同样的问题

3. **提问**: 在Issue中提问，我们会尽快回复

## 📄 许可证

通过贡献代码，你同意你的贡献将遵循本项目的 MIT License。

---

再次感谢你的贡献！🎉
