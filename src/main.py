"""Эмулятор командный строки  с конфигурацией и VFS, 3 этап."""

import getpass
import os
import socket
import sys
import base64
import xml.etree.ElementTree as ET

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

def build_node(element):
    """Строит один узел дерева VFS (файл или папку) из XML-элемента."""
    name = element.get("name")
    if element.tag == "directory":
        children = {}
        for child_element in element:
            child_node = build_node(child_element)
            children[child_node["name"]] = child_node
        return {"type": "dir", "name": name, "children": children}
    if element.tag == "file":
        text = element.text or ""
        content = base64.b64decode(text.strip())
        return {"type": "file", "name": name, "content": content}
    raise ValueError("Неизвестный тег в VFS: " + element.tag)

def load_vfs(path):
    """Загружает VFS из XML-файла и строит дерево в памяти.
    Отбрасывает исключение, если файл не найден или XML некорректен,
    то вызывающий код сам решает, как сообщить об ошибке."""
    tree = ET.parse(path)
    root_element = tree.getroot()
    children = {}
    for child_element in root_element:
        child_node = build_node(child_element)
        children[child_node["name"]] = child_node
    return {"type": "dir", "name": "/", "children": children}

def count_files(node):
    """Считает количество файлов в дереве VFS."""
    if node["type"] == "file":
        return 1
    total = 0
    for child in node["children"].values():
        total += count_files(child)
    return total

def load_vfs_or_report_error(vfs_path):
    """Попытка загрузки VFS и вывод успеха или ошибки."""
    if vfs_path is None:
        return None

    try:
        vfs_root = load_vfs(vfs_path)
    except FileNotFoundError:
        print("Ошибка загрузки VFS: файл не найден:", vfs_path)
        return None
    except ET.ParseError as error:
        print("Ошибка загрузки VFS: неверный формат XML:", error)
        return None

    print("VFS успешно загружена. Файлов в VFS:", count_files(vfs_root))
    return vfs_root
    
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
    """Основной цикл. Разбирает аргументы, загружает VFS, выводит отладочную информацию
    и запускает либо стартовый скрипт, либо REPL."""
    vfs_path, script_path = parse_args(sys.argv[1:])
    print_debug_info(vfs_path, script_path)
    load_vfs_or_report_error(vfs_path)

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
