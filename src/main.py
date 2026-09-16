"""Эмулятор командный строки  с конфигурацией, 2 этап."""

import getpass
import os
import socket
import sys

def get_promt():
    """Возвращение строки приглашения"""
    user = getpass.getuser()
    host = socket.gethostname()
    return user + "@" + host + ":~$ "

def parse_command(line):
    """Раскрытие переменных окружения и разбивает строку на слова."""
    line = os.path.expandvars(line)
    parts = line.split()
    if len(parts) == 0:
        return None, []
    command = parts[0]
    args = parts[1:]
    return command, args

def execute(command, args):
    """Выполняет одну команду. Возвращает ложь, если необходимо выйти."""
    if command is None:
        return True, False
    if command == "exit":
        return False, False
    if command == "ls" or command == "cd":
        print(command + ": аргументы:", args)
        return True, False
    print("Ошибка: неизвестная команда:", command)
    return True, True

def parse_args(argv):
    """Разбирает аргументы командной строки: ---vfs и --script."""
    vfs_path = None
    script_path = None
    i = 0
    while i < len(argv):
        if argv[i] == "--vfs" and i + 1 < len(argv):
            vfs_path = argv[i + 1]
            i += 2
        elif argv[i] == "--script" and i + 1 < len(argv):
            script_path = argv[i + 1]
            i += 2
        else:
            i += 1
    return vfs_path, script_path

def print_debug_info(vfs_path, script_path):
    """Печатает все заданные параметры запуска."""
    print("Отладочная информация:")
    print("  Путь к VFS:", vfs_path)
    print("  Путь к стартовому скрипту:", script_path)

def run_script(script_path):
    """Построчно выполняет из стартового скрипта. 
    Каждая строка печатается вместе с приглашением, а затем печатается результат её выполнения
    При первой ошибке выполнение скрипта останавливается.
    """
    try:
        script_file = open(script_path)
    except OSError as error:
        print("Ошибка запуска скрита:", error)
        return

    with script_file:
        for line in script_file:
            line = line.strip()
            if line == "":
                continue

            print(get_promt() + line)
            command, args = parse_command(line)
            should_continue, error_occured = execute(command, args)

            if error_occured:
                print("Выполнение скрипта остановлено из-за ошибки.")
                return
            if not should_continue:
                return
def main():
    """Основной цикл: показывает приглашение и выполняет комманды."""
    vfs_path, script_path = parse_args(sys.argv[1:])
    print_debug_info(vfs_path, script_path)

    if script_path is not None:
        run_script(script_path)
        return
        
    while True:
        line = input(get_promt())
        command, args = parse_command(line)
        should_continue = execute(command, args)
        if not should_continue:
            break

if __name__ == "__main__":
    main()
