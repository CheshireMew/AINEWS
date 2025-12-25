# AINews 爬虫实现策略

## 重要新闻识别方法

根据网站特点，我们使用多种方式识别"重要新闻"：

### 1. 特定CSS类名
某些网站会给重要新闻添加特定的class：
- **深潮TechFlow**: `c002CCC` 类
- **Foresight News**: `redcolor` 类

### 2. 图标标识
使用特殊图标标记重要性：
- **深潮TechFlow**: `first_pub_ico.svg` （首发图标）
- **Odaily**: `hot.1b4e7492.svg` （火焰图标）
- **TheBlockBeats**: 闪电"first"徽章

### 3. CSS样式判断 ⭐ **通用方法**
通过计算样式（`window.getComputedStyle`）判断：

#### 颜色判断
- **红色系**: `rgb(r, g, b)` 其中 `r > 200` 且 `r > g+50` 且 `r > b+50`
- **橙色/金色**: `r > 200` 且 `g > 100` 且 `b < 100`

#### 字体粗细
- `font-weight: bold` 或数值 `>= 600`

#### 字体大小
- `font-size >= 18px`

### 实现代码

```python
# 在BaseScraper中
style_check = await self.check_importance_by_style(title_element)

if style_check['is_important']:
    # 这是重要新闻
    site_importance_flag = style_check['style_flag']  # 如 "red_color+bold_font"
```

### 优先级策略

对于每个网站，建议使用**多重检查**：

```python
is_important = (
    has_special_class or        # CSS类名
    has_special_icon or         # 图标
    style_check['is_important'] # 样式判断（兜底）
)
```

这样即使网站改版，只要视觉上仍标记为重要（红色/粗体），我们仍能识别。

## 各网站具体策略

| 网站 | 主要方法 | 备用方法 | 样式特征 |
|------|---------|---------|---------|
| TechFlow | CSS类`c002CCC` | 样式检查 | 可能有特殊颜色 |
| Odaily | 火焰图标 | 样式检查 | 红色标题 |
| BlockBeats | "first"徽章 | 样式检查 | 粗体/特殊色 |
| Foresight | CSS类`redcolor` | 样式检查 | 红色 |
| ChainCatcher | 待确认 | **样式检查** | 可能粗体/红色 |
| PANews | 待确认 | **样式检查** | 可能粗体/红色 |
| MarsBit | 待确认 | **样式检查** | 可能粗体/红色 |
| Followin | 待确认 | **样式检查** | 可能粗体/红色 |

对于未确认的网站，**样式检查是最通用的方法**。
