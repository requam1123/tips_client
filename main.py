# main.py
import sys
import readline
import signup
from core.client import TipsClient
from core.CommandHandler import CommandHandler # 引入刚才写的处理器
from ui import renderer, style
from getpass import getpass
import os
import pickle
import uuid
import datetime
from hashlib import sha256
from config import AUTO_LOGIN_FILE, VERSION

def autoLogin(username, password):
    mac = hex(uuid.getnode())
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    token = f"{mac}|{now}"
    tks = f"{token}={username}:{password}"
    token_hash = sha256(tks.encode('utf-8')).hexdigest()
    with open("./core/Auth.pkl", "wb") as f:
        pickle.dump((token, token_hash, username, password), f)
    
def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--signup':
        try:
            signup.signup() 
        except KeyboardInterrupt:
            print("\n已取消注册。")
        return 
    
    client = TipsClient()
    in_tui_mode = False 

    try:
        # --- 登录阶段 ---
        print("--- Login ---")
        auth_file = AUTO_LOGIN_FILE
        flag=False
        if auth_file and os.path.exists(auth_file):
            try:
                with open(auth_file, "rb") as f:
                    auth_data = pickle.load(f)
            except Exception as e:
                print(f"自动登录失败: {e}")
            if auth_data and len(auth_data) == 4:
                token, token_hash, username, password = auth_data
                mac = hex(uuid.getnode())
                now = datetime.datetime.now()
                token_parts = token.split('|')
                if len(token_parts) != 2:
                    print(f"自动登录失败: 无效的认证数据格式。")
                    os.remove(auth_file)
                token_mac, token_time_str = token_parts
                try:
                    token_time = datetime.datetime.strptime(token_time_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    print(f"自动登录失败: 无效的认证数据格式。")
                    os.remove(auth_file)
                    token_time = None
                if token_mac != mac:
                    print(f"自动登录失败: 设备不匹配。")
                    os.remove(auth_file)
                elif token_time and (now - token_time).days > 30:
                    print(f"自动登录失败: 认证已过期，请重新登录。")
                    os.remove(auth_file)
                else:
                    expected_tks = f"{token}={username}:{password}"
                    expected_hash = sha256(expected_tks.encode('utf-8')).hexdigest()
                    if expected_hash == token_hash:
                        success, msg = client.login(username, password)
                        if success:
                            print(f"自动登录成功，欢迎 {username}！")
                            flag=True
                        if not success:
                            print(f"自动登录失败: {msg}")
                            os.remove(auth_file)
                
            else:
                print(f"自动登录失败: 无效的认证数据格式。")
                os.remove(auth_file)
        
        if not flag:
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
            else:
                print(f"\nLogin Successful. Welcome, {u}!")
                if auth_file: autoLogin(u, p)

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
            'auth' : handler.tntauth,
            'uauth' : handler.tntunauth,
            'auto_login' : handler.change_auto_login,
            'kill_auto_login' : handler.del_auto_login,
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
                func:function = COMMAND_MAP[raw_cmd]
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