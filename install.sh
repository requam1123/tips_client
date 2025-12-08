#!/bin/bash

# 定义颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ================= 配置区 =================
# 最低支持的 Python 版本
MIN_VERSION_MAJOR=3
MIN_VERSION_MINOR=10
# ========================================

echo -e "${GREEN}[1/5] 正在检查环境...${NC}"
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 1. 检查是否存在 python3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 Python3，请先安装 Python。${NC}"
    exit 1
fi

# 2. 检查 Python 版本是否 >= 3.10
# 获取版本号字符串 (例如 "Python 3.10.12")
PY_VER_STR=$(python3 --version 2>&1)
# 提取版本号，利用 bash 正则提取 Major 和 Minor
if [[ $PY_VER_STR =~ Python\ ([0-9]+)\.([0-9]+) ]]; then
    VER_MAJOR=${BASH_REMATCH[1]}
    VER_MINOR=${BASH_REMATCH[2]}

    # 逻辑：主版本<3 或者 (主版本=3 且 次版本<10) 则报错
    if [ "$VER_MAJOR" -lt "$MIN_VERSION_MAJOR" ] || ([ "$VER_MAJOR" -eq "$MIN_VERSION_MAJOR" ] && [ "$VER_MINOR" -lt "$MIN_VERSION_MINOR" ]); then
        echo -e "${RED}错误: Python 版本过低！${NC}"
        echo "当前版本: $PY_VER_STR"
        echo "最低要求: Python $MIN_VERSION_MAJOR.$MIN_VERSION_MINOR"
        exit 1
    fi
    echo "Python 版本检查通过: $PY_VER_STR"
else
    echo -e "${RED}警告: 无法识别 Python 版本，跳过版本检查。${NC}"
fi

# 3. 检查是否安装了 python3-venv 模块 (解决你之前遇到的空壳环境问题)
# 尝试运行 venv 的帮助命令，如果失败说明模块缺失
if ! python3 -m venv --help > /dev/null 2>&1; then
    echo -e "${RED}错误: 您的 Python 缺少 'venv' 模块。${NC}"
    echo "这在 Ubuntu/Debian/WSL 上很常见。请运行以下命令修复："
    echo ""
    echo "    sudo apt update && sudo apt install -y python3-venv"
    echo ""
    exit 1
fi

echo -e "${GREEN}[2/5] 正在准备虚拟环境...${NC}"
# 创建一个虚拟环境，防止污染对方的全局环境
# 如果已经存在，不仅判断文件夹，还要看里面是不是坏的
if [ -d "$PROJECT_DIR/venv" ]; then
    # 简单检查 activate 是否存在，不存在说明是坏的，删掉重建
    if [ ! -f "$PROJECT_DIR/venv/bin/activate" ]; then
        echo "发现损坏的虚拟环境，正在重建..."
        rm -rf "$PROJECT_DIR/venv"
        python3 -m venv "$PROJECT_DIR/venv"
    else
        echo "虚拟环境已存在，跳过创建。"
    fi
else
    echo "创建新的虚拟环境..."
    python3 -m venv "$PROJECT_DIR/venv"
fi

echo -e "${GREEN}[3/5] 正在安装 Python 依赖...${NC}"
# 激活虚拟环境并安装依赖
# 注意：在脚本中 source 只对当前 shell 有效，所以后面用完整路径调用 pip 更稳妥
"$PROJECT_DIR/venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt"

echo -e "${GREEN}[4/5] 正在配置 'tips' 命令...${NC}"

# 创建启动脚本的内容
LAUNCHER_PATH="/usr/local/bin/tips"

cat << EOF > tips_launcher.temp
#!/bin/bash
# 进入项目目录
cd "$PROJECT_DIR"
# 使用虚拟环境中的 Python 运行 main.py
"$PROJECT_DIR/venv/bin/python" main.py "\$@"
EOF

# 移动并赋予权限
echo "需要管理员权限来创建全局命令..."
sudo mv tips_launcher.temp $LAUNCHER_PATH
sudo chmod +x $LAUNCHER_PATH

echo -e "${GREEN}[5/5] 安装完成！${NC}"
echo "----------------------------------------"
echo "环境检查: Python $VER_MAJOR.$VER_MINOR (OK)"
echo "现在你可以在任意地方输入 'tips' 来使用了！"
echo "试一试: tips --help"