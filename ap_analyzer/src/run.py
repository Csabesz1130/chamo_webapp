import os
import sys

import time

# Check all modified files
files_to_check = [
    "src/utils/point_counter.py",
    "src/gui/app.py",
    "src/gui/action_potential_tab.py"
]

print("\nFILE MODIFICATION TIMESTAMPS:")
for file_path in files_to_check:
    try:
        mod_time = time.ctime(os.path.getmtime(file_path))
        print(f"{file_path} last modified: {mod_time}")
    except Exception as e:
        print(f"Error checking {file_path}: {e}")
print()

# Add src to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.append(current_dir)

from src.main import main

if __name__ == "__main__":
    main()