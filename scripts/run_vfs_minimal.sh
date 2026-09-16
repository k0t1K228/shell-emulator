#!/usr/bin/env bash
python3 "$(dirname "$0")/../src/main.py" --vfs "$(dirname "$0")/../vfs/minimal.xml" --script "$(dirname "$0")/demo.txt"
