#!/usr/bin/env bash
python3 "$(dirname "$0")/../src/main.py" --vfs "$(dirname "$0")/../vfs/example.xml" --script "$(dirname "$0")/demo.txt"
