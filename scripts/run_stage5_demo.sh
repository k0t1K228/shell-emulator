#!/usr/bin/env bash
python3 "$(dirname "$0")/../src/main.py" --vfs "$(dirname "$0")/../vfs/commands_demo.xml" --script "$(dirname "$0")/demo_stage5.txt"
