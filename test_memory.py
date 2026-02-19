import requests

print('Testing memory API...')

# Add memories
memories_to_add = [
    {'content': 'User name is Amir Ali', 'category': 'personal', 'importance': 10, 'tags': ['name', 'identity']},
    {'content': 'User lives in Lahore, Pakistan', 'category': 'personal', 'importance': 8, 'tags': ['location']},
    {'content': 'User is a content writer and copywriter', 'category': 'fact', 'importance': 7, 'tags': ['profession', 'work']},
    {'content': 'User prefers professional but premium tone on LinkedIn', 'category': 'preference', 'importance': 6, 'tags': ['writing', 'style']},
    {'content': 'User is working on ClawForge AI Agent project', 'category': 'context', 'importance': 9, 'tags': ['project', 'ai']}
]

for mem in memories_to_add:
    resp = requests.post('http://127.0.0.1:8000/api/memory/add', json=mem)
    print(f'Add memory: {resp.status_code}')

# Get all memories
resp = requests.get('http://127.0.0.1:8000/api/memory/all')
data = resp.json()
print(f'Total memories: {data.get("total", 0)}')

# Get stats
resp = requests.get('http://127.0.0.1:8000/api/memory/stats')
stats = resp.json()
print('By category:')
for cat, count in stats.get('by_category', {}).items():
    if count > 0:
        print(f'  {cat}: {count}')

print()
print('Memories added successfully!')
