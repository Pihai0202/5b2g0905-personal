import os
import sys
import json
import urllib.request
import urllib.error
import subprocess

REPO_NAME = "5b2g0905-personal"
COLLABORATOR = "5b2g0905-sys"
PROJECT_DIR = r"C:\Users\User\Documents\antigravity\friendly-newton"

def run_git_cmd(args):
    print(f"Executing: git {' '.join(args)}")
    res = subprocess.run(["git"] + args, cwd=PROJECT_DIR, capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        print(f"Git Warning/Error: {res.stderr.strip()}")
    return res

def make_github_request(url, method, token, data=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "Antigravity-Agent")
    
    if data is not None:
        req.add_header("Content-Type", "application/json")
        json_data = json.dumps(data).encode("utf-8")
    else:
        json_data = None
        
    try:
        with urllib.request.urlopen(req, data=json_data) as response:
            if response.status in [200, 201, 204]:
                content = response.read().decode("utf-8")
                return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8") if e.fp else ""
        print(f"HTTP Error {e.code}: {e.reason}")
        print(f"Response: {err_msg}")
        raise e
    except Exception as e:
        print(f"Error making request: {e}")
        raise e

def main():
    print("=" * 60)
    print(" GitHub 儲存庫自動設定工具 ")
    print("=" * 60)
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", help="GitHub Personal Access Token")
    parser.add_argument("--username", help="GitHub Username")
    cmd_args = parser.parse_args()
    
    token = cmd_args.token
    username = cmd_args.username
    
    if not token and not username:
        token = input("請輸入您的 GitHub Personal Access Token (PAT)\n(若要手動建立儲存庫，請直接按 Enter 跳過): ").strip()
    
    # If no token is provided but username is, it is a non-interactive manual run
    is_interactive = not cmd_args.token and not cmd_args.username

    if token:
        try:
            print("\n正在驗證您的 GitHub Token...")
            user_data = make_github_request("https://api.github.com/user", "GET", token)
            username = user_data.get("login")
            print(f"驗證成功！帳號名稱：{username}")
            
            # Create repository
            print(f"\n正在 GitHub 上建立儲存庫 '{REPO_NAME}'...")
            repo_payload = {
                "name": REPO_NAME,
                "description": "個人網站與課堂作業遊戲網頁",
                "private": False,
                "has_issues": True,
                "has_projects": True,
                "has_wiki": True
            }
            try:
                make_github_request("https://api.github.com/user/repos", "POST", token, repo_payload)
                print(f"成功在 GitHub 建立儲存庫 '{REPO_NAME}'！")
            except urllib.error.HTTPError as e:
                if e.code == 422:
                    print(f"提示：儲存庫 '{REPO_NAME}' 可能已經存在。將繼續執行後續步驟。")
                else:
                    raise e
            
            # Add collaborator
            print(f"\n正在將 '{COLLABORATOR}' 新增為共同編輯者...")
            collab_url = f"https://api.github.com/repos/{username}/{REPO_NAME}/collaborators/{COLLABORATOR}"
            try:
                make_github_request(collab_url, "PUT", token, {"permission": "push"})
                print(f"已成功發送共同編輯者邀請給 '{COLLABORATOR}'！")
            except urllib.error.HTTPError as e:
                print(f"新增共同編輯者失敗：{e}")
                
        except Exception as e:
            print(f"\nAPI 執行過程中發生錯誤：{e}")
            print("將改用手動引導模式...")
            token = None

    if not token:
        if is_interactive:
            print("\n--- 手動建立儲存庫模式 ---")
            print(f"1. 請前往您的 GitHub (https://github.com/new) 建立一個名為 '{REPO_NAME}' 的新儲存庫。")
            print(f"2. 建立完成後，請將 '{COLLABORATOR}' 加為共同編輯者 (Settings -> Collaborators)。")
            input("完成上述步驟後，請按 Enter 鍵以繼續將本地程式碼推送至儲存庫...")
            
            # Ask for username to setup git remote
            username = input("請輸入您的 GitHub 使用者名稱 (例如 Pihai0202): ").strip()
            while not username:
                username = input("使用者名稱不能為空，請輸入: ").strip()
        else:
            if not username:
                print("Error: In non-interactive mode, --username must be provided if --token is not specified.")
                sys.exit(1)

    # Git Operations
    print("\n正在初始化本地 Git 與提交變更...")
    run_git_cmd(["init"])
    run_git_cmd(["add", "."])
    run_git_cmd(["commit", "-m", "Initial commit of personal website and games"])
    run_git_cmd(["branch", "-M", "main"])
    
    # Remove existing remote if any
    run_git_cmd(["remote", "remove", "origin"])
    
    # Add remote
    remote_url = f"https://github.com/{username}/{REPO_NAME}.git"
    run_git_cmd(["remote", "add", "origin", remote_url])
    
    print(f"\n正在推送變更至 {remote_url}...")
    if token:
        # Push using token in URL (temporary)
        push_url = f"https://{token}@github.com/{username}/{REPO_NAME}.git"
        res = subprocess.run(["git", "push", "-u", push_url, "main"], cwd=PROJECT_DIR, capture_output=True, text=True)
        if res.returncode == 0:
            print("成功推送到 GitHub 儲存庫！")
        else:
            print(f"推送失敗：{res.stderr.strip()}")
            print("請嘗試手動執行: git push -u origin main")
    else:
        # Push using standard URL (prompts Git Credential Manager)
        res = subprocess.run(["git", "push", "-u", "origin", "main"], cwd=PROJECT_DIR, capture_output=True, text=True)
        if res.returncode == 0:
            print("成功推送到 GitHub 儲存庫！")
        else:
            print(f"推送失敗：{res.stderr.strip()}")
            print("請嘗試手動執行: git push -u origin main")

    print("\n設定完成！")

if __name__ == "__main__":
    main()
