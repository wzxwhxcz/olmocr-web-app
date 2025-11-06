# olmOCR Web 服务日志说明

## 日志功能

已为 olmocr-render-app 添加了完整的日志记录功能,可以帮助追踪和调试应用的运行状态。

## 日志级别

应用使用以下日志级别:

- **INFO**: 记录正常的操作流程和关键信息
- **WARNING**: 记录警告信息(如文件格式不支持、缺少参数等)
- **ERROR**: 记录错误信息(如处理失败、超时等)
- **DEBUG**: 记录详细的调试信息(如健康检查详情)

## 日志输出位置

日志会输出到两个位置:

1. **标准输出(控制台)**: 实时显示在终端
2. **日志文件**: 保存在 `olmocr_app.log` 文件中

## 日志内容

### 1. 应用启动日志

```
2025-11-06 14:00:00 - __main__ - INFO - ============================================================
2025-11-06 14:00:00 - __main__ - INFO - 启动 olmOCR Web 服务
2025-11-06 14:00:00 - __main__ - INFO - ============================================================
2025-11-06 14:00:00 - __main__ - INFO - 当前提供商: deepinfra
2025-11-06 14:00:00 - __main__ - INFO - API 密钥已配置: True
2025-11-06 14:00:00 - __main__ - INFO - 上传文件夹: /tmp
2025-11-06 14:00:00 - __main__ - INFO - 最大文件大小: 50MB
2025-11-06 14:00:00 - __main__ - INFO - 服务器端口: 5000
2025-11-06 14:00:00 - __main__ - INFO - 调试模式: False
2025-11-06 14:00:00 - __main__ - INFO - ============================================================
```

### 2. API 请求日志

#### 主页访问
```
INFO - 访问主页,来自 IP: 127.0.0.1
```

#### 健康检查
```
DEBUG - 健康检查请求,来自 IP: 127.0.0.1
DEBUG - 健康检查结果: {'status': 'ok', 'provider': 'deepinfra', ...}
```

#### 文件转换请求
```
INFO - 收到转换请求,来自 IP: 127.0.0.1
INFO - 上传文件: document.pdf
INFO - 创建任务 abc-123-def,工作目录: /tmp/olmocr_abc-123-def
INFO - 文件保存成功: /tmp/olmocr_abc-123-def/document.pdf (大小: 1048576 字节)
INFO - 创建输出目录: /tmp/olmocr_abc-123-def/output
INFO - 开始处理任务 abc-123-def
```

### 3. olmOCR 处理日志

```
INFO - 开始处理 PDF: /tmp/olmocr_abc-123-def/document.pdf
INFO - 输出目录: /tmp/olmocr_abc-123-def/output
INFO - 使用提供商: deepinfra
INFO - API 服务器: https://api.deepinfra.com/v1/openai
INFO - 模型: allenai/olmOCR-2-7B-1025
INFO - 执行命令: python -m olmocr.pipeline /tmp/olmocr_abc-123-def/output --server https://api.deepinfra.com/v1/openai --api_key *** --model allenai/olmOCR-2-7B-1025 --markdown --pdfs /tmp/olmocr_abc-123-def/document.pdf
INFO - 开始执行 olmOCR 处理...
INFO - olmOCR 处理完成,耗时: 45.32秒
INFO - olmOCR 处理成功
```

### 4. 结果处理日志

```
INFO - 查找 Markdown 文件: /tmp/olmocr_abc-123-def/output/markdown
INFO - 找到 1 个 Markdown 文件
INFO - 读取 Markdown 文件: /tmp/olmocr_abc-123-def/output/markdown/document.md
INFO - Markdown 内容大小: 5432 字符
INFO - 清理工作目录: /tmp/olmocr_abc-123-def
INFO - 任务 abc-123-def 处理成功
```

### 5. 错误日志

```
WARNING - 请求中未包含文件
WARNING - 文件名为空
WARNING - 不支持的文件格式: document.txt
ERROR - 未设置 OLMOCR_API_KEY 环境变量
ERROR - 未知的提供商: unknown_provider
ERROR - olmOCR 处理失败,返回码: 1
ERROR - 未生成 Markdown 文件
ERROR - 任务 abc-123-def 处理超时
ERROR - 任务 abc-123-def 处理错误: Connection timeout
```

## 查看日志

### 实时查看日志文件

```bash
tail -f olmocr_app.log
```

### 查看最近的日志

```bash
tail -n 100 olmocr_app.log
```

### 搜索特定内容

```bash
# 搜索错误
grep "ERROR" olmocr_app.log

# 搜索特定任务
grep "abc-123-def" olmocr_app.log

# 搜索处理时间
grep "耗时" olmocr_app.log
```

## 日志格式

日志格式为:
```
时间戳 - 日志记录器名称 - 日志级别 - 日志消息
```

示例:
```
2025-11-06 14:30:45 - __main__ - INFO - 收到转换请求,来自 IP: 127.0.0.1
```

## 安全性

- API 密钥在日志中会被替换为 `***`,不会泄露敏感信息
- 记录客户端 IP 地址,便于追踪和调试

## 性能监控

日志中包含以下性能指标:

1. **文件大小**: 上传文件的字节数
2. **处理时间**: olmOCR 处理耗时(秒)
3. **输出大小**: 生成的 Markdown 内容字符数

这些指标可以帮助分析和优化应用性能。

## 生产环境建议

在生产环境中,建议:

1. 使用日志轮转工具(如 logrotate)管理日志文件大小
2. 将日志级别设置为 INFO 或 WARNING,减少 DEBUG 日志
3. 考虑使用集中式日志管理系统(如 ELK Stack、Splunk 等)
4. 定期分析日志,监控错误率和性能指标

## 修改日志级别

在代码中修改日志级别:

```python
# 修改为 DEBUG 级别(显示更多详细信息)
logging.basicConfig(level=logging.DEBUG, ...)

# 修改为 WARNING 级别(只显示警告和错误)
logging.basicConfig(level=logging.WARNING, ...)
```

或通过环境变量设置:

```bash
export LOG_LEVEL=DEBUG
```
