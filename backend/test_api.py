import requests

r = requests.get('http://127.0.0.1:8000/api/prompt/personas')
print('Status:', r.status_code)
data = r.json()
print('Personas:', list(data.get('personas', []))[:10])
print('Total personas:', len(data.get('personas', [])))
