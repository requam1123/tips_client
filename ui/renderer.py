# ui/renderer.py
import sys
from datetime import datetime
from ui.style import Term
from core.client import TipsClient

UI_WIDTH = 56  # 假设终端宽度为56字符
def clear_screen():
    sys.stdout.write(Term.CLEAR)
    sys.stdout.flush()

def draw_main_ui(client_obj:TipsClient, status_msg):
    """
    接收 client 对象（包含 user 和 cache）来绘图
    """
    clear_screen()
    
    # Header
    now_str = datetime.now().strftime('%H:%M')
    print(f"{Term.BG_BLUE}{Term.BOLD}{Term.FG_WHITE} VIM-TIPS MANAGER {Term.RESET} User: {client_obj.current_user} | {now_str}")
    print("-" * UI_WIDTH)
    
    # Body
    if not client_obj.local_cache:
        print("\n   [No tips available]\n")
    else:
        print(f"{'ID':<4} | {'DDL':<16} | {'IsDone':<6} | {'CONTENT'}")
        print("-" * UI_WIDTH)
        for item in client_obj.local_cache:
            c = item['content']
            if len(c) > 30: c = c[:27] + "..."
            d = item['ddl'] if item['ddl'] else "None"
            is_done_str = "  ✅" if item['is_done'] else "  ❌"
            print(f"{item['index']:<4} | {d:<16} | {is_done_str:<6} | {c}")

    # Footer8
    print("-" * UI_WIDTH)
    print(f"{Term.FG_YELLOW} 🔔 Status: {status_msg}{Term.RESET}")
    print("-" * UI_WIDTH)
    print(" Command: [a]dd | [d]elete | [r]efresh | [q]uit | [c]hange states" )