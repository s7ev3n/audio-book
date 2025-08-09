# 📚 Audio Book Translator

将英文 EPUB 电子书翻译成中文有声书的完整解决方案。支持自动章节提取、AI 翻译、TTS 语音合成，提供美观的双栏阅读界面和音频播放功能。

## ✨ 功能特性

- � **EPUB 解析**: 自动提取 EPUB 文件章节和内容
- 🌐 **智能翻译**: 支持多种 AI 翻译服务（硅基流动、OpenAI、Claude 等）
- 🔊 **语音合成**: 集成多种 TTS 服务，生成高质量中文语音
- 🎵 **音频管理**: 自动拼接章节音频，支持播放控制
- 💻 **双栏界面**: 原文译文对照显示，阅读体验优秀
- 🎯 **同步高亮**: 音频播放时文字内容同步高亮
- 📚 **书库管理**: 本地书库管理，支持书籍删除和重新处理

## 🏗️ 技术架构

- **后端**: Python 3.11 + FastAPI + Uvicorn
- **前端**: React 18 + TypeScript + Material-UI
- **状态管理**: Zustand + React Query
- **音频处理**: FFmpeg + PyDub
- **文件处理**: EbookLib + BeautifulSoup4

## 📁 项目结构

```
audio-book/
├── backend/                    # Python FastAPI 后端
│   ├── app/                   # 应用核心代码
│   │   ├── api/              # API 路由
│   │   ├── core/             # 核心配置
│   │   ├── models/           # 数据模型
│   │   ├── services/         # 业务逻辑服务
│   │   └── utils/            # 工具函数
│   ├── storage/              # 文件存储目录
│   │   ├── uploads/          # 上传的 EPUB 文件
│   │   ├── translations/     # 翻译结果
│   │   └── audio/            # 生成的音频文件
│   ├── main.py               # 应用入口
│   ├── requirements.txt      # Python 依赖
│   ├── .env.example         # 环境变量示例
│   └── Dockerfile           # Docker 配置
├── frontend/                  # React 前端应用
│   ├── src/
│   │   ├── components/       # React 组件
│   │   ├── services/         # API 服务
│   │   ├── store/           # 状态管理
│   │   ├── types/           # TypeScript 类型定义
│   │   └── utils/           # 工具函数
│   ├── package.json         # Node.js 依赖
│   └── Dockerfile          # Docker 配置
├── docker-compose.yml       # Docker Compose 配置
└── README.md               # 项目说明
```

## 🚀 快速开始

### 方式一：Docker Compose（推荐）

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd audio-book
   ```

2. **配置环境变量**
   ```bash
   cp backend/.env.example backend/.env
   # 编辑 backend/.env 文件，填入你的 API 密钥
   ```

3. **启动服务**
   ```bash
   docker-compose up -d
   ```

4. **访问应用**
   - 前端界面: http://localhost:3000
   - 后端 API: http://localhost:8000
   - API 文档: http://localhost:8000/docs

### 方式二：本地开发

#### 前置要求

- Python 3.11+
- Node.js 18+
- FFmpeg

#### 后端启动

1. **进入后端目录**
   ```bash
   cd backend
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # 或
   .venv\Scripts\activate     # Windows
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入你的 API 密钥
   ```

5. **启动后端服务**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

#### 前端启动

1. **进入前端目录**
   ```bash
   cd frontend
   ```

2. **安装依赖**
   ```bash
   npm install
   ```

3. **启动前端服务**
   ```bash
   npm start
   ```

## ⚙️ 配置说明

### 环境变量配置

在 `backend/.env` 文件中配置以下变量：

```bash
# 硅基流动 API 配置（推荐）
SILICONFLOW_API_KEY=your_siliconflow_api_key_here
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1

# 翻译配置
TRANSLATION_MODEL=deepseek-ai/DeepSeek-V3
TRANSLATION_PROVIDER=siliconflow
CHUNK_SIZE=2000

# Azure TTS 配置（可选）
AZURE_TTS_KEY=your_azure_tts_key
AZURE_TTS_REGION=eastus
TTS_VOICE=zh-CN-XiaoxiaoNeural

# 其他配置
DATABASE_URL=sqlite:///./audiobook.db
MAX_FILE_SIZE=52428800
DEBUG=false
MAX_WORKERS=4
```

### 支持的翻译服务

- 🔥 **硅基流动**（推荐）: 性价比高，支持多种模型
- 🤖 **OpenAI**: GPT-3.5/4 系列模型
- 🧠 **Claude**: Anthropic 的 Claude 系列模型

### 支持的 TTS 服务

- 🎙️ **Azure Cognitive Services**: 高质量中文语音合成
- 🔊 **其他服务**: 支持扩展其他 TTS 提供商

## 📝 使用指南

1. **上传 EPUB 文件**: 在首页点击"上传书籍"，选择 EPUB 文件
2. **查看书库**: 上传后自动跳转到"我的书库"，查看已上传的书籍
3. **开始翻译**: 点击书籍封面进入阅读界面，开始翻译和音频生成
4. **阅读体验**: 享受双栏对照阅读和音频播放功能
5. **管理书籍**: 可以删除不需要的书籍，释放存储空间

## 🛠️ 开发说明

### API 接口

- `GET /books/` - 获取书籍列表
- `POST /books/upload` - 上传 EPUB 文件
- `DELETE /books/{book_id}` - 删除书籍
- `GET /books/{book_id}/chapters` - 获取章节列表
- `POST /translation/translate` - 翻译文本
- `POST /tts/synthesize` - 语音合成

### 目录结构说明

- `backend/storage/` - 用户数据存储目录，已配置 git 忽略
- `frontend/src/components/` - 可复用的 React 组件
- `frontend/src/store/` - Zustand 状态管理
- `frontend/src/services/` - API 调用服务

## 🐳 Docker 部署

### 生产环境部署

1. **修改环境变量**
   ```bash
   # 设置生产环境配置
   DEBUG=false
   ```

2. **构建并启动**
   ```bash
   docker-compose up -d --build
   ```

3. **查看日志**
   ```bash
   docker-compose logs -f
   ```

### 服务管理

```bash
# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看服务状态
docker-compose ps

# 进入容器
docker-compose exec backend bash
docker-compose exec frontend sh
```

## 📋 故障排除

### 常见问题

1. **FFmpeg 未安装**
   - Ubuntu/Debian: `sudo apt install ffmpeg`
   - macOS: `brew install ffmpeg`
   - Windows: 下载 FFmpeg 官方二进制文件

2. **API 密钥错误**
   - 检查 `.env` 文件中的 API 密钥是否正确
   - 确认 API 服务商账户余额充足

3. **端口冲突**
   - 修改 `docker-compose.yml` 中的端口映射
   - 或停止占用端口的其他服务

4. **存储空间不足**
   - 清理 `backend/storage/` 目录下的文件
   - 或通过界面删除不需要的书籍

### 日志查看

```bash
# Docker 环境
docker-compose logs backend
docker-compose logs frontend

# 本地开发
# 后端日志在终端输出
# 前端日志在浏览器控制台
```

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

此项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Python Web 框架
- [React](https://reactjs.org/) - 用于构建用户界面的 JavaScript 库
- [Material-UI](https://mui.com/) - React UI 组件库
- [EbookLib](https://github.com/aerkalov/ebooklib) - Python EPUB 处理库