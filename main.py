# main.py
import sys
import readline
from core.client import TipsClient
from ui import renderer, style
from getpass import getpass


def main():
    # 1. 初始化
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

        # --- TUI 阶段 ---
        sys.stdout.write(style.Term.ALT_SCREEN_ON)
        in_tui_mode = True  
        
        status_msg = f"Welcome {u}! Fetching..."
        msg, _ = client.fetch_tips() 
        status_msg = msg
        
        while True:
            renderer.draw_main_ui(client, status_msg)
            
            cmd = input(" : ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd == 'r':
                status_msg = "Refreshing..."
                renderer.draw_main_ui(client, status_msg)
                msg, _ = client.fetch_tips()
                status_msg = msg
            elif cmd == 'a':
                c = input("   > Content: ")
                d = input("   > DDL: ")
                msg, refresh = client.add_tip(c, d)
                status_msg = msg
                if refresh: client.fetch_tips()
            elif cmd == 'd':
                idx = input("   > Delete Indexes (e.g., 1,2,5):")
                msg, refresh = client.delete_tips(idx)
                status_msg = msg
                if refresh: client.fetch_tips()
            elif cmd == 'c':
                idx = input("   > Change tips state Indexes (e.g., 1,2,5): ")
                msg, refresh = client.change_tip_state(idx)
                status_msg = msg
                if refresh: client.fetch_tips()
            elif cmd == 'create_group':
                name = input("   > Group Name: ").strip()
                msg, _ = client.create_group(name)
                status_msg = msg
            elif cmd == 'join_group':
                gid = input("   > Group invite code: ").strip()
                msg, _ = client.join_group(gid)
                status_msg = msg
            elif cmd == 'list_my_groups':
                msg, _ = client.list_my_groups()
                status_msg = msg
            elif cmd == 'get_group_info':
                gid = input("   > Group ID: ").strip()
                msg, _ = client.get_group_info(gid)
                status_msg = msg
            elif cmd == 'set_group_admin':
                gid = input("   > Group ID: ").strip()
                user_ids = input("   > New Admin id(e.g.1,2,3): ")
                msg, _ = client.set_group_admin(gid, user_ids)
                status_msg = msg

    except KeyboardInterrupt:
        if not in_tui_mode:
            print("\n\n[!] Login cancelled by user.")
        else:
            pass

    finally:
        if in_tui_mode:
            sys.stdout.write(style.Term.ALT_SCREEN_OFF)
            sys.stdout.flush()
        print("Bye!")

if __name__ == "__main__":
    main()