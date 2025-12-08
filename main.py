# main.py
import sys
import readline
from core.client import TipsClient
from core.CommandHandler import CommandHandler # 引入刚才写的处理器
from ui import renderer, style
from getpass import getpass

def main():
    client = TipsClient()
    in_tui_mode = False 

    try:
        # --- 登录阶段 ---
        print("--- Login ---")
        u = input("User: ").strip()
        if not u: 
            print("Empty username. Exiting.")
            return
        p = getpass("Pass: ").strip()
        if u == "admin":
            print("Admin 你妈的逼")
            return
        success, msg = client.login(u, p)
        if not success:
            print(f"\nLogin Failed: {msg}")
            return

        # --- TUI 初始化 ---
        sys.stdout.write(style.Term.ALT_SCREEN_ON)
        in_tui_mode = True  
        client.fetch_tips() # 初始拉取
        
        # 初始化处理器
        handler = CommandHandler(client, renderer)

        COMMAND_MAP = {
            'r': handler.refresh,
            'a': handler.add_tip,
            'd': handler.delete_tip,
            'c': handler.change_state,
            'create_group': handler.create_group,
            'join_group': handler.join_group,
            'list_my_groups': handler.list_groups,
            'get_group_info': handler.get_group_info,
            'get_my_group': handler.get_my_group,
            'set_group_admin': handler.set_group_admin,
            'enter': handler.enter_group,
            'help' : handler.show_help,
        }

        while True:
            # 1. 绘制界面
            handler.refresh_ui()
            
            # 2. 获取输入
            try:
                raw_cmd = input(" > ").strip().lower()
            except EOFError:
                break
            
            if not raw_cmd: continue
            if raw_cmd == 'q': break # 退出单独处理

            # 3. 【一键分发】查表执行
            if raw_cmd in COMMAND_MAP:
                func = COMMAND_MAP[raw_cmd]
                func() # 执行对应的函数
            else:
                handler.status_msg = f"Unknown command: {raw_cmd}"

    except KeyboardInterrupt:
        if not in_tui_mode: print("\n[!] Cancelled.")
    finally:
        if in_tui_mode:
            sys.stdout.write(style.Term.ALT_SCREEN_OFF)
            sys.stdout.flush()
        print("Bye!")

if __name__ == "__main__":
    main()