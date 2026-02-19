import os
import json

# Check memory directory
mem_dir = 'C:\\Users\\HP\\.openclaw\\workspace\\ClawForge\\memory'
print('Memory directory:', mem_dir)
print('Exists:', os.path.exists(mem_dir))
print()

if os.path.exists(mem_dir):
    files = os.listdir(mem_dir)
    print('Files in memory dir:', files)
    print()
    
    for f in files:
        path = os.path.join(mem_dir, f)
        if f.endswith('.json'):
            size = os.path.getsize(path)
            print(f'{f}: {size} bytes')
            with open(path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if isinstance(data, dict):
                    if 'memories' in data:
                        print(f'  Memories: {len(data["memories"])}')
                    if 'conversations' in data:
                        print(f'  Conversations: {len(data["conversations"])}')
else:
    print('Memory directory does not exist!')
