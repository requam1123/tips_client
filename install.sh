#!/bin/bash

# 定义颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# ================= 配置区 =================
# 最低支持的 Python 版本
MIN_VERSION_MAJOR=3
MIN_VERSION_MINOR=10
# ========================================

echo -e "${GREEN}[1/5] 正在检查环境...${NC}"
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 前置检查：确保核心文件存在
if [ ! -f "$PROJECT_DIR/main.py" ]; then
    echo -e "${RED}错误: 找不到 main.py！请确保你在正确的目录下运行此脚本。${NC}"
    exit 1
fi

# 1. 检查是否存在 python3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 Python3，请先安装 Python。${NC}"
    exit 1
fi

# 2. 检查 Python 版本是否 >= 3.10
PY_VER_STR=$(python3 --version 2>&1)
if [[ $PY_VER_STR =~ Python\ ([0-9]+)\.([0-9]+) ]]; then
    VER_MAJOR=${BASH_REMATCH[1]}
    VER_MINOR=${BASH_REMATCH[2]}

    if [ "$VER_MAJOR" -lt "$MIN_VERSION_MAJOR" ] || ([ "$VER_MAJOR" -eq "$MIN_VERSION_MAJOR" ] && [ "$VER_MINOR" -lt "$MIN_VERSION_MINOR" ]); then
        echo -e "${RED}错误: Python 版本过低！${NC}"
        echo "当前版本: $PY_VER_STR"
        echo "最低要求: Python $MIN_VERSION_MAJOR.$MIN_VERSION_MINOR"
        exit 1
    fi
    echo "Python 版本检查通过: $PY_VER_STR"
else
    # 给变量赋默认值，防止最后打印为空
    VER_MAJOR="未知"
    VER_MINOR="版本"
    echo -e "${YELLOW}警告: 无法识别 Python 版本，跳过版本检查。${NC}"
fi

# 3. 检查是否安装了 python3-venv 模块
if ! python3 -m venv --help > /dev/null 2>&1; then
    echo -e "${RED}错误: 您的 Python 缺少 'venv' 模块。${NC}"
    echo "请运行以下命令修复: sudo apt update && sudo apt install -y python3-venv"
    exit 1
fi

echo -e "${GREEN}[2/5] 正在准备虚拟环境...${NC}"
if [ -d "$PROJECT_DIR/venv" ]; then
    if [ ! -f "$PROJECT_DIR/venv/bin/activate" ]; then
        echo "发现损坏的虚拟环境，正在重建..."
        rm -rf "$PROJECT_DIR/venv"
        python3 -m venv "$PROJECT_DIR/venv" || { echo -e "${RED}创建虚拟环境失败${NC}"; exit 1; }
    else
        echo "虚拟环境已存在，跳过创建。"
    fi
else
    echo "创建新的虚拟环境..."
    python3 -m venv "$PROJECT_DIR/venv" || { echo -e "${RED}创建虚拟环境失败${NC}"; exit 1; }
fi

echo -e "${GREEN}[3/5] 正在安装 Python 依赖...${NC}"
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    # 添加了 || exit 1，一旦安装失败立即停止，不误导用户
    "$PROJECT_DIR/venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt" || {
        echo -e "${RED}错误: 依赖安装失败，请检查网络或 requirements.txt 内容。${NC}"
        exit 1
    }
else
    echo -e "${YELLOW}未发现 requirements.txt，跳过依赖安装。${NC}"
fi

echo -e "${GREEN}[4/5] 正在配置 'tips' 命令...${NC}"
LAUNCHER_PATH="/usr/local/bin/tips"

echo "需要管理员权限来创建全局命令..."
# 优化点：使用 sudo tee 直接写入目标文件，避免产生临时文件
sudo tee "$LAUNCHER_PATH" > /dev/null << EOF
#!/bin/bash
# 进入项目目录
cd "$PROJECT_DIR"
# 使用虚拟环境中的 Python 运行 main.py
"$PROJECT_DIR/venv/bin/python" main.py "\$@"
EOF

# 检查全局命令是否创建成功
if [ $? -eq 0 ]; then
    sudo chmod +x "$LAUNCHER_PATH"
else
    echo -e "${RED}错误: 无法写入 $LAUNCHER_PATH，权限获取失败。${NC}"
    exit 1
fi

echo -e "${GREEN}[5/5] 安装完成！${NC}"
echo "----------------------------------------"
echo "环境检查: Python ${VER_MAJOR}.${VER_MINOR} (OK)"
echo "现在你可以在任意地方输入 'tips' 来使用了！"
echo "试一试: tips --help"