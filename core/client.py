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
                        
                        # 【建议补充】虽然是 private，但也显式给个 None，保持结构整齐
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
                        # 这里获取 group_id 很关键，UI 过滤要用
                        'group_id' : tip.get('group_id'),
                        'group_name' : tip.get('group_name', 'Unknown'),
                        'owner': tip.get('owner_name', 'Unknown'),
                        'completed_members': tip.get('completed_members', [])
                    })
                
                self.local_cache.sort(key=lambda x: x['index'])

                # ========================================================
                # 3. 处理当前上下文 (Group Context) - 修复重点
                # ========================================================
                
                # 如果还没有初始化 group_id，就用后端给的默认值
                if not hasattr(self, 'current_group_id') or self.current_group_id is None:
                    self.current_group_id = data.get('group_id')
                
                # 【关键修复】更新 group_name
                # 后端最外层通常没返回 group_name，所以 data.get('group_name') 可能是空的。
                # 我们需要去 cache 里的群组便签中 "偷" 一个名字出来。
                
                if self.current_group_id:
                    # 默认显示 ID，以防列表为空找不到名字
                    target_name = f"Group {self.current_group_id}"
                    
                    # 尝试从刚才处理好的 local_cache 里找这个群的名字
                    for item in self.local_cache:
                        # 注意类型转换：有些时候 id 是 int 有些是 str，转 str 比较最稳
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
            
            # === 修改处 START ===
            # 1. 在查找名字之前，必须先去服务器把这个组的数据拉下来！
            # 假设你有一个方法叫 fetch_tips() 用来更新 self.local_cache
            # 如果没有，你需要把那个 requests.get(...) 的逻辑加在这里
            try:
                self.fetch_tips() # <--- 关键：先刷新数据，填满 local_cache
            except Exception as e:
                # 如果拉取失败（比如没网，或者组不存在），还是会让它切过去，但名字是 Unknown
                pass 
            # === 修改处 END ===

            # 2. 现在缓存里有新组的数据了，再遍历就能找到了
            found_name = "Unknown Group"
            for t in self.local_cache:
                # 这里的逻辑是对的，只要 cache 是新的
                if t.get('group_id') == gid and t.get('group_name'):
                    found_name = t['group_name']
                    break
            
            # 如果这是一个空组（没有任何便签），上述循环还是找不到名字。
            # 这种情况下，更稳健的做法是单独请求 GET /groups/{id} 接口（如果有的话）。
            
            self.current_group_name = found_name
            return f"Context switched to Group {gid} ({found_name})", True
            
        except ValueError:
            return "Invalid Group ID", False

    def exit_group(self):
        """Set context back to private"""
        self.current_group_id = None
        return "Context switched to Private"