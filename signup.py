from getpass import getpass
from core.client import TipsClient

print("Sign up Need an invite code.")
u = input("Choose a username: ").strip()
p = getpass("Choose a password: ").strip()
recheck = getpass("Re-enter password: ").strip()
if u.lower() == "admin":
    print("Admin 你妈逼.")
    exit(1)
if p != recheck:
    print("Passwords do not match. Exiting.")
    exit(1)
invite_code = input("Invite Code: ").strip()
client = TipsClient()
success, msg = client.sign_up(u, p, invite_code)
print(msg)