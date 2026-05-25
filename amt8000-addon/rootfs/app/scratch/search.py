import urllib.request
import urllib.parse
import json
import re

def search_github():
    print("=== Searching GitHub for 'intelbras' repositories ===")
    url = "https://api.github.com/search/repositories?q=intelbras"
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            items = data.get('items', [])
            print(f"Found {len(items)} repositories.")
            for item in items:
                print(f"Repo: {item['full_name']} - {item['description']}")
                # Search for files in the repo
                search_repo_files(item['full_name'])
    except Exception as e:
        print("Error:", e)

def search_repo_files(repo_name):
    # Query code or search commits or files
    url = f"https://api.github.com/repos/{repo_name}/git/trees/main?recursive=1"
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            tree = data.get('tree', [])
            for file in tree:
                path = file.get('path', '')
                if any(x in path.lower() for x in ['client', 'protocol', 'intelbras', 'amt', 'sec']):
                    if path.endswith('.py') or path.endswith('.go'):
                        print(f"  File: {path}")
                        # Check contents of interesting files
                        if 'client' in path.lower() or 'protocol' in path.lower():
                            check_file_contents(repo_name, path)
    except Exception:
        # Try master if main doesn't exist
        url = f"https://api.github.com/repos/{repo_name}/git/trees/master?recursive=1"
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                tree = data.get('tree', [])
                for file in tree:
                    path = file.get('path', '')
                    if any(x in path.lower() for x in ['client', 'protocol', 'intelbras', 'amt', 'sec']):
                        if path.endswith('.py') or path.endswith('.go'):
                            print(f"  File: {path}")
                            if 'client' in path.lower() or 'protocol' in path.lower():
                                check_file_contents(repo_name, path)
        except Exception:
            pass

def check_file_contents(repo_name, path):
    url = f"https://raw.githubusercontent.com/{repo_name}/master/{path}"
    # try master then main
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    content = ""
    try:
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8')
    except Exception:
        url = f"https://raw.githubusercontent.com/{repo_name}/main/{path}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req) as response:
                content = response.read().decode('utf-8')
        except Exception:
            return

    # Check for bypass / arm / disarm / 401C
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if any(x in line.lower() for x in ['bypass', 'anular', 'anul', '401', '0x1c', '0x1e']):
            print(f"    [{path}:{i+1}]: {line.strip()}")

search_github()
