import os
import sys
from datetime import datetime

# 引入 rich 库的核心组件
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich import box
from rich.text import Text
from rich.align import Align

# 初始化控制台
console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# --- 模拟数据 ---
private_tips = [
    {"id": 1, "ddl": "25-12-08 23:59", "done": False, "content": "aid"},
    {"id": 2, "ddl": "25-12-21 23:59", "done": False, "content": "概统大作业"},
    {"id": 3, "ddl": "None", "done": True,  "content": "买牛奶"},
]

group_tips = [
    {"id": 4, "ddl": "25-12-06 23:59", "done": False, "content": "fill fwc table"},
    {"id": 5, "ddl": "25-12-10 10:00", "done": False, "content": "组会PPT准备"},
]

current_user = "quam1123"
current_group_name = "考研小队"
focus_mode = "GROUP" # 假设当前选中了 Group

def generate_table(tips_list, is_focused):
    """
    生成一个 Rich 表格对象
    """
    # 如果没选中，颜色变暗
    border_style = "blue" if is_focused else "dim white"
    header_style = "bold white" if is_focused else "dim white"
    
    # 创建表格，去掉默认边框，因为外层会有 Panel 包裹
    table = Table(box=None, expand=True, padding=(0, 1), show_header=True, header_style=header_style)
    
    # 定义列
    table.add_column("ID", style="cyan", width=4)
    table.add_column("DDL", style="yellow", width=16)
    table.add_column("Done", justify="center", width=6)
    table.add_column("Content", style="white")

    if not tips_list:
        table.add_row("-", "-", "-", "[dim]No tips available[/dim]")
        return table

    for t in tips_list:
        # 处理完成状态图标
        icon = "✅" if t['done'] else "❌"
        # DDL 颜色逻辑
        ddl_str = t['ddl']
        
        # 添加行
        table.add_row(
            str(t['id']), 
            ddl_str, 
            icon, 
            t['content']
        )
    
    return table

def draw_ui():
    clear_screen()
    
    # 1. 顶部标题栏 (模拟 LAZY CLI 的第一行)
    # 使用 Text 对象来拼接颜色
    header_text = Text()
    header_text.append(" TIPS CLIENT ", style="bold white on blue")
    header_text.append(f" - User: {current_user} ", style="bold blue")
    header_text.append(f"| {datetime.now().strftime('%H:%M')} ", style="dim")
    console.print(header_text)
    console.print("") # 空一行

    # 2. 私人 Tips 面板 (模拟 'Options' 那个框)
    # 这里的 title_align="left" 让标题靠左，和截图一样
    private_table = generate_table(private_tips, is_focused=(focus_mode=="PRIVATE"))
    
    # 边框样式：如果是焦点，蓝色；否则灰色
    p_border = "blue" if focus_mode=="PRIVATE" else "dim white"
    p_title = "[bold blue]🏠 Private Tips[/]" if focus_mode=="PRIVATE" else "[dim]🏠 Private Tips[/]"
    
    # Panel 就是那个圆角框框
    console.print(Panel(
        private_table, 
        title=p_title, 
        title_align="left",
        border_style=p_border,
        box=box.ROUNDED, # 使用圆角边框 ╭─╮
        expand=False,    # 不撑满全屏，也可以设为 True
        width=80         # 固定宽度，看起来更像 CLI 工具
    ))

    # 3. 群组 Tips 面板 (模拟 'Commands' 那个框)
    group_table = generate_table(group_tips, is_focused=(focus_mode=="GROUP"))
    
    g_border = "yellow" if focus_mode=="GROUP" else "dim white"
    g_title = f"[bold yellow]👥 Group: {current_group_name}[/]" if focus_mode=="GROUP" else f"[dim]👥 Group: {current_group_name}[/]"

    console.print(Panel(
        group_table, 
        title=g_title, 
        title_align="left",
        border_style=g_border,
        box=box.ROUNDED,
        expand=False,
        width=80
    ))

    # 4. 底部状态栏
    console.print("")
    status_text = Text(" 🔔 Status: Data refreshed successfully.", style="yellow italic")
    console.print(status_text)
    
    # 5. 命令提示
    console.print("[dim]─" * 80)
    console.print("[bold cyan]Command > [/bold cyan]", end="")

if __name__ == "__main__":
    draw_ui()
    # 模拟输入挂起，方便看效果
    input()