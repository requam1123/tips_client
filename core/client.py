# core/client.py
import requests
from config import SERVER_URL
from datetime import datetime
from core.crypto import encrypt_password


class TipsClient:
    def __init__(self):
        self.session = requests.Session()
        self.current_user = None
        self.local_cache = [] # 存储 tips 数据
        
    def login(self, username, password):
        # 1. 获取公钥
        try:    
            resp = self.session.get(f"{SERVER_URL}/public_key/")
            if resp.status_code != 200: return False, "Server connect error"
            pem_key = resp.json()['public_key'].encode('utf-8')
        except:
            return False, "Network error"

        # 2. 加密并登录
        enc_pwd = encrypt_password(password, pem_key)
        resp = self.session.post(f"{SERVER_URL}/login/", json={
            "username": username, "password": enc_pwd
        })
        
        if resp.status_code == 200 and "login successful" in resp.text:
            self.current_user = username
            return True, "Login Success"
        return False, resp.text

    def fetch_tips(self):
        try:
            resp = self.session.get(f"{SERVER_URL}/show_tips/")
            if resp.status_code == 200:
                data:dict = resp.json()
                tips = data.get('tips', [])
                maps = data.get('maps', {})
                
                # 重建缓存
                new_cache = []
                for idx, tip in enumerate(tips, 1):
                    real_id = maps.get(str(idx)) 
                    # 这里你可以加个防御逻辑，如果real_id找不到
                    new_cache.append({
                        'index': idx,
                        'real_id': real_id,
                        'content': tip['content'],
                        'ddl': tip['ddl'],
                        'is_done': tip['is_done']
                    })
                self.local_cache = new_cache
                return f"Updated {len(self.local_cache)} tips.", False
            return "Auth failed or Server error.", False
        except Exception as e:
            return f"Network Error: {e}", False

    def add_tip(self, content, ddl):
        if not self._check_ddl_format(ddl):
            return "Invalid date format (YY-MM-DD HH:MM).", False
        
        try:
            payload = {"content": content, "ddl": ddl}
            response = self.session.post(f"{SERVER_URL}/add_tip/", json=payload)
            if response.status_code == 200:
                return "Tip added successfully!", True # True 表示建议刷新列表
            return f"Add failed: {response.status_code}", False
        except Exception as e:
            return f"Error: {str(e)}", False

    def delete_tips(self, input_str: str):
        """解析输入并删除"""
        if not self.local_cache:
            return "No tips locally to delete.", False
        try:
            # 解析输入 "1,2,5"
            indexes = set()
            parts = input_str.split(',')
            max_idx = len(self.local_cache)
            
            for part in parts:
                part = part.strip()
                if part.isdigit():
                    val = int(part)
                    if 1 <= val <= max_idx:
                        indexes.add(val)
            
            if not indexes:
                return "No valid indexes provided.", False

            # 找到对应的真实 ID
            real_ids = []
            for item in self.local_cache:
                if item['index'] in indexes:
                    real_ids.append(item['real_id'])
            
            if not real_ids:
                return "Could not map indexes to Real IDs.", False

            # 发送请求
            response = self.session.post(f"{SERVER_URL}/delete_tips/", json={"tips_ids": real_ids})
            if response.status_code == 200:
                return f"Deleted {len(real_ids)} tips.", True
            return f"Delete failed: {response.text}", False

        except Exception as e:
            return f"Delete Error: {str(e)}", False
        
    def change_tip_state(self,input_str: str):
        if not self.local_cache:
            return "No tips locally to change.", False
        try:
            # 解析输入 "1,2,5"
            indexes = set()
            parts = input_str.split(',')
            max_idx = len(self.local_cache)
            
            for part in parts:
                part = part.strip()
                if part.isdigit():
                    val = int(part)
                    if 1 <= val <= max_idx:
                        indexes.add(val)
            
            if not indexes:
                return "No valid indexes provided.", False

            # 找到对应的真实 ID
            real_ids = []
            for item in self.local_cache:
                if item['index'] in indexes:
                    real_ids.append(item['real_id'])
            
            if not real_ids:
                return "Could not map indexes to Real IDs.", False

            # 发送请求
            response = self.session.post(f"{SERVER_URL}/change_tip_state/", json={"tips_ids": real_ids})
            if response.status_code == 200:
                return f"Changed state of {len(real_ids)} tips.", True
            return f"Change state failed: {response.text}", False
        except Exception as e:
            return f"Change State Error: {str(e)}", False

    def _check_ddl_format(self, ddl_str):
        try:
            if not ddl_str: return True
            datetime.strptime(ddl_str, "%y-%m-%d %H:%M")
            return True
        except ValueError:
            return False
    