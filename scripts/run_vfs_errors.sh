#!/usr/bin/env bash
echo "--- Битый XML ---"
python3 "$(dirname "$0")/../src/main.py" --vfs "$(dirname "$0")/../vfs/broken.xml" --script "$(dirname "$0")/demo.txt"
echo "--- Несуществующий файл  ---"
python3 "$(dirname "$0")/../src/main.py" --vfs "$(dirname "$0")/../vfs/does_not_exits.xml" --script "$(dirname "$0")/demo.txt"
