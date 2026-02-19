with open('C:\\Users\\HP\\.openclaw\\workspace\\ClawForge\\backend\\__init__.py', 'r') as f:
    content = f.read()

# Find and replace the __all__ section
start = content.find('# NVIDIA API')

new_section = """)
    
    # NVIDIA API
    "NvidiaAPIClient",
    "UnifiedAPIClient",
    "get_unified_client",
    "test_nvidia_api_key",
    
    # Features (Consolidated)
    "get_memory_stats",
    "search_memory",
    "web_search",
    "fetch_url",
    "get_git_status",
    "git_commit",
    "text_to_speech",
    "list_voices",
    "read_file_content",
    "edit_file_content",
    "generate_plan",
]"""

new_content = content[:start] + new_section

with open('C:\\Users\\HP\\.openclaw\\workspace\\ClawForge\\backend\\__init__.py', 'w') as f:
    f.write(new_content)

print('Updated __all__ section')
