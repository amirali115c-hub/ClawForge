with open('C:\\Users\\HP\\.openclaw\\workspace\\ClawForge\\backend\\__init__.py', 'r') as f:
    content = f.read()

# Update the __all__ exports
old_exports = """    # Features (Consolidated)
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

new_exports = """    # Features (Consolidated)
    "get_memory_stats",
    "search_memories",
    "add_memory",
    "get_memories",
    "delete_memory",
    "get_privacy_settings",
    "update_privacy_settings",
    "export_memory_data",
    "import_memory_data",
    "clear_memory_data",
    "add_conversation",
    "get_conversations",
    "web_search",
    "fetch_url",
    "get_git_status",
    "git_commit",
    "text_to_speech",
    "list_voices",
    "read_file_content",
    "edit_file_content",
    "generate_plan",
    "longterm_memory",
]"""

content = content.replace(old_exports, new_exports)

with open('C:\\Users\\HP\\.openclaw\\workspace\\ClawForge\\backend\\__init__.py', 'w') as f:
    f.write(content)

print('Updated __all__ exports')
