import requests
from config import SERVER_URL
from datetime import datetime
from core.crypto import encrypt_password

class TipsClient:
    def __init__(self):
        self.session = requests.Session()
        self.current_user = None
        self.current_user_id = None
        
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
                self.current_user_id = resp.json().get("user_id")
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
                        'completed_members': [],
                        'group_id': None 
                    })

                # 2. Process Public (Group) Tips
                for tip in raw_public:
                    self.local_cache.append({
                        'index': tip['index'],
                        'real_id': maps.get(str(tip['index'])),
                        'content': tip['content'], 
                        'ddl': tip['ddl'],
                        'is_done': tip['is_done'], 
                        'type': 'GROUP',
                        'group_id' : tip.get('group_id'),
                        'group_name' : tip.get('group_name', 'Unknown'),
                        'owner': tip.get('owner_name', 'Unknown'),
                        'completed_members': tip.get('completed_members', [])
                    })
                
                self.local_cache.sort(key=lambda x: x['index'])

                # ========================================================
                # 3. 处理当前上下文 (Group Context) 
                # ========================================================
                
                # 如果还没有初始化 group_id，就用后端给的默认值
                if not hasattr(self, 'current_group_id') or self.current_group_id is None:
                    self.current_group_id = data.get('group_id')
                
                if self.current_group_id:
                    target_name = f"Group {self.current_group_id}"
                    for item in self.local_cache:
                        if item.get('type') == 'GROUP' and str(item.get('group_id')) == str(self.current_group_id):
                            target_name = item.get('group_name', target_name)
                            break
                    
                    self.current_group_name = target_name
                else:
                    self.current_group_name = "None"

                return f"Updated {len(self.local_cache)} tips.", False
            
            return f"Auth failed or Server error: {resp.status_code}", False
        except Exception as e:
            return f"Network Error: {e}", False

    def add_tip(self, content, ddl , group_id:int | None=None):
        if not self._check_ddl_format(ddl):
            return "Invalid date format (YY-MM-DD HH:MM).", False
        
        try:
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
            resp = self.session.get(f"{SERVER_URL}/groups/{group_id}/info")
            if resp.status_code == 200:
                return resp.json()['members'], True
            return f"Error: {resp.text}", False
        except Exception as e: return f"Network Error: {e}", False
    
    def set_group_admin(self, group_id: int, user_ids): # 去掉 :list 避免误导，或者保留但要在内部处理
        try:
            if not user_ids: 
                return "Invalid user IDs", False
            
            if not isinstance(user_ids, list):
                if isinstance(user_ids, str) and ',' in user_ids:
                    real_user_ids = [uid.strip() for uid in user_ids.split(',')]
                else:
                    real_user_ids = [user_ids]
            else:
                real_user_ids = user_ids

            resp = self.session.post(f"{SERVER_URL}/groups/set_admin", json={
                "group_id": group_id,
                "user_ids": real_user_ids # 发送处理后的列表
            })
            
            if resp.status_code == 200: return "Admins updated!", True
            # 建议打印 resp.json() 方便调试，而不是 resp.text
            return f"Failed: {resp.text}", False
            
        except Exception as e: return f"Error: {e}", False

    # === Context Switching ===
    def enter_group(self, group_id):
        """切换群组视图"""
        try:
            gid = int(group_id)
            self.current_group_id = gid
            
            try:
                self.fetch_tips() 
            except Exception as e:
                # 如果拉取失败（比如没网，或者组不存在），还是会让它切过去，但名字是 Unknown
                pass 

            found_name = "Unknown Group"
            for t in self.local_cache:
                if t.get('group_id') == gid and t.get('group_name'):
                    found_name = t['group_name']
                    break
            self.current_group_name = found_name
            return f"Context switched to Group {gid} ({found_name})", True
            
        except ValueError:
            return "Invalid Group ID", False

    # def exit_group(self):
    #     """Set context back to private"""
    #     self.current_group_id = None
    #     return "Context switched to Private"