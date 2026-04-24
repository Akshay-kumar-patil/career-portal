import sys

path = r'd:\aiml\career-platform\frontend\utils\api_client.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# In text mode on Windows, \r\n is normalised to \n
old = (
    '    return _handle_response(resp)\n'
    '\n'
    '\n'
    '\n'
    '\n'
    'def login'
)
new = (
    '    return _handle_response(resp)\n'
    '\n'
    '\n'
    'def google_oauth_status():\n'
    '    """Check whether Google OAuth is configured on the backend."""\n'
    '    try:\n'
    '        resp = requests.get(f"{BASE_URL}/api/auth/google/status", timeout=5)\n'
    '        if resp.status_code == 200:\n'
    '            return resp.json()\n'
    '    except Exception:\n'
    '        pass\n'
    '    return None\n'
    '\n'
    '\n'
    'def get_google_login_url():\n'
    '    """Return the backend URL that starts the Google OAuth flow."""\n'
    '    return f"{BASE_URL}/api/auth/google"\n'
    '\n'
    '\n'
    'def login'
)

if old in content:
    content = content.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: Google OAuth helpers added to api_client.py')
else:
    print('ERROR: pattern not found — dumping raw chars around line 61:')
    idx = content.find('return _handle_response(resp)\n\n\n')
    print(repr(content[idx:idx+120]))
    sys.exit(1)
