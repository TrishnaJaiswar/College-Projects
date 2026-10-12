import zipfile
import os

zipf = zipfile.ZipFile('code_only.zip', 'w')

EXCLUDE_DIRS = {'venv', 'models', 'data', 'logs', '__pycache__', '.git', '.cache', 'temp_convert_venv3'}

for root, dirs, files in os.walk('.'):
    # 🔥 Skip heavy folders
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

    for file in files:
        if file.endswith(('.py', '.txt', '.md', '.json')):
            filepath = os.path.join(root, file)
            zipf.write(filepath, os.path.relpath(filepath, '.'))

zipf.close()

print("✅ Zip created fast!")