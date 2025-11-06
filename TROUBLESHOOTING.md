# Render 部署故障排查指南

## 常见问题和解决方案

### 1. "此服务目前不可用" 错误

这个错误通常是由以下原因之一导致的:

#### 原因 A: 应用启动失败

**检查步骤:**
1. 登录 Render 控制台
2. 进入你的服务页面
3. 查看 "Logs" 选项卡
4. 查找错误信息

**常见错误和解决方案:**

- **ModuleNotFoundError**: 缺少依赖包
  ```
  解决: 检查 requirements.txt 是否包含所有依赖
  ```

- **ImportError**: 导入错误
  ```
  解决: 检查 app.py 中的 import 语句
  ```

- **FileNotFoundError**: 文件未找到
  ```
  解决: 检查 templates 目录是否存在
  ```

#### 原因 B: 环境变量未配置

**检查步骤:**
1. 在 Render 控制台,进入你的服务
2. 点击 "Environment" 选项卡
3. 确认以下环境变量已设置:
   - `OLMOCR_API_KEY` - **必需** (你的 API 密钥)
   - `OLMOCR_PROVIDER` - 可选 (默认: deepinfra)

**解决方案:**
1. 点击 "Add Environment Variable"
2. 添加 `OLMOCR_API_KEY`
3. 粘贴你的 API 密钥
4. 点击 "Save Changes"

#### 原因 C: 构建失败

**检查步骤:**
1. 在 Render 控制台查看 "Events" 选项卡
2. 查找最近的部署事件
3. 点击 "View Build" 查看构建日志

**常见构建错误:**

- **apt-get 失败**: 系统包安装失败
  ```yaml
  # render.yaml 中确保有这行:
  buildCommand: |
    apt-get update && apt-get install -y poppler-utils ttf-mscorefonts-installer
    pip install --upgrade pip
    pip install -r requirements.txt
  ```

- **pip install 失败**: Python 包安装失败
  ```
  解决: 检查 requirements.txt 中的包版本是否兼容
  ```

#### 原因 D: 端口配置问题

**检查步骤:**
确认 Render 使用正确的启动命令

**在 render.yaml 中:**
```yaml
startCommand: gunicorn app:app
```

**在 Procfile 中:**
```
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 300
```

Render 会自动设置 `$PORT` 环境变量。

#### 原因 E: 应用崩溃或超时

**检查步骤:**
1. 查看日志中的错误堆栈
2. 检查是否有未捕获的异常

**解决方案:**
- 增加启动超时时间
- 检查代码中的异常处理
- 确保所有依赖都已安装

### 2. 健康检查失败

**症状**: 服务显示 "Unhealthy" 或频繁重启

**解决方案:**

1. **检查 /health 端点:**
   ```bash
   curl https://your-app.onrender.com/health
   ```

2. **确认应用正常响应:**
   ```json
   {
     "status": "ok",
     "provider": "deepinfra",
     "api_url": "...",
     "model": "...",
     "api_key_configured": true
   }
   ```

3. **如果 health 端点失败:**
   - 检查 Flask 路由是否正确
   - 查看应用日志中的错误

### 3. 日志相关问题

**问题**: 最新的更新添加了日志功能,可能导致启动失败

**解决方案**: 已修复为使用临时目录,并添加了错误处理:

```python
# 日志会尝试写入临时目录
# 如果失败,只输出到控制台
log_file = os.path.join(tempfile.gettempdir(), 'olmocr_app.log')
```

### 4. 查看详细日志

**在 Render 控制台:**
1. 进入你的服务
2. 点击 "Logs" 选项卡
3. 使用搜索功能查找错误

**常用搜索关键词:**
- `ERROR` - 错误信息
- `WARNING` - 警告信息
- `启动` - 启动日志
- `处理失败` - 处理错误

### 5. 手动部署触发

如果自动部署失败:

1. 在 Render 控制台,进入你的服务
2. 点击右上角 "Manual Deploy"
3. 选择 "Clear build cache & deploy"
4. 观察构建和部署过程

### 6. 测试 API Key 配置

使用健康检查端点测试配置:

```bash
curl https://your-app.onrender.com/health
```

检查响应中的 `api_key_configured` 字段:
- `true` - API Key 已配置
- `false` - API Key 未配置 (需要在环境变量中添加)

### 7. 常见错误代码

- **503 Service Unavailable**: 应用未启动或崩溃
- **502 Bad Gateway**: 应用启动中或端口配置错误
- **500 Internal Server Error**: 应用运行时错误
- **404 Not Found**: 路由不存在

## 快速修复清单

在 Render 控制台依次检查:

- [ ] 服务状态是否为 "Live"
- [ ] 最近的部署是否成功
- [ ] 构建日志是否有错误
- [ ] 运行日志是否有错误
- [ ] 环境变量 `OLMOCR_API_KEY` 是否已设置
- [ ] 健康检查端点 `/health` 是否可访问

## 获取帮助

如果以上方法都无法解决问题:

1. **导出日志**: 在 Render 控制台复制完整的日志
2. **记录错误信息**: 截图错误页面
3. **检查 GitHub Issues**: 查看是否有类似问题
4. **联系支持**: 提供详细的错误信息和日志

## 最新更新相关问题

如果问题在最新更新后出现:

1. **回滚到上一个版本:**
   ```bash
   git revert HEAD
   git push origin master
   ```

2. **查看更新内容:**
   - 检查 CHANGELOG.md
   - 对比 git diff

3. **手动测试:**
   ```bash
   # 本地测试
   python app.py
   ```

## Render 特定配置

确保 render.yaml 配置正确:

```yaml
services:
  - type: web
    name: olmocr-web
    env: python
    region: oregon  # 或其他区域
    plan: starter   # 或其他套餐
    buildCommand: |
      apt-get update && apt-get install -y poppler-utils ttf-mscorefonts-installer
      pip install --upgrade pip
      pip install -r requirements.txt
    startCommand: gunicorn app:app
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: OLMOCR_PROVIDER
        value: deepinfra
      - key: OLMOCR_API_KEY
        sync: false
```

## 联系信息

- GitHub 仓库: https://github.com/wzxwhxcz/olmocr-web-app
- Render 文档: https://render.com/docs
