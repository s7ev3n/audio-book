#!/bin/bash

# Audio Book Translator 启动脚本

echo "🚀 启动 Audio Book Translator..."

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 检查配置文件
if [ ! -f "backend/.env" ]; then
    echo "📝 复制环境配置文件..."
    cp backend/.env.example backend/.env
    echo "⚠️  请编辑 backend/.env 文件，填入你的 API 密钥"
    echo "📖 编辑完成后，再次运行此脚本启动服务"
    exit 0
fi

# 启动服务
echo "🐳 启动 Docker 服务..."
docker-compose up -d --build

echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

echo ""
echo "✅ 服务启动完成！"
echo ""
echo "🌐 前端界面: http://localhost:3000"
echo "🔧 后端 API: http://localhost:8000"
echo "📚 API 文档: http://localhost:8000/docs"
echo ""
echo "💡 使用以下命令管理服务:"
echo "  停止服务: docker-compose down"
echo "  查看日志: docker-compose logs -f"
echo "  重启服务: docker-compose restart"
echo ""
