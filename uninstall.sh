#!/bin/bash

# 定义颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# 获取当前脚本所在目录
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LAUNCHER_PATH="/usr/local/bin/tips"

echo -e "${YELLOW}警告: 这将卸载全局命令 'tips' 并删除相关的虚拟环境。${NC}"
echo "您的源代码和数据文件将保留在: $PROJECT_DIR"
echo ""

# 二次确认防呆设计
read -p "确定要继续卸载吗？(y/N): " confirm

# 检查用户输入，只在输入 y 或 Y 时继续
if [[ "$confirm" != [yY] && "$confirm" != [yY][eE][sS] ]]; then
    echo "已取消卸载。"
    exit 0
fi

echo ""
echo -e "${GREEN}[1/2] 正在移除全局命令...${NC}"
if [ -f "$LAUNCHER_PATH" ]; then
    echo "需要管理员权限来删除 $LAUNCHER_PATH..."
    sudo rm -f "$LAUNCHER_PATH"
    
    # 检查是否删除成功
    if [ $? -eq 0 ]; then
        echo "✅ 全局命令移除成功。"
    else
        echo -e "${RED}❌ 错误: 无法删除全局命令，请检查权限。${NC}"
        exit 1
    fi
else
    echo "未发现全局命令，可能已被删除，跳过。"
fi

echo -e "${GREEN}[2/2] 正在清理虚拟环境...${NC}"
if [ -d "$PROJECT_DIR/venv" ]; then
    rm -rf "$PROJECT_DIR/venv"
    echo "✅ 虚拟环境 (venv) 清理完毕。"
else
    echo "未发现虚拟环境，跳过。"
fi

echo "----------------------------------------"
echo -e "${GREEN}卸载完成！山高水长，后会有期。${NC}"