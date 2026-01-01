# 分析师API测试指南

## 问题诊断

从日志看到：
```
INFO: 127.0.0.1:14188 - "POST /api/analyst/keys HTTP/1.1" 404 Not Found
```

原因：后端重启不完全，新的API端点没有加载。

## 解决方案和测试步骤

### 步骤1：完全重启后端

**重要**：必须完全停止后端进程并重新启动！

```powershell
# 在后端终端按 Ctrl+C 停止
# 然后重新运行
cd e:\Work\Code\AINEWS
python backend/main.py
```

**验证启动成功**：
- 看到 `INFO:     Uvicorn running on http://0.0.0.0:8000`
- 看到 `✅ SQLite数据库初始化完成`
- 没有报错信息

### 步骤2：测试Web界面

1. **打开浏览器**：访问 `http://localhost:3000`

2. **进入API配置Tab**：
   - 点击左侧导航的"API配置"
   - 应该看到"分析师API密钥管理"卡片

3. **创建第一个密钥**：
   - 点击右上角"创建新密钥"按钮
   - 在弹出的Modal中输入：
     - 密钥名称：`测试密钥`
     - 备注：`测试用途`（可选）
   - 点击"创建"按钮

4. **查看结果**：
   - 应该看到成功提示："已为 '测试密钥' 创建密钥"
   - 表格中出现新的一行，显示密钥信息
   - 点击"复制"按钮可以复制密钥

5. **测试删除**：
   - 点击某个密钥行的"删除"按钮
   - 确认删除对话框
   - 密钥应该从列表中消失

### 步骤3：使用cURL测试API（推荐）

#### 3.1 创建密钥（通过Web界面或cURL）

通过Web界面创建后，复制生成的密钥，或使用cURL直接创建：

```powershell
# 创建新密钥
curl -X POST "http://localhost:8000/api/analyst/keys" `
  -H "Content-Type: application/json" `
  -d '{"key_name": "cURL测试", "notes": "通过cURL创建"}'
```

**成功响应示例**：
```json
{
  "success": true,
  "message": "已为 'cURL测试' 创建密钥",
  "data": {
    "id": 1,
    "key_name": "cURL测试",
    "api_key": "analyst_abc123...",
    "notes": "通过cURL创建"
  }
}
```

#### 3.2 获取所有密钥列表

```powershell
curl "http://localhost:8000/api/analyst/keys"
```

#### 3.3 测试新闻API（使用生成的密钥）

```powershell
# 替换 YOUR_API_KEY 为实际的密钥
curl "http://localhost:8000/api/analyst/news?api_key=analyst_YOUR_KEY_HERE&hours=24&min_score=7"
```

**成功响应示例**：
```json
{
  "success": true,
  "message": "成功获取 5 条新闻",
  "data": {
    "news": [
      {
        "id": 123,
        "title": "比特币突破10万美元",
        "content": "...",
        "source_url": "https://...",
        "source_site": "blockbeats",
        "published_at": "2025-12-27 10:00:00",
        "ai_score": 8.5,
        "ai_summary": "..."
      }
    ],
    "metadata": {
      "count": 5,
      "time_range_hours": 24,
      "min_score": 7,
      "query_time": "2025-12-27 11:30:00"
    }
  }
}
```

### 步骤4：使用Python脚本测试

创建测试文件 `test_analyst_api.py`：

```python
import requests
import json

BASE_URL = "http://localhost:8000"

def test_create_key():
    """测试创建密钥"""
    print("\n=== 测试1：创建API密钥 ===")
    response = requests.post(
        f"{BASE_URL}/api/analyst/keys",
        json={"key_name": "Python测试", "notes": "自动化测试"}
    )
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    if data['success']:
        return data['data']['api_key']
    return None

def test_get_keys():
    """测试获取密钥列表"""
    print("\n=== 测试2：获取密钥列表 ===")
    response = requests.get(f"{BASE_URL}/api/analyst/keys")
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"找到 {len(data['data'])} 个密钥")
    for key in data['data']:
        print(f"- {key['key_name']}: {key['api_key'][:20]}...")

def test_get_news(api_key):
    """测试获取新闻API"""
    print("\n=== 测试3：获取新闻数据 ===")
    response = requests.get(
        f"{BASE_URL}/api/analyst/news",
        params={
            "api_key": api_key,
            "hours": 24,
            "min_score": 6,
            "limit": 5
        }
    )
    print(f"状态码: {response.status_code}")
    data = response.json()
    
    if data['success']:
        print(f"成功获取 {data['data']['metadata']['count']} 条新闻")
        for news in data['data']['news'][:3]:  # 只显示前3条
            print(f"\n标题: {news['title']}")
            print(f"评分: {news['ai_score']}")
            print(f"来源: {news['source_site']}")
    else:
        print(f"失败: {data.get('message', '未知错误')}")

def test_invalid_key():
    """测试无效密钥"""
    print("\n=== 测试4：测试无效密钥 ===")
    response = requests.get(
        f"{BASE_URL}/api/analyst/news",
        params={"api_key": "invalid_key_123", "hours": 24}
    )
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"错误信息: {data.get('message', data)}")

if __name__ == "__main__":
    print("开始测试分析师API...")
    
    # 测试1：创建密钥
    api_key = test_create_key()
    
    # 测试2：获取列表
    test_get_keys()
    
    # 测试3：使用密钥获取新闻
    if api_key:
        test_get_news(api_key)
    
    # 测试4：无效密钥
    test_invalid_key()
    
    print("\n测试完成！")
```

**运行测试**：
```powershell
python test_analyst_api.py
```

## 常见问题

### Q1: 仍然返回404
**解决**：
1. 确保后端完全重启（Ctrl+C停止，重新运行）
2. 检查后端日志是否有启动错误
3. 访问 `http://localhost:8000/docs` 查看API文档

### Q2: 401错误"无效的API密钥"
**原因**：密钥不存在或已删除
**解决**：通过Web界面重新创建密钥

### Q3: 返回空数据
**原因**：数据库中没有符合条件的新闻
**解决**：
- 降低 `min_score` 参数（如改为3）
- 增加 `hours` 参数（如改为168）

### Q4: Web界面报错
**检查**：
1. 打开浏览器开发者工具（F12）
2. 查看Console和Network标签
3. 看具体的错误信息

## 下一步

测试成功后，你可以：
1. 将API密钥分享给朋友
2. 让他们参考 `API_DOCUMENTATION.md` 使用API
3. 在"最后使用"列查看每个密钥的使用情况
4. 根据需要删除不再使用的密钥
