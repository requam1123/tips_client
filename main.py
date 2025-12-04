import sys
from core.client import TipsClient
from ui import renderer, style
from getpass import getpass

def main():
    # 1. 初始化
    client = TipsClient()
    in_tui_mode = False  # 标志位：用来记录是否已经进入了 TUI 界面

    try:
        # --- 登录阶段 ---
        print("--- Login ---")
        u = input("User: ").strip()
        # 如果用户直接回车，也可以视为想退出
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
        in_tui_mode = True  # 标记：现在我们在 TUI 里了
        
        status_msg = f"Welcome {u}! Fetching..."
        msg, _ = client.fetch_tips() # 初始拉取
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
                # 这里的 input 也会被外层的 try 捕获，很安全
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