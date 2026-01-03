# AINEWS 部署指南 (Target: new.blocknico.com)

本指南专门针对将 AINEWS 部署到服务器并使用域名 `new.blocknico.com` 的场景。

## 🎯 目标架构

- **域名**: `https://new.blocknico.com`
- **前端 (展示)**: `https://new.blocknico.com/` (NewsFeed)
- **前端 (管理)**: `https://new.blocknico.com/admin` (Dashboard)
- **后端 API**: `https://new.blocknico.com/api` (反向代理到本地 8000 端口)

## ✅ 1. 本地准备工作

在将代码上传到服务器之前，请确保本地配置正确。

1. **前端配置已更新**:
   - 路由已调整：首页 `/` 直接显示 NewsFeed。
   - 生产环境配置 (`frontend/.env.production`) 已设置为 `VITE_API_BASE_URL=https://new.blocknico.com`。

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

1. **上传/拉取代码**:
   ```bash
   # 假设代码在该目录
   mkdir -p /var/www/ainews
   cd /var/www/ainews
   # 使用 git pull 或 scp 上传代码
   ```

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

3. **配置 Systemd 服务 (守护进程)**:
   创建服务文件以保持后端一直运行。
   
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
   ExecStart=/var/www/ainews/venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000 --headers "X-Forwarded-Proto: https"
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
   `sudo nano /etc/nginx/sites-available/new.blocknico.com`

   ```nginx
   server {
       server_name new.blocknico.com;

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
   sudo ln -s /etc/nginx/sites-available/new.blocknico.com /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

3. **配置 SSL (HTTPS)**:
   使用 Certbot 自动配置 SSL。
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d new.blocknico.com
   ```
   按照提示完成配置。

## 🎉 6. 验证

访问 `https://new.blocknico.com`：
- 应该看到新闻列表页面。
- 只有登录状态下访问 `https://new.blocknico.com/admin` 才能看到管理仪表盘（否则跳转登录页）。
- 检查网络请求（F12 -> Network），确认 API 请求指向 `https://new.blocknico.com/api/...` 且状态为 200。
