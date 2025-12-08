#!/bin/bash

GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}[1/4] 正在检查环境...${NC}"
# 获取当前脚本所在的绝对路径
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 检查是否安装了 python3
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3，请先安装 Python。"
    exit 1
fi

echo -e "${GREEN}[2/4] 正在安装 Python 依赖...${NC}"
# 创建一个虚拟环境，防止污染对方的全局环境
if [ ! -d "$PROJECT_DIR/venv" ]; then
    python3 -m venv "$PROJECT_DIR/venv"
fi

# 激活虚拟环境并安装依赖
source "$PROJECT_DIR/venv/bin/activate"
pip install -r "$PROJECT_DIR/requirements.txt"

echo -e "${GREEN}[3/4] 正在配置 'tips' 命令...${NC}"

# 创建启动脚本的内容
LAUNCHER_PATH="/usr/local/bin/tips"

# 这里我们需要使用 sudo 来写入 /usr/local/bin
# 我们生成一个临时的启动脚本，然后移动它
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

echo -e "${GREEN}[4/4] 安装完成！${NC}"
echo "----------------------------------------"
echo "现在你可以在任意地方输入 'tips' 来使用了！"
echo "试一试: tips --help (如果你的程序支持)"