import requests

# Test backend connection
try:
    r = requests.get('http://127.0.0.1:8000/api/health', timeout=5)
    print('[OK] Backend connection: OK')
    print('Status:', r.status_code)
except Exception as e:
    print('[FAILED] Backend connection: FAILED')
    print('Error:', e)

# Test API endpoints
try:
    r = requests.get('http://127.0.0.1:8000/api/prompt/personas', timeout=5)
    if r.status_code == 200:
        data = r.json()
        print('[OK] Prompt API: OK')
        print('Personas available:', len(data.get('personas', [])))
    else:
        print('[FAILED] Prompt API: Error', r.status_code)
except Exception as e:
    print('[FAILED] Prompt API: FAILED')
    print('Error:', e)
