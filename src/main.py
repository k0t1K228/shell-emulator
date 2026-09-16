"""Эмулятор командный строки, 1 этап."""

import getpass
import os
import socket

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
        return True
    if command == "exit":
        return False
    if command == "ls" or command == "cd":
        print(command + ": аргументы:", args)
        return True
    print("Ошибка: неизвестная команда:", command)
    return True

def main():
    """Основной цикл: показывает приглашение и выполняет комманды."""
    while True:
        line = input(get_promt())
        command, args = parse_command(line)
        should_continue = execute(command, args)
        if not should_continue:
            break

if __name__ == "__main__":
    main()
