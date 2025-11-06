# 自定义 API 配置指南

## 🎯 功能说明

除了内置的推理服务提供商（DeepInfra、Cirrascale、Parasail），现在支持使用**自定义 API 端点**！

## 🔧 使用场景

### 1. 自己部署的 vLLM 服务器

如果你有自己的 GPU 服务器运行 vLLM：

```bash
# 在你的 GPU 服务器上启动 vLLM
vllm serve allenai/olmOCR-2-7B-1025 \
  --served-model-name olmocr \
  --max-model-len 16384 \
  --port 8000
```

在 Render 环境变量中设置：
```
OLMOCR_PROVIDER=custom
OLMOCR_CUSTOM_API_URL=http://你的服务器IP:8000/v1
OLMOCR_CUSTOM_MODEL=olmocr
OLMOCR_API_KEY=可选的API密钥
```

### 2. 使用其他兼容 OpenAI API 的服务

任何实现 OpenAI API 格式的推理服务都可以使用：

- **Ollama** - 本地运行大模型
- **LM Studio** - 桌面 LLM 应用
- **LocalAI** - 开源 OpenAI 替代品
- **其他云服务商**

### 3. 使用不同的模型版本

如果提供商有多个模型版本：

```bash
OLMOCR_PROVIDER=custom
OLMOCR_CUSTOM_API_URL=https://api.某服务商.com/v1
OLMOCR_CUSTOM_MODEL=allenai/olmOCR-7B-0825-FP8
OLMOCR_API_KEY=你的密钥
```

## 📝 配置示例

### 示例 1: 本地 vLLM 服务器

```env
OLMOCR_PROVIDER=custom
OLMOCR_CUSTOM_API_URL=http://192.168.1.100:8000/v1
OLMOCR_CUSTOM_MODEL=olmocr
OLMOCR_API_KEY=
```

### 示例 2: 云服务器

```env
OLMOCR_PROVIDER=custom
OLMOCR_CUSTOM_API_URL=https://my-vllm-server.example.com/v1
OLMOCR_CUSTOM_MODEL=allenai/olmOCR-2-7B-1025
OLMOCR_API_KEY=sk-xxxxxxxxxxxxx
```

### 示例 3: 内网穿透

如果你在家里的电脑上运行 vLLM，使用 ngrok 或 cloudflare tunnel：

```bash
# 启动 ngrok
ngrok http 8000

# 使用 ngrok 提供的 URL
```

```env
OLMOCR_PROVIDER=custom
OLMOCR_CUSTOM_API_URL=https://xxxx-xx-xx-xxx-xxx.ngrok-free.app/v1
OLMOCR_CUSTOM_MODEL=olmocr
OLMOCR_API_KEY=
```

## 🔑 API Key 说明

- 如果你的自定义 API 不需要认证，可以留空 `OLMOCR_API_KEY`
- 如果需要认证，填入对应的 API Key
- API Key 通过 HTTP Authorization Bearer header 传递

## ✅ 验证配置

部署后访问 `/health` 端点检查配置：

```bash
curl https://your-app.onrender.com/health
```

返回示例：
```json
{
  "status": "ok",
  "provider": "custom",
  "api_url": "http://192.168.1.100:8000/v1",
  "model": "olmocr",
  "api_key_configured": false
}
```

## 🚨 注意事项

1. **网络访问** - 确保 Render 服务器可以访问你的自定义 API URL
2. **安全性** - 不要在公网暴露没有认证的 API
3. **超时设置** - 如果模型推理慢，可能需要调整超时时间
4. **兼容性** - API 必须兼容 OpenAI 的接口格式

## 💡 推荐配置

### 成本优化方案
使用 **RunPod** 或 **Vast.ai** 部署自己的 vLLM 实例：
- 按小时计费，用时启动
- A100 40GB: ~$1-2/小时
- 处理完关闭，非常经济

### 最佳性能方案
使用内置提供商：
- **Cirrascale** - 最便宜 ($0.07/$0.15)
- **DeepInfra** - 性价比高 ($0.09/$0.19)

### 完全控制方案
自己部署 vLLM + 使用 custom 配置
- 完全掌控
- 无限制调用
- 适合大批量处理

## 🔗 相关资源

- vLLM 文档: https://docs.vllm.ai/
- olmOCR GitHub: https://github.com/allenai/olmocr
- ngrok: https://ngrok.com/
- cloudflare tunnel: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/
