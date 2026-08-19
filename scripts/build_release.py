import os
import json
import re
import subprocess
from datetime import datetime

def has_untracked_or_modified_changes(filepath):
    """
    Checks if a file has modified or untracked changes in git.
    Returns True if it has changes, False if it is clean.
    """
    try:
        status = subprocess.run(
            ['git', 'status', '--porcelain', filepath],
            capture_output=True, text=True, check=True
        )
        # If there is any output, the file is modified or untracked
        return bool(status.stdout.strip())
    except subprocess.CalledProcessError:
        # If git fails, fail gracefully and assume it's modified
        return True

def parse_version_info(first_line):
    """
    Extracts the version from the first line and determines its type.
    """
    version = first_line.strip().split()[-1]
    
    if re.match(r'^\d{2}\.\d{2}\.\d{2}$', version):
        version_type = "calver"
    else:
        version_type = "semver"
        
    return version, version_type

def main():
    releases_dir = 'releases'
    output_file = 'releases.json'
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 1. Try to load existing JSON
    existing_data = {}
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: {output_file} is corrupt. Starting fresh.")
    
    file_map = {
        'squigit-app.md': 'app',
        'squigit-cli.md': 'cli',
        'squigit-ocr.md': 'ocr'
    }
    
    output_data = {}
    
    for filename, json_key in file_map.items():
        filepath = os.path.join(releases_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"Warning: File not found -> {filepath}")
            continue
            
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
            
        lines = content.splitlines()
        if not lines:
            continue
            
        version, version_type = parse_version_info(lines[0])
        
        # 2. Date Logic: Apply your exact rules
        if not existing_data or json_key not in existing_data:
            # Not found in JSON -> Today
            released_at = today
        else:
            # Found in JSON -> Check if tracked/untracked
            if has_untracked_or_modified_changes(filepath):
                # Untracked/Modified -> Today
                released_at = today
            else:
                # Tracked and clean -> Keep existing date from JSON
                released_at = existing_data[json_key].get("released_at", today)
        
        output_data[json_key] = {
            "current_version": None,
            "latest_version": version,
            "version_type": version_type,
            "released_at": released_at,
            "content": content
        }
        
    # Write the payload
    with open(output_file, 'w', encoding='utf-8') as out_file:
        json.dump(output_data, out_file, indent=2)
        out_file.write('\n')
        
    print(f"Successfully generated {output_file}")

if __name__ == "__main__":
    main()
