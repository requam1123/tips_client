import requests
from config import SERVER_URL
from datetime import datetime
from core.crypto import encrypt_password

class TipsClient:
    def __init__(self):
        self.session = requests.Session()
        self.current_user = None
        
        # Unified cache for both private and group tips
        self.local_cache = [] 
        
        # We need these placeholders so renderer.py doesn't crash
        # (Renderer checks for these if using the split-view logic, 
        # but we are using the unified view logic now)
        self.current_group_id = None
        self.current_group_name = "None"

    def login(self, username, password):
        try:    
            resp = self.session.get(f"{SERVER_URL}/public_key/", timeout=5)
            if resp.status_code != 200: return False, "Server connect error"
            pem_key = resp.json()['public_key'].encode('utf-8')
        except Exception as e:
            return False, f"Network error: {e}"

        enc_pwd = encrypt_password(password, pem_key)
        try:
            resp = self.session.post(f"{SERVER_URL}/login/", json={
                "username": username, "password": enc_pwd
            })
            if resp.status_code == 200:
                self.current_user = username
                return True, "Login Success"
            return False, resp.text
        except Exception as e:
            return False, f"Login Error: {e}"
        
    def sign_up(self, username, password, invite_code):
        try:    
            resp = self.session.get(f"{SERVER_URL}/public_key/", timeout=5)
            if resp.status_code != 200: return False, "Server connect error"
            pem_key = resp.json()['public_key'].encode('utf-8')
        except Exception as e:
            return False, f"Network error: {e}"

        enc_pwd = encrypt_password(password, pem_key)
        try:
            resp = self.session.post(f"{SERVER_URL}/users/signup/", json={
                "username": username, 
                "password": enc_pwd,
                "invite_code": invite_code
            })
            if resp.status_code == 200:
                return True, "Sign Up Success"
            return False, resp.text
        except Exception as e:
            return False, f"Sign Up Error: {e}"

    def fetch_tips(self):
        """
        Fetch all tips (private + group) and merge them into local_cache.
        """
        try:
            resp = self.session.get(f"{SERVER_URL}/show_tips/")
            
            if resp.status_code == 200:
                data = resp.json()
                
                raw_private = data.get('private_tips', [])
                raw_public = data.get('public_tips', [])
                maps = data.get('maps', {})
                
                self.local_cache = []

                # 1. Process Private Tips
                for tip in raw_private:
                    self.local_cache.append({
                        'index': tip['index'],
                        'real_id': maps.get(str(tip['index'])), 
                        'content': tip['content'],
                        'ddl': tip['ddl'],
                        'is_done': tip['is_done'],
                        'type': 'PRIVATE',
                        # 私人便签通常没有这个列表，给个空列表保持结构统一
                        'completed_members': []
                    })

                # 2. Process Public (Group) Tips
                for tip in raw_public:
                    self.local_cache.append({
                        'index': tip['index'],
                        'real_id': maps.get(str(tip['index'])),
                        'content': tip['content'], 
                        'ddl': tip['ddl'],
                        'is_done': tip['is_done'], # 这是当前用户(你)的状态，用于打钩
                        'type': 'GROUP',
                        'group_name' : tip.get('group_name', 'Unknown'),
                        'owner': tip.get('owner_name', 'Unknown'),
                        
                        # 【新增】这里接收后端传来的名单列表 ["Alice", "Bob"]
                        'completed_members': tip.get('completed_members', [])
                    })
                
                # Sort by index just in case
                self.local_cache.sort(key=lambda x: x['index'])

                # 获取群组ID (转为字符串以防 UI 报错)
                self.current_group_name = str(data.get('group_id')) if data.get('group_id') else "None"

                return f"Updated {len(self.local_cache)} tips.", False
            
            return f"Auth failed or Server error: {resp.status_code}", False
        except Exception as e:
            return f"Network Error: {e}", False

    def add_tip(self, content, ddl , group_id:int | None=None):
        if not self._check_ddl_format(ddl):
            return "Invalid date format (YY-MM-DD HH:MM).", False
        
        try:
            # If you want to support adding to group, you need to set self.current_group_id
            # For now, this defaults to private (group_id=None)
            payload = {
                "content": content, 
                "ddl": ddl if ddl else None,
                "group_id": group_id 
            }
            resp = self.session.post(f"{SERVER_URL}/add_tip/", json=payload)
            if resp.status_code == 200:
                return "Tip added successfully!", True
            return f"Add failed: {resp.status_code}", False
        except Exception as e:
            return f"Error: {str(e)}", False
        
    

    def delete_tips(self, input_str: str , group_id:int | None=None):
        if not self.local_cache: return "No tips locally.", False
        try:
            indexes = set()
            parts = input_str.split(',')
            for part in parts:
                if part.strip().isdigit():
                    indexes.add(int(part.strip()))
            
            if not indexes: return "No valid indexes.", False

            real_ids = []
            for item in self.local_cache:
                if item['index'] in indexes:
                    real_ids.append(item['real_id'])
            
            if not real_ids: return "Could not map to Real IDs.", False

            # Backend expects 'delete_ids' list
            response = self.session.post(f"{SERVER_URL}/delete_tips/", json={
                "tips_ids": real_ids,
                "group_id": group_id
            })
            if response.status_code == 200:
                return f"Deleted {len(real_ids)} tips.", True
            return f"Delete failed: {response.text}", False

        except Exception as e:
            return f"Delete Error: {str(e)}", False
        
    def change_tip_state(self, input_str: str):
        if not self.local_cache: return "No tips locally.", False
        try:
            indexes = set()
            parts = input_str.split(',') 
            for part in parts:
                if part.strip().isdigit():
                    indexes.add(int(part.strip()))
            
            real_ids = []
            for item in self.local_cache:
                if item['index'] in indexes:
                    real_ids.append(item['real_id'])
            
            if not real_ids: return "No valid IDs.", False

            # Key is 'tips_ids' per your backend
            response = self.session.post(f"{SERVER_URL}/change_tip_state/", json={"tips_ids": real_ids})
            if response.status_code == 200:
                return f"Changed state.", True
            return f"Failed: {response.text}", False
        except Exception as e:
            return f"Error: {str(e)}", False

    def _check_ddl_format(self, ddl_str):
        try:
            if not ddl_str: return True
            datetime.strptime(ddl_str, "%y-%m-%d %H:%M")
            return True
        except ValueError:
            return False

    # === Group Actions ===
    def create_group(self, name):
        try:
            resp = self.session.post(f"{SERVER_URL}/groups/create", json={"name": name})
            if resp.status_code == 200:
                return f"Created! Code: {resp.json()['invite_code']}", True
            return f"Failed: {resp.text}", False
        except Exception as e: return f"Error: {e}", False

    def join_group(self, invite_code):
        try:
            # Fixed URL construction
            resp = self.session.post(f"{SERVER_URL}/groups/join/{invite_code}")
            if resp.status_code == 200:
                return f"Joined group successfully!", True
            return f"Join failed: {resp.text}", False
        except Exception as e: return f"Error: {e}", False

    def list_my_groups(self):
        try:
            resp = self.session.get(f"{SERVER_URL}/groups/my")
            if resp.status_code == 200:
                # Backend returns {"groups": [...]}
                return resp.json().get('groups', []), False 
            return [], False
        except: return [], False
    
    def get_group_info(self, group_id):
        try:
            # Fixed URL: /members instead of /info
            resp = self.session.get(f"{SERVER_URL}/groups/{group_id}/members")
            if resp.status_code == 200:
                return resp.json()['members'], True
            return f"Error: {resp.text}", False
        except Exception as e: return f"Network Error: {e}", False
    
    def set_group_admin(self, group_id: int, user_ids: list):
        try:
            if not user_ids: return "Invalid user IDs", False
            resp = self.session.post(f"{SERVER_URL}/groups/set_admin", json={
                "group_id": group_id,
                "user_ids": user_ids
            })
            if resp.status_code == 200: return "Admins updated!", True
            return f"Failed: {resp.text}", False
        except Exception as e: return f"Error: {e}", False

    # === Context Switching ===
    def enter_group(self, group_id):
        """Set context to a specific group so Add Tip goes there"""
        self.current_group_id = int(group_id)
        return f"Context switched to Group {group_id}" , True

    def exit_group(self):
        """Set context back to private"""
        self.current_group_id = None
        return "Context switched to Private"