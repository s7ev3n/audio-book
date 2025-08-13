# F5-TTS 微服务使用指南

## 概述

F5-TTS已经被封装为一个独立的微服务，与主后端服务分离运行。这种架构设计带来以下优势：

1. **性能隔离**: TTS处理不会影响主服务的响应
2. **资源优化**: F5-TTS可以独占GPU资源
3. **可扩展性**: 可以根据需要独立扩缩容TTS服务
4. **长文本处理**: 特别适合处理书籍级别的长文本

## 架构组件

### 1. F5-TTS 微服务 (`f5tts-service`)
- **端口**: 8001
- **功能**: 专门处理文本转语音任务
- **API风格**: RESTful异步API
- **支持功能**: 
  - 自动语言检测（中英文）
  - 可配置语音速度
  - 静音移除
  - 任务状态跟踪

### 2. 主后端服务 (`backend`)
- **端口**: 8000  
- **功能**: 调用F5-TTS微服务进行TTS处理
- **长文本策略**: 自动分段处理，避免内存溢出

## API接口设计

### F5-TTS 微服务 API

#### 1. 创建TTS任务
```http
POST /tts
Content-Type: application/json

{
  "text": "要转换的文本",
  "language": "auto",  // "zh", "en", "auto"
  "speed": 1.0,        // 语音速度倍率
  "remove_silence": true
}
```

响应:
```json
{
  "task_id": "uuid-string",
  "status": "pending",
  "message": "Task created successfully"
}
```

#### 2. 查询任务状态
```http
GET /task/{task_id}
```

响应:
```json
{
  "task_id": "uuid-string",
  "status": "completed",  // pending, processing, completed, failed
  "progress": 1.0,
  "audio_url": "/audio/uuid-string.wav",
  "error_message": null
}
```

#### 3. 下载音频文件
```http
GET /audio/{filename}
```

返回音频文件（WAV格式）

#### 4. 健康检查
```http
GET /health
```

## 长文本处理策略

针对书籍级别的长文本，系统采用以下策略：

### 1. 智能分段
- 按句号分割文本（中文）
- 每段限制在1000字符以内
- 保持语义完整性

### 2. 并发处理
- 使用异步任务处理
- 支持进度跟踪
- 自动错误重试

### 3. 音频合并
- 自动在音频段落间添加0.5秒静音
- 最终输出MP3格式（压缩存储）
- 保持音质的同时减小文件大小

## 部署配置

### Docker Compose 配置

```yaml
f5tts-service:
  build:
    context: ./f5tts-service
  ports:
    - "8001:8001"
  volumes:
    - huggingface-cache:/root/.cache/huggingface/hub/
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

### 环境变量
```bash
TTS_PROVIDER=f5tts
F5TTS_SERVICE_URL=http://f5tts-service:8001
```

## 使用方法

### 启动服务
```bash
# 构建并启动所有服务
docker-compose up --build

# 仅启动F5-TTS服务
docker-compose up f5tts-service
```

### 测试F5-TTS服务
```bash
# 健康检查
curl http://localhost:8001/health

# 创建TTS任务
curl -X POST http://localhost:8001/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "你好，这是一个测试。", "language": "auto", "speed": 1.0}'

# 查询任务状态（替换task_id）
curl http://localhost:8001/task/{task_id}
```

## 性能优化建议

1. **GPU资源**: 确保为F5-TTS服务分配足够的GPU内存
2. **缓存管理**: HuggingFace模型会缓存在Docker volume中
3. **并发控制**: 可根据GPU性能调整后台任务数量
4. **监控**: 监控F5-TTS服务的内存和GPU使用情况

## 故障排除

### 常见问题

1. **GPU不可用**: 检查nvidia-docker和GPU驱动
2. **模型下载慢**: 配置国内镜像或预下载模型
3. **内存不足**: 调整Docker内存限制或减少并发任务数
4. **网络连接**: 确保服务间网络连通性

### 日志查看
```bash
# 查看F5-TTS服务日志
docker-compose logs f5tts-service

# 查看后端服务日志
docker-compose logs backend
```

这个微服务架构特别适合处理长文本（如整本书）的TTS任务，通过异步处理和智能分段，可以高效地处理大量文本而不会导致系统卡顿或内存溢出。