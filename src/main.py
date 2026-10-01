"""Эмулятор командной строки: REPL, VFS, команды (Этапы 1-5)."""

import base64
import datetime
import getpass
import os
import socket
import sys
import xml.etree.ElementTree as element_tree

MODE_LENGTH = 3
CHMOD_MIN_ARGS = 2

def parse_command(line):
    """Раскрывает переменные окружения, разбивает строку на слова."""
    line = os.path.expandvars(line)
    parts = line.split()
    if len(parts) == 0:
        return None, []
    command = parts[0]
    args = parts[1:]
    return command, args

def parse_args(argv):
    """Разбирает аргументы командной строки: --vfs и --script."""
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
    """Печатает параметры запуска (отладочный вывод)."""
    print("Отладочная информация:")
    print("  Путь к VFS:", vfs_path)
    print("  Путь к стартовому скрипту:", script_path)

def apply_path_parts(segments, path):
    """Применяет к сегментам части пути (учитывает '.' и '..')."""
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
    """Строит список сегментов пути с учётом текущей директории."""
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
    """Превращает сегменты обратно в строку пути вида /a/b/c."""
    if len(segments) == 0:
        return "/"
    return "/" + "/".join(segments)

def get_prompt(cwd):
    """Возвращает строку приглашения вида user@host:путь$."""
    user = getpass.getuser()
    host = socket.gethostname()
    return user + "@" + host + ":" + format_path(cwd) + "$ "

def is_valid_mode(mode):
    """Проверяет, что режим доступа - три восьмеричные цифры."""
    if len(mode) != MODE_LENGTH:
        return False
    for digit in mode:
        if digit not in "01234567":
            return False
    return True

def build_node(element):
    """Строит один узел дерева VFS из XML-элемента."""
    name = element.get("name")

    if element.tag == "directory":
        children = {}
        for child_element in element:
            child_node = build_node(child_element)
            children[child_node["name"]] = child_node
        return {
            "type": "dir",
            "name": name,
            "children": children,
            "mode": "755",
        }

    if element.tag == "file":
        text = element.text or ""
        content = base64.b64decode(text.strip())
        return {
            "type": "file",
            "name": name,
            "content": content,
            "mode": "644",
        }

    raise ValueError("Неизвестный тег в VFS: " + element.tag)

def load_vfs(path):
    """Загружает VFS из XML-файла и строит дерево в памяти.

    Бросает исключение, если файл не найден или XML некорректен -
    вызывающий код сам решает, как сообщить об ошибке.
    """
    tree = element_tree.parse(path)
    root_element = tree.getroot()

    children = {}
    for child_element in root_element:
        child_node = build_node(child_element)
        children[child_node["name"]] = child_node

    return {"type": "dir", "name": "/",
"children": children, "mode": "755"}

def count_files(node):
    """Считает количество файлов в дереве VFS."""
    if node["type"] == "file":
        return 1
    total = 0
    for child in node["children"].values():
        total += count_files(child)
    return total

def load_vfs_or_report_error(vfs_path):
    """Пытается загрузить VFS, печатает результат: успех или ошибку."""
    if vfs_path is None:
        return None

    try:
        vfs_root = load_vfs(vfs_path)
    except FileNotFoundError:
        print("Ошибка загрузки VFS: файл не найден:", vfs_path)
        return None
    except element_tree.ParseError as error:
        print("Ошибка загрузки VFS: неверный формат XML:", error)
        return None

    file_count = count_files(vfs_root)
    print("VFS успешно загружена. Файлов в VFS:", file_count)
    return vfs_root

def parse_ls_args(args):
    """Извлекает путь и флаг -l из аргументов команды ls."""
    long_format = "-l" in args
    path_args = []
    for arg in args:
        if arg != "-l":
            path_args.append(arg)
    if len(path_args) > 0:
        path = path_args[0]
    else:
        path = None
    return path, long_format

def format_entry(name, mode, is_dir, long_format):
    """Формирует одну строку вывода для ls."""
    suffix = "/" if is_dir else ""
    if long_format:
        return mode + " " + name + suffix
    return name + suffix

def command_ls(vfs_root, cwd, args):
    """Выводит содержимое директории VFS. Флаг -l - режим доступа."""
    if vfs_root is None:
        print("ls: VFS не подключена")
        return True

    path, long_format = parse_ls_args(args)
    segments = normalize_path(cwd, path)
    node = get_node(vfs_root, segments)

    if node is None:
        print("ls: путь не найден:", format_path(segments))
        return True

    if node["type"] == "file":
        entry = format_entry(node["name"], node["mode"], False, long_format)
        print(entry)
        return False

    for name in sorted(node["children"].keys()):
        child = node["children"][name]
        is_dir = child["type"] == "dir"
        print(format_entry(name, child["mode"], is_dir, long_format))
    return False

def command_cd(vfs_root, cwd, args):
    """Меняет текущую директорию VFS. True, если была ошибка."""
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
    """Очищает экран терминала (ANSI-последовательность)."""
    print("\033[H\033[J", end="")
    return False

def command_date():
    """Печатает текущую дату и время реальной ОС."""
    now = datetime.datetime.now()
    print(now.strftime("%Y-%m-%d %H:%M:%S"))
    return False

def command_tac(vfs_root, cwd, args):
    """Печатает содержимое файла VFS построчно, в обратном порядке."""
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

def command_chmod(vfs_root, cwd, args):
    """Изменяет режим доступа узла VFS (только в памяти)."""
    if vfs_root is None:
        print("chmod: VFS не подключена")
        return True

    if len(args) < CHMOD_MIN_ARGS:
        print("chmod: укажите режим и путь, например: chmod 755 docs")
        return True

    mode = args[0]
    path = args[1]

    if not is_valid_mode(mode):
        print("chmod: неверный формат режима:", mode)
        return True

    segments = normalize_path(cwd, path)
    node = get_node(vfs_root, segments)

    if node is None:
        print("chmod: путь не найден:", format_path(segments))
        return True

    node["mode"] = mode
    print("chmod: режим", format_path(segments), "изменён на", mode)
    return False

def command_rmdir(vfs_root, cwd, args):
    """Удаляет пустую директорию из VFS (только в памяти)."""
    if vfs_root is None:
        print("rmdir: VFS не подключена")
        return True

    if len(args) == 0:
        print("rmdir: не указана директория")
        return True

    path = args[0]
    segments = normalize_path(cwd, path)

    if len(segments) == 0:
        print("rmdir: нельзя удалить корневую директорию")
        return True

    parent_segments = segments[:-1]
    target_name = segments[-1]
    parent_node = get_node(vfs_root, parent_segments)

    if parent_node is None or parent_node["type"] != "dir":
        print("rmdir: путь не найден:", format_path(segments))
        return True

    if target_name not in parent_node["children"]:
        print("rmdir: путь не найден:", format_path(segments))
        return True

    target_node = parent_node["children"][target_name]

    if target_node["type"] != "dir":
        print("rmdir: не является директорией:", format_path(segments))
        return True

    if len(target_node["children"]) > 0:
        print("rmdir: директория не пуста:", format_path(segments))
        return True

    del parent_node["children"][target_name]
    print("rmdir: директория удалена:", format_path(segments))
    return False

def execute(command, args, vfs_root, cwd):
    """Выполняет одну команду.

    Возвращает (should_continue, error_occurred).
    """
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

    if command == "chmod":
        return True, command_chmod(vfs_root, cwd, args)

    if command == "rmdir":
        return True, command_rmdir(vfs_root, cwd, args)

    print("Ошибка: неизвестная команда:", command)
    return True, True

def run_script(script_path, vfs_root, cwd):
    """Построчно выполняет команды из стартового скрипта.

    Каждая строка печатается вместе с приглашением, затем
    печатается результат её выполнения. При первой ошибке
    выполнение скрипта останавливается.
    """
    try:
        script_file = open(script_path)
    except OSError as error:
        print("Ошибка запуска скрипта:", error)
        return

    with script_file:
        for line in script_file:
            line = line.strip()
            if line == "":
                continue

            print(get_prompt(cwd) + line)
            command, args = parse_command(line)
            should_continue, error_occurred = execute(
                command, args, vfs_root, cwd
            )

            if error_occurred:
                print("Выполнение скрипта остановлено из-за ошибки.")
                return
            if not should_continue:
                return

def main():
    """Разбирает аргументы, загружает VFS, запускает REPL или скрипт."""
    vfs_path, script_path = parse_args(sys.argv[1:])
    print_debug_info(vfs_path, script_path)
    vfs_root = load_vfs_or_report_error(vfs_path)
    cwd = []

    if script_path is not None:
        run_script(script_path, vfs_root, cwd)
        return

    while True:
        line = input(get_prompt(cwd))
        command, args = parse_command(line)
        should_continue, error_occurred = execute(
            command,
args, vfs_root, cwd
        )
        if not should_continue:
            break

if __name__ == "__main__":
    main()
