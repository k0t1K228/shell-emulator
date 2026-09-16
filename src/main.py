"""Эмулятор командный строки с конфигурацией и VFS, 4 этап."""

import getpass
import os
import socket
import sys
import base64
import xml.etree.ElementTree as ET
import datetime

def get_promt(cwd):
    """Возвращение строки приглашения"""
    user = getpass.getuser()
    host = socket.gethostname()
    return user + "@" + host + ":" + format_path(cwd) + "$ "

def parse_command(line):
    """Раскрытие переменных окружения и разбивает строку на слова."""
    line = os.path.expandvars(line)
    parts = line.split()
    if len(parts) == 0:
        return None, []
    command = parts[0]
    args = parts[1:]
    return command, args

def execute(command, args, vfs_root, cwd):
    """Выполняет одну команду. Возвращает ложь, если необходимо выйти."""
    if command is None:
        return True, False
    if command == "exit":
        return False, False
    if command == "ls":
        return True, command_ls(vfs_root, cwd, args)
    if command == "cd":
        return True, command_cd(vfs_root, cwd, args)
    if command == "clear":
        return True, command_clear()
    if command == "date":
        return True, command_date()
    if command == "tac":
        return True, command_tac(vfs_root, cwd, args)
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

def apply_path_parts(segments, path):
    """Применяет к списку сегментов части пути."""
    for part in path.split("/"):
        if part == "" or part == ".":
            continue
        if part == "..":
            if segments:
                segments.pop()
        else:
            segments.append(part)
    return segments

def normalize_path(cwd, path):
    """Вычисляет список сегментов пути с учётом текущей директории."""
    if path is None or path == "":
        segments = list(cwd)
    elif path.startswith("/"):
        segments = apply_path_parts([], path)
    else:
        segments = apply_path_parts(list(cwd), path)
    return segments

def get_node(vfs_root, segments):
    """Находит узел VFS по списку сегментов пути."""
    if vfs_root is None:
        return None
    node = vfs_root
    for part in segments:
        if node["type"] != "dir":
            return None
        if part not in node["children"]:
            return None
        node = node["children"][part]
    return node

def format_path(segments):
    """Превращает список сегментов обратно в строку пути вида /a/b/c."""
    if len(segments) == 0:
        return "/"
    return "/" + "/".join(segments)

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

def command_ls(vfs_root, cwd, args):
    """Выводит содержимое директории VFS."""
    if vfs_root is None:
        print("ls: VFS не подключена")
        return True

    path = args[0] if len(args) > 0 else None
    segments = normalize_path(cwd, path)
    node = get_node(vfs_root, segments)
    if node is None:
        print("ls: путь не найден:", format_path(segments))
        return True
    if node["type"] == "file":
        print(node["name"])
        return False
    for name in sorted(node["children"].keys()):
        child = node["children"][name]
        suffix = "/" if child["type"] == "dir" else ""
        print(name + suffix)
    return False

def command_cd(vfs_root, cwd, args):
    """Меняет текущую директорию VFS."""
    if vfs_root is None:
        print("cd: VFS не подключена")
        return True

    path = args[0] if len(args) > 0 else "/"
    segments = normalize_path(cwd, path)
    node = get_node(vfs_root, segments)
    if node is None:
        print("cd: путь не найден:", format_path(segments))
        return True

    if node["type"] != "dir":
        print("cd: не является директорией:", format_path(segments))
        return True

    cwd.clear()
    cwd.extend(segments)
    return False

def command_clear():
    """Очищает экран терминала."""
    print("\033[H\033[J", end="")
    return False

def command_date():
    """Печатает текущую дату и время реальной OC."""
    now = datetime.datetime.now()
    print(now.strftime("%Y-%m-%d %H:%M:%S"))
    return False

def command_tac(vfs_root, cwd, args):
    """Печатает содержимое файла VFS построчно в обратном порядке."""
    if vfs_root is None:
        print("tac: VFS не подключена")
        return True

    if len(args) == 0:
        print("tac: не указан файл")
        return True

    path = args[0]
    segments = normalize_path(cwd, path)
    node = get_node(vfs_root, segments)
    if node is None:
        print("tac: файл не найден:", format_path(segments))
        return True
    if node["type"] != "file":
        print("tac: не является файлом:", format_path(segments))
        return True

    text = node["content"].decode("utf-8", errors="replace")
    lines = text.splitlines()
    for line in reversed(lines):
        print(line)
    return False

def run_script(script_path, vfs_root, cwd):
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

            print(get_promt(cwd) + line)
            command, args = parse_command(line)
            should_continue, error_occured = execute(command, args, vfs_root, cwd)

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
    vfs_root = load_vfs_or_report_error(vfs_path)
    cwd = []

    if script_path is not None:
        run_script(script_path, vfs_root, cwd)
        return
        
    while True:
        line = input(get_promt(cwd))
        command, args = parse_command(line)
        should_continue, error_occurred = execute(command, args, vfs_root, cwd)
        if not should_continue:
            break

if __name__ == "__main__":
    main()
