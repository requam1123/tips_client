import sys
import os
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.text import Text

# =============================================================================
# 1. 样式配置区 (UI_CONFIG) 
# =============================================================================
UI_CONFIG = {
    # --- 颜色主题 ---
    "theme": {
        "header_bg": "blue",          # 顶部标题背景
        "header_fg": "bold white",    # 顶部标题文字
        "user_highlight": "bold cyan",# 用户名高亮
        
        "border_private": "blue",     # 私人便签边框颜色
        "border_group": "magenta",    # 群组便签边框颜色

        "table_header": "bold yellow",   # 表头颜色

        
        # DDL 状态颜色
        "status_overdue": "bold red",    # 超时
        "status_urgent": "bold yellow",  # 24小时内
        "status_future": "green",        # 未来
        "status_done": "dim green",      # 已完成
        "status_none": "dim white",      # 无日期
        
        # 文字内容颜色
        "content_sender": "bold cyan",   # 群消息发送者名字
        "content_meta": "italic cyan",    # "Done: ..." 那行小字
        
    },

    # --- 图标 ---
    "icons": {
        "done": "[bold green]✔[/]",      # 已完成图标
        "todo": "[dim]◻[/]",        # 未完成图标
        "unknown": "-",
    },

    # --- 布局参数 ---
    "layout": {
        "width": 80,            # 整体宽度
        "max_rows": 8,          # 面板最大显示行数(暂时不用)
        "col_id_width": 4,      # ID列宽度
        "col_ddl_width": 16,    # 时间列宽度
        "col_done_width": 4,    # 状态列宽度
    }
}

# 初始化 Rich
console = Console()

# =============================================================================
# 2. 辅助逻辑函数
# =============================================================================

def clear_screen():
    # Windows 用 cls，macOS/Linux 用 clear
    command = 'cls' if os.name == 'nt' else 'clear'
    os.system(command)

def parse_ddl(raw_ddl):
    """尝试解析时间格式，返回 datetime 对象或 None"""
    if not raw_ddl:
        return None
    
    # 优先尝试 ISO 格式
    if "T" in raw_ddl:
        try:
            return datetime.fromisoformat(raw_ddl)
        except ValueError:
            pass

    formats = [
        '%y-%m-%d %H:%M', '%Y-%m-%d %H:%M', 
        '%Y-%m-%d %H:%M:%S', '%y-%m-%d %H:%M:%S', '%Y-%m-%d'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(raw_ddl, fmt)
        except ValueError:
            continue
    return None

def get_status_style_key(ddl_dt, is_done):
    """根据时间和状态，返回 UI_CONFIG 中的颜色键名"""
    if is_done:
        return "status_done"
    
    if ddl_dt is None:
        return "status_none"

    now = datetime.now()
    if ddl_dt < now:
        return "status_overdue"
    elif ddl_dt < now + timedelta(days=1):
        return "status_urgent"
    else:
        return "status_future"

def format_group_content(item):
    """处理群组便签的显示文本（发送者 + 内容 + 完成名单）"""
    content = item.get('content', '')
    owner = item.get('owner', 'Unknown')
    
    # 1. 拼装第一行：发送者 + 内容
    sender_style = UI_CONFIG['theme']['content_sender']
    display_text = f"[{sender_style}]{owner}[/]: {content}"

    # 2. 拼装第二行：完成者名单
    comps = item.get('completed_members', [])
    if comps:
        joined = ", ".join(comps)
        
        meta_style = UI_CONFIG['theme']['content_meta']
        display_text += f"\n[{meta_style}]  ↳ Done: {joined}[/]"
        
    return display_text

# =============================================================================
# 3. 组件渲染函数
# =============================================================================

def create_list_panel(title, tips_list, border_color):
    """绘制通用的列表面板"""
    layout = UI_CONFIG["layout"]
    icons = UI_CONFIG["icons"]
    theme = UI_CONFIG["theme"]

    # 表格初始化
    table = Table(
        box=None, 
        expand=True, 
        padding=(0, 1), 
        show_header=True, 
        header_style=theme["table_header"]
    )
    
    table.add_column("ID", justify="left", width=layout["col_id_width"], style="cyan")
    table.add_column("DDL", justify="left", width=layout["col_ddl_width"])
    table.add_column("Done", justify="center", width=layout["col_done_width"])
    table.add_column("Content", justify="left", style="white")

    if not tips_list:
        table.add_row("-", "-", "-", "[dim]No tips available[/dim]")
        return Panel(table, title=f"[bold {border_color}]{title}[/]", border_style=f"bold {border_color}", box=box.ROUNDED, width=layout["width"])

    # 遍历数据
    for item in tips_list:
        # A. 准备数据
        raw_ddl = item.get('ddl')
        is_done = item.get('is_done', False)
        idx = str(item.get('index', '?'))
        is_group = (item.get('type') == 'GROUP')

        # B. 计算样式
        ddl_dt = parse_ddl(raw_ddl)
        style_key = get_status_style_key(ddl_dt, is_done)
        color_tag = theme[style_key] # 从配置获取颜色 (如 "bold red")
        
        # C. 准备内容列
        if is_group:
            content_display = format_group_content(item)
        else:
            # 私人内容简单截断
            content_display = item.get('content', '')


        # D. 准备图标
        icon = icons["done"] if is_done else icons["todo"]
        
        # E. 填充表格
        # 注意：DDL 如果解析失败，ddl_dt 为 None，显示原始字符串
        ddl_str = raw_ddl if raw_ddl else "-"
        table.add_row(
            idx, 
            f"[{color_tag}]{ddl_str}[/]", 
            icon, 
            content_display
        )

    return Panel(
        table,
        title=f"[bold {border_color}]{title}[/]",
        title_align="left",
        border_style=f"bold {border_color}",
        box=box.ROUNDED,
        width=layout["width"],
        expand=False
    )

def draw_main_ui(client_obj, status_msg):
    clear_screen()
    
    # 快捷引用配置
    theme = UI_CONFIG["theme"]
    layout = UI_CONFIG["layout"]
    
    # =========================================================
    # 1. 数据准备 & 过滤
    # =========================================================
    all_tips = getattr(client_obj, 'local_cache', [])
    
    # --- 1.1 私人便签 (永远显示) ---
    private_list = [t for t in all_tips if t.get('type') == 'PRIVATE']

    # --- 1.2 群组便签 (根据 current_group_id 过滤) ---
    current_gid = getattr(client_obj, 'current_group_id', None)
    
    group_list = []
    # 只有当用户确实进入了某个群组时，才去筛选
    if current_gid is not None:
        for t in all_tips:
            if t.get('type') == 'GROUP':
                # 强转字符串比较，防止 int/str 类型不一致导致匹配失败
                if str(t.get('group_id')) == str(current_gid):
                    group_list.append(t)

    # =========================================================
    # 2. 修正群组名称 
    # =========================================================
    g_name = getattr(client_obj, 'current_group_name', 'None')
    
    if current_gid is None:
        g_name = "No Group Selected"
    elif group_list and (g_name in ['None', 'Unknown', 'Unknown Group']):
        # 从数据里得到真正的群名
        first_real_name = group_list[0].get('group_name')
        if first_real_name:
            g_name = first_real_name
            # (可选) 顺手帮 client 更新一下，下次渲染就不用再偷了
            if hasattr(client_obj, 'current_group_name'):
                client_obj.current_group_name = g_name
    elif g_name == 'None':
        # 如果既没名字，列表也是空的
        g_name = f"Group ID: {current_gid}"

    # =========================================================
    # 3. 绘制 Header
    # =========================================================
    now_str = datetime.now().strftime('%H:%M')
    user_name = getattr(client_obj, 'current_user', 'User') 
    user_id = getattr(client_obj, 'current_user_id', 'ID')
    header = Text()
    header.append(" TIPS CLIENT ", style=f"{theme['header_fg']} on {theme['header_bg']}")
    header.append(f" User: {user_name}#ID:{user_id} ", style=theme['user_highlight'])
    header.append(f"| {now_str}", style="dim")
    
    console.print(header)
    console.print("") # 空行

    # =========================================================
    # 4. 绘制两个面板
    # =========================================================
    # 私人面板
    console.print(create_list_panel(
        "🏠 Private Tips", 
        private_list, 
        theme["border_private"]
    ))

    # 群组面板
    console.print(create_list_panel(
        f"👥 Group: {g_name}", 
        group_list, 
        theme["border_group"]
    ))

    # =========================================================
    # 5. Footer & Status
    # =========================================================
    console.print("")
    console.print(f"[dim]{'-' * layout['width']}[/]")
    
    # --- 状态栏防溢出处理 ---
    status_str = str(status_msg).replace('\n', ' | ')
    # 预留一点空间给 "Status: " 字样
    # limit_len = layout['width'] - 15 
    
    # if len(status_str) > limit_len: 
    #     status_str = status_str[:limit_len-3] + "..."
    
    console.print(f"[{theme['status_urgent']}] 🔔 Status: {status_str}[/]")
    console.print(f"[dim]{'-' * layout['width']}[/]")

    console.print("[bold white] Command : help for help ; r for refresh ; q to quit [/bold white]")