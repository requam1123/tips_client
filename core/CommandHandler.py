# core/handler.py (新建)
import sys
from ui import style
from core.client import TipsClient

class CommandHandler:
    def __init__(self, client : TipsClient, renderer):
        self.client = client
        self.renderer = renderer
        self.status_msg = f"Welcome {client.current_user}!"

    def refresh_ui(self):
        self.renderer.draw_main_ui(self.client, self.status_msg)

    # --- 基础命令处理函数 ---
    
    def refresh(self):
        self.status_msg = "Refreshing..."
        self.refresh_ui() 
        msg, _ = self.client.fetch_tips()
        self.status_msg = msg

    def add_tip(self):
        print("\n[Add Tip]")
        c = input("   Content: ")
        d = input("   DDL (YY-MM-DD HH:MM): ")
        g = input("   Group ID (leave empty for Private): ").strip()
        group_id = int(g) if g.isdigit() else None
        msg, refresh = self.client.add_tip(c, d, group_id)
        self.status_msg = msg
        if refresh: self.client.fetch_tips()

    def delete_tip(self):
        idx = input("\n[Delete] Indexes (e.g. 1,2): ")
        msg, refresh = self.client.delete_tips(idx)
        self.status_msg = msg
        if refresh: self.client.fetch_tips()

    def change_state(self):
        idx = input("\n[Change State] Indexes (e.g. 1,2): ")
        msg, refresh = self.client.change_tip_state(idx)
        self.status_msg = msg
        if refresh: self.client.fetch_tips()

    # --- 群组命令 ---

    def create_group(self):
        name = input("\n[Create Group] Name: ").strip()
        msg, _ = self.client.create_group(name)
        self.status_msg = msg

    def join_group(self):
        gid = input("\n[Join Group] Invite Code: ").strip()
        msg, _ = self.client.join_group(gid)
        self.status_msg = msg

    def list_groups(self):
        # 暂时切出 TUI 显示列表
        sys.stdout.write(style.Term.ALT_SCREEN_OFF)
        groups, _ = self.client.list_my_groups()
        print("\n--- My Groups ---")
        if not groups:
            print("   (No groups joined)")
        for g in groups:
            print(f"ID: {g['id']} | Name: {g['name']} | Role: {g['role']} | Code: {g['invite_code']}")
        input("\nPress Enter to return...")
        sys.stdout.write(style.Term.ALT_SCREEN_ON)
        self.status_msg = "Group list checked."

    def set_group_admin(self):
        gid = input("   > Group ID to set admin: ").strip()
        uid = input("   > User ID to promote: ").strip()
        msg, _ = self.client.set_group_admin(gid, uid)
        self.status_msg = msg

    def enter_group(self):
        gid = input("   > Group ID to enter: ").strip()
        msg, refresh = self.client.enter_group(gid)
        self.status_msg = msg
        if refresh: self.client.fetch_tips()

    def get_group_info(self):
        gid = input("   > Group ID to show info: ").strip()
        msg, _ = self.client.get_group_info(gid)
        self.status_msg = msg
    
    def get_my_group(self):
        msg, _ = self.client.list_my_groups()
        self.status_msg = msg
    
    def show_help(self):
        help_text = """
Available Commands:
    help              : 打开指令笔记本
    a                 : 新增tips
    d                 : 删除tips
    c                 : 修改tips状态（完成/未完成）
    r                 : 刷新界面
    q                 : 退出程序
    create_group      : 创造一个新群组
    join_group        : 加入一个群组
    get_group_info    : 展示某个群组的成员信息
    get_my_group      : 列出我加入的所有群组
    set_group_admin   : 设置管理员（需要你是群主）
    enter             : 切换到某个群组
"""
        sys.stdout.write(style.Term.ALT_SCREEN_OFF)
        print(help_text)
        input("Press Enter to return...")
        sys.stdout.write(style.Term.ALT_SCREEN_ON)
        self.status_msg = "Help displayed."

