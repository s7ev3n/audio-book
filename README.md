# 📚 Audio Book Translator

将英文 EPUB 电子书翻译成中文有声书的完整解决方案。

## 功能特性

- 🔄 EPUB 文件解析和章节提取
- 🌐 AI 大语言模型翻译（支持 OpenAI、Claude 等）
- 🔊 TTS 语音合成（多种语音服务支持）
- 🎵 音频文件管理和拼接
- 💻 双栏界面显示（原文 | 译文）
- 🎯 音频播放时文字高亮同步

## 技术架构

- **后端**: Python + FastAPI
- **前端**: React + TypeScript
- **数据库**: SQLite
- **音频处理**: FFmpeg + PyDub

## 项目结构

```
audio-book/
├── backend/          # Python FastAPI 后端
├── frontend/         # React 前端应用
├── storage/          # 文件存储目录
└── docker-compose.yml
```

## 快速开始

1. 克隆项目并安装依赖
2. 配置 API 密钥（翻译和 TTS 服务）
3. 启动后端服务
4. 启动前端应用
5. 上传 EPUB 文件开始转换

## 配置要求

- Python 3.9+
- Node.js 16+
- FFmpeg