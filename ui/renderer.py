import sys
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.text import Text

# 初始化 Rich
console = Console()
UI_WIDTH = 80 

def clear_screen():
    console.clear()

def get_ddl_style(raw_ddl, is_done):
    """辅助函数：计算 DDL 颜色"""
    if not raw_ddl:
        return "None", "dim white"
    
    ddl_dt = None
    try:
        # 尝试兼容多种格式
        if "T" in raw_ddl:
            ddl_dt = datetime.fromisoformat(raw_ddl)
        else:
            ddl_dt = datetime.strptime(raw_ddl, '%y-%m-%d %H:%M')
    except ValueError:
        return raw_ddl, "dim white"

    now = datetime.now()
    if is_done:
        return raw_ddl, "dim green"
    
    if ddl_dt < now:
        return raw_ddl, "bold red"
    elif ddl_dt < now + timedelta(days=1):
        return raw_ddl, "bold yellow"
    
    return raw_ddl, "green"

def create_list_panel(title, tips_list, is_focused, border_color):
    """绘制列表面板"""
    # 动态边框样式
    if is_focused:
        border_style = f"bold {border_color}"
        title_style = f"bold {border_color}"
    else:
        border_style = "dim white"
        title_style = "dim white"

    table = Table(box=None, expand=True, padding=(0, 1), show_header=True, header_style=title_style)
    
    table.add_column("ID", justify="left", width=4, style="cyan")
    table.add_column("DDL", justify="left", width=16)
    table.add_column("Done", justify="center", width=6)
    table.add_column("Content", justify="left", style="white")

    MAX_ROWS = 5
    
    if not tips_list:
        table.add_row("-", "-", "-", "[dim]No tips available[/dim]")
    else:
        for item in tips_list[:MAX_ROWS]:
            # 兼容处理：确保 item 是字典
            c = item.get('content', '')
            if len(c) > 35: c = c[:32] + "..."
            
            raw_ddl = item.get('ddl')
            is_done = item.get('is_done', False)
            idx = str(item.get('index', '?'))

            ddl_str, ddl_style = get_ddl_style(raw_ddl, is_done)
            icon = "✅" if is_done else "❌"
            
            table.add_row(idx, f"[{ddl_style}]{ddl_str}[/]", icon, c)
        
        if len(tips_list) > MAX_ROWS:
            rest = len(tips_list) - MAX_ROWS
            table.add_row("...", "...", "...", f"[dim]... and {rest} more ...[/]")

    return Panel(
        table,
        title=f"[{title_style}]{title}[/]",
        title_align="left",
        border_style=border_style,
        box=box.ROUNDED,
        width=UI_WIDTH,
        expand=False
    )

def draw_main_ui(client_obj, status_msg):
    clear_screen()
    
    # === 1. 兼容性数据获取 (关键修改) ===
    # 优先找 private_cache，找不到就找 local_cache (老版本数据)
    if hasattr(client_obj, 'private_cache'):
        data_private = client_obj.private_cache
        data_group = getattr(client_obj, 'group_cache', [])
        focus = getattr(client_obj, 'focus_mode', 0)
        g_name = getattr(client_obj, 'current_group_name', 'None')
    else:
        # Fallback: 使用老版本 local_cache
        data_private = getattr(client_obj, 'local_cache', [])
        data_group = [] # 老版本还没有群组数据，先置空
        focus = 0       # 强制聚焦在第一个框
        g_name = "None"

    # === 2. 绘制 Header ===
    now_str = datetime.now().strftime('%H:%M')
    focus_name = "PRIVATE" if focus == 0 else "GROUP"
    
    header = Text()
    header.append(" TIPS CLIENT ", style="bold white on blue")
    header.append(f" User: {client_obj.current_user} ", style="bold blue")
    header.append(f"| {now_str} | Focus: [{focus_name}]", style="dim")
    
    console.print(header)
    console.print("")

    # === 3. 绘制两个框 ===
    
    # 顶部框：显示 local_cache / private_cache
    panel_p = create_list_panel(
        "🏠 Tips List", 
        data_private, 
        is_focused=(focus == 0), 
        border_color="blue"
    )
    console.print(panel_p)

    # 底部框：暂时显示为空 (等待你以后更新Client)
    panel_g = create_list_panel(
        f"👥 Group: {g_name}", 
        data_group, 
        is_focused=(focus == 1), 
        border_color="yellow"
    )
    console.print(panel_g)

    # === 4. Footer ===
    console.print("")
    console.print(f"[dim]{'-' * UI_WIDTH}[/]")
    console.print(f"[bold yellow] 🔔 Status: {status_msg}[/]")
    console.print(f"[dim]{'-' * UI_WIDTH}[/]")
    
    # === 修复后的命令栏绘制 ===
    cmd_text = Text()
    cmd_text.append(" Command: ", style="dim")
    
    # 定义一个内部小函数来拼装命令，既整洁又不出错
    def add_cmd(key, desc, has_sep=True):
        cmd_text.append("[", style="bold white")
        cmd_text.append(key, style="bold white")
        cmd_text.append("]", style="bold white")
        cmd_text.append(desc, style="dim")
        if has_sep:
            cmd_text.append(" | ", style="dim")

    add_cmd("TAB", "Focus")
    add_cmd("a", "dd")
    add_cmd("d", "el")
    add_cmd("c", "hange")
    add_cmd("r", "efresh")
    add_cmd(":", "Cmd")
    add_cmd("q", "uit", has_sep=False) # 最后一个不加竖线
    
    console.print(cmd_text)