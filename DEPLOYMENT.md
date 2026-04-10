# AINEWS 部署指南 (Target: new.blacknico.com)

本指南专门针对将 AINEWS 部署到服务器并使用域名 `new.blacknico.com` 的场景。

## 🎯 目标架构

- **域名**: `https://new.blacknico.com`
- **前端 (展示)**: `https://new.blacknico.com/` (NewsFeed)
- **前端 (管理)**: `https://new.blacknico.com/admin` (Dashboard)
- **后端 API**: `https://new.blacknico.com/api` (反向代理到本地 8000 端口)

## ✅ 1. 本地准备工作

在将代码上传到服务器之前，请确保本地配置正确。

1. **前端配置已更新**:

   - 路由已调整：首页 `/` 直接显示 NewsFeed。
   - 生产环境配置 (`frontend/.env.production`) 已设置为 `VITE_API_BASE_URL=https://new.blacknico.com`。

2. **构建前端**:
   在本地运行构建命令，生成静态文件：

   ```bash
   cd frontend
   npm run build
   # 生成的文件位于 frontend/dist 目录
   ```

3. **后端代码准备**:
   确保 `backend/main.py` 和 `requirements.txt` 是最新的。

## 🚀 2. 服务器环境准备 (Ubuntu/Debian 示例)

登录您的服务器，安装必要的软件：

0. **检查已安装软件** (可选):
   如果您不确定是否已安装 Node.js，请运行：
   ```bash
   node -v
   npm -v
   ```
   如果显示版本号（如 v18.x.x），则无需重复安装 Node.js。

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Python 3.10+, Node.js, Nginx, Git
sudo apt install python3 python3-pip python3-venv nginx git -y

# 安装 Node.js (如果需要在线构建，可选)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

## 📦 3. 后端部署

建议将项目代码放在 `/var/www/ainews` 目录。

1. **拉取代码 (首次部署)**:

   ```bash
   # 创建目录
   sudo mkdir -p /var/www/ainews
   # 设置权限（将 current_user 替换为您的用户名，如 ubuntu）
   sudo chown -R $USER:$USER /var/www/ainews

   # 克隆代码
   git clone <您的GitHub仓库地址> /var/www/ainews

   # 💡 私有仓库提示：
   # 如果是私有仓库，推荐使用 Personal Access Token (PAT) 拉取：
   # git clone https://<your_token>@github.com/<username>/<repo>.git /var/www/ainews

   cd /var/www/ainews
   ```

   _(如果是后续更新代码，只需在目录内执行 `git pull origin main`)_

2. **设置 Python 环境**:

   ```bash
   cd /var/www/ainews
   python3 -m venv venv
   source venv/bin/activate

   # 安装依赖
   pip install -r crawler/requirements.txt
   pip install uvicorn[standard]

   # 安装 Playwright 浏览器
   playwright install chromium

   # 确保 deps
   playwright install-deps
   ```

3. **配置 Systemd 服务 (实现 24/7 运行)**:
   这是**最关键**的一步。使用 Systemd 守护进程可以确保：

   - 您的后端程序在后台 **24 小时不间断运行**。
   - 即使程序意外崩溃或服务器重启，它也会 **自动重启**。

   创建服务文件：
   `sudo nano /etc/systemd/system/ainews-backend.service`

   ```ini
   [Unit]
   Description=AINEWS Backend Service
   After=network.target

   [Service]
   User=root
   # 如果不是root用户，请修改为实际用户
   WorkingDirectory=/var/www/ainews
   Environment="PATH=/var/www/ainews/venv/bin:/usr/local/bin:/usr/bin:/bin"
   ExecStart=/var/www/ainews/venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000 --proxy-headers --forwarded-allow-ips '*'
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   **启动服务**:

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable ainews-backend
   sudo systemctl start ainews-backend
   sudo systemctl status ainews-backend
   ```

## 🎨 4. 前端部署

将本地构建好的 `frontend/dist` 文件夹上传到服务器的 `/var/www/ainews/frontend/dist`。

```bash
# 确保目录存在
mkdir -p /var/www/ainews/frontend/dist

# (本地操作) 上传文件
# scp -r frontend/dist/* user@your-server:/var/www/ainews/frontend/dist/
```

## 🌐 5. Nginx 配置 (核心步骤)

配置 Nginx 处理域名、SSL 和反向代理。

1. **创建配置文件**:
   `sudo nano /etc/nginx/sites-available/new.blacknico.com`

   ```nginx
   server {
       server_name new.blacknico.com;

       # 前端静态文件根目录
       root /var/www/ainews/frontend/dist;
       index index.html;

       # 核心：处理 SPA 路由
       # 任何找不到的文件都重定向到 index.html，交给 React Router 处理
       location / {
           try_files $uri $uri/ /index.html;
       }

       # 后端 API 反向代理
       location /api/ {
           proxy_pass http://127.0.0.1:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }

       # 静态资源缓存优化 (可选)
       location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
           expires 30d;
           add_header Cache-Control "public, no-transform";
       }
   }
   ```

2. **启用站点**:

   ```bash
   sudo ln -s /etc/nginx/sites-available/new.blacknico.com /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

3. **配置 SSL (HTTPS)**:
   使用 Certbot 自动配置 SSL。
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d new.blacknico.com
   ```
   按照提示完成配置。

## 🎉 6. 验证

访问 `https://new.blacknico.com`：

- 应该看到新闻列表页面。
- 只有登录状态下访问 `https://new.blacknico.com/admin` 才能看到管理仪表盘（否则跳转登录页）。
- 检查网络请求（F12 -> Network），确认 API 请求指向 `https://new.blacknico.com/api/...` 且状态为 200。

---

# AINEWS 项目下线方案 (Decommissioning Plan)

本方案旨在安全地将 AINEWS 项目从您的 VPS 服务器上下线，停止其运行并防止外界访问。

## 问题背景与原因

下线项目通常是为了：

1. **节省资源**：停止后台运行的爬虫、API 和数据库，释放 CPU 和内存。
2. **安全性**：防止未经授权的访问或潜在的漏洞利用（如果您不再维护该项目）。
3. **域名迁移**：为该域名指向新的项目做准备。

根据 `DEPLOYMENT.md` 的记录，您的项目包含两个主要运行组件：

- **后端 (FastAPI)**：由 `systemd` 守护进程管理。
- **前端 (React)**：由 `Nginx` 作为静态服务器和反向代理提供服务。

## 详细操作步骤 (Full Detailed Steps)

请按顺序在您的 VPS 服务器上执行以下命令：

### 1. 停止并禁用后端服务

首先停止正在运行的 Python 后端程序。

```bash
sudo systemctl stop ainews-backend
sudo systemctl disable ainews-backend
```

### 2. 下线 Nginx 站点配置

移除 Nginx 的启用链接，使域名不再指向该项目。

```bash
# 1. 移除启用链接
sudo rm /etc/nginx/sites-enabled/new.blacknico.com
# 2. 测试 Nginx 配置并重载
sudo nginx -t
sudo systemctl reload nginx
```

### 3. 备份数据库 (重要)

在彻底删除前，建议将数据库文件备份到您的用户主目录。

```bash
# 复制数据库到用户主目录
cp /var/www/ainews/ainews.db ~/ainews_backup_$(date +%F).db
```

> [!TIP]
> 备份后，您可以考虑使用 `scp` 等工具将其下载到本地保存。

### 4. 彻底删除项目文件与配置 (不可逆)

确认备份完成后，执行以下命令清理服务器。

```bash
# 1. 删除 systemd 服务文件
sudo rm /etc/systemd/system/ainews-backend.service
sudo systemctl daemon-reload

# 2. 删除 Nginx 源配置文件 (sites-available 中的源文件)
sudo rm /etc/nginx/sites-available/new.blacknico.com

# 3. 删除整个项目目录 (包含代码、虚拟环境、前端打包文件和数据库)
sudo rm -rf /var/www/ainews
```

## 验证计划

### 手动验证

- **访问域名**: 在浏览器中访问 `https://new.blacknico.com`，应该看到 Nginx 的默认页面或“无法连接”错误。
- **确认服务不存在**:
  - 运行 `sudo systemctl status ainews-backend`，应该提示 `Unit ainews-backend.service could not be found.`。
- **确认文件已删除**:
  - 运行 `ls /var/www/ainews`，应该提示 `No such file or directory`。

> [!IMPORTANT]
> 备份是您的最后一道防线。请确保步骤 3 中的数据库备份已成功完成并已下载到您的本地电脑或移动到其他安全位置。
