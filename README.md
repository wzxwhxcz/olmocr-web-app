# olmOCR Web 服务 - Render 部署版

使用 olmOCR 工具包 + 外部 API 推理的 Web 应用，可以部署在 Render 上。

## ✨ 功能特性

- 📄 支持 PDF、PNG、JPEG 格式
- 🤖 使用外部 API 进行模型推理（无需 GPU）
- 🎨 简洁美观的 Web 界面
- 📝 输出 Markdown 格式
- 💾 支持复制和下载结果
- 🚀 一键部署到 Render

## 🏗️ 架构说明

```
用户 → Render Web 服务 → olmOCR 工具包 → 外部推理 API
                                          ↓
用户 ← Render Web 服务 ← Markdown 结果
```

**优势：**
- ✅ 不需要 GPU，可以使用 Render 免费套餐
- ✅ 使用外部 API，按需付费
- ✅ 简单易部署

## 📋 部署前准备

### 1. 注册外部推理服务（选择一个）

推荐 **DeepInfra**（性价比高）：

| 提供商 | 价格/百万输入 token | 价格/百万输出 token | 注册链接 |
|--------|-------------------|-------------------|---------|
| DeepInfra | $0.09 | $0.19 | https://deepinfra.com/ |
| Cirrascale | $0.07 | $0.15 | https://ai2endpoints.cirrascale.ai/ |
| Parasail | $0.10 | $0.20 | https://www.saas.parasail.io/ |

注册后获取你的 **API Key**。

### 2. 准备 GitHub 仓库

```bash
cd olmocr-render-app

# 初始化 Git 仓库
git init
git add .
git commit -m "Initial commit"

# 推送到 GitHub
git remote add origin https://github.com/你的用户名/olmocr-render-app.git
git branch -M main
git push -u origin main
```

## 🚀 部署到 Render

### 方法 1: 使用 Render Dashboard（推荐）

1. **登录 Render**
   - 访问 https://render.com/
   - 使用 GitHub 账号登录

2. **创建新的 Web 服务**
   - 点击 "New +" → "Web Service"
   - 连接你的 GitHub 仓库
   - 选择 `olmocr-render-app` 仓库

3. **配置服务**
   ```
   Name: olmocr-web
   Region: Oregon (US West) 或就近选择
   Branch: main
   Runtime: Python 3
   Build Command:
     apt-get update && apt-get install -y poppler-utils ttf-mscorefonts-installer msttcorefonts fonts-crosextra-caladea fonts-crosextra-carlito gsfonts lcdf-typetools && pip install -r requirements.txt
   Start Command: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 300
   ```

4. **设置环境变量**
   - 在 "Environment" 标签页添加：
   ```
   OLMOCR_PROVIDER=deepinfra
   OLMOCR_API_KEY=你的_API_KEY
   ```

5. **选择套餐**
   - 免费套餐：适合测试
   - Starter ($7/月)：适合生产使用

6. **部署**
   - 点击 "Create Web Service"
   - 等待部署完成（约 5-10 分钟）

### 方法 2: 使用 render.yaml（自动配置）

如果仓库包含 `render.yaml`，Render 会自动识别配置：

1. 在 Render Dashboard 点击 "New +" → "Blueprint"
2. 连接你的 GitHub 仓库
3. Render 会自动读取 `render.yaml` 配置
4. 在控制台设置环境变量 `OLMOCR_API_KEY`
5. 点击 "Apply" 开始部署

## 🧪 本地测试

在部署前，可以先在本地测试：

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key

# 3. 运行应用
python app.py

# 4. 访问
# 打开浏览器访问 http://localhost:5000
```

## 📝 使用说明

1. **访问你的 Render 应用**
   - 部署完成后，Render 会提供一个 URL
   - 例如：`https://olmocr-web.onrender.com`

2. **上传 PDF**
   - 点击上传区域或拖拽文件
   - 支持 PDF、PNG、JPG 格式
   - 最大 50MB

3. **等待处理**
   - 处理时间取决于文件大小
   - 通常 1-2 分钟

4. **查看结果**
   - 转换完成后显示 Markdown 内容
   - 可以复制或下载结果

## 💰 成本估算

### Render 费用
- **免费套餐**：750 小时/月（足够测试）
- **Starter 套餐**：$7/月（推荐生产使用）

### 推理 API 费用（使用 DeepInfra）
假设每页 PDF：
- 输入：~2000 tokens
- 输出：~1000 tokens

**示例成本：**
- 100 页：~$0.04
- 1000 页：~$0.37
- 10000 页：~$3.70

总成本非常低！

## 🔧 配置选项

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OLMOCR_PROVIDER` | 推理服务提供商 | `deepinfra` |
| `OLMOCR_API_KEY` | API 密钥 | 无（必需） |
| `PORT` | 服务端口 | `5000` |
| `DEBUG` | 调试模式 | `False` |

### 支持的提供商

- `deepinfra` - DeepInfra
- `cirrascale` - Cirrascale
- `parasail` - Parasail

## 🐛 故障排查

### 问题 1: 部署失败
```
错误: Could not find a version that satisfies the requirement...
解决: 检查 requirements.txt 中的依赖版本是否正确
```

### 问题 2: API Key 错误
```
错误: 未设置 OLMOCR_API_KEY 环境变量
解决: 在 Render 控制台的 Environment 标签页设置 API Key
```

### 问题 3: 处理超时
```
错误: 处理超时，请稍后重试
解决: 增加 gunicorn 的 timeout 参数（默认 300 秒）
```

### 问题 4: 依赖安装失败
```
错误: apt-get install 失败
解决: 检查 Build Command 是否包含系统依赖安装命令
```

## 📚 API 文档

### POST /api/convert

上传并转换 PDF 文件

**请求：**
```bash
curl -X POST \
  -F "file=@document.pdf" \
  https://your-app.onrender.com/api/convert
```

**响应：**
```json
{
  "success": true,
  "filename": "document.pdf",
  "markdown": "# 文档内容\n\n...",
  "job_id": "uuid"
}
```

### GET /api/providers

列出可用的推理服务提供商

**响应：**
```json
{
  "providers": ["deepinfra", "cirrascale", "parasail"],
  "current": "deepinfra"
}
```

### GET /health

健康检查

**响应：**
```json
{
  "status": "ok",
  "provider": "deepinfra",
  "api_key_configured": true
}
```

## 🔗 相关链接

- olmOCR GitHub: https://github.com/allenai/olmocr
- Render 文档: https://render.com/docs
- DeepInfra: https://deepinfra.com/
- Cirrascale: https://ai2endpoints.cirrascale.ai/
- Parasail: https://www.saas.parasail.io/

## 📄 许可证

本项目使用 Apache 2.0 许可证。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## ⭐ 功能路线图

- [ ] 支持批量上传
- [ ] 添加用户认证
- [ ] 支持更多输出格式
- [ ] 添加处理历史记录
- [ ] 集成 S3 存储
- [ ] 添加 WebSocket 实时进度

## 💡 技巧和建议

1. **免费套餐限制**
   - Render 免费套餐会在 15 分钟无活动后休眠
   - 第一次访问可能需要等待 30 秒唤醒

2. **性能优化**
   - 使用 Starter 套餐获得更好性能
   - 调整 `--workers` 参数优化并发

3. **安全建议**
   - 不要在代码中硬编码 API Key
   - 使用环境变量管理敏感信息
   - 考虑添加用户认证限制访问

4. **监控和日志**
   - 在 Render Dashboard 查看日志
   - 设置告警通知
   - 监控 API 使用量

---

**祝部署顺利！** 🎉

如有问题，欢迎提 Issue。
