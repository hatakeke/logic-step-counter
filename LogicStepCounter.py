import os
import tkinter as tk
from tkinter import ttk
import json
import re

# --------------------------------
# 論理ステップカウント関連関数
# --------------------------------
def is_logical_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    # コメント除去（Python, C/C++, Java, JS, etc）
    if stripped.startswith(('#', '//', '*', '/*', '*/')):
        return False
    # 制御構文・定義文を検出（共通）
    keywords = ['if ', 'for ', 'while ', 'def ', 'function ', 'return ', 'with ',
                'class ', 'switch ', 'case ', 'else', 'try', 'except ', 'catch ', 'fn ']
    if any(stripped.startswith(kw) for kw in keywords):
        return True
    # 代入または関数呼び出しらしき構文
    if '=' in stripped and not stripped.startswith('='):
        return True
    if re.match(r'^\w+\(', stripped):  # 例: func(...)
        return True
    if ';' in stripped:
        return True
    return False


def count_logical_steps_in_file(file_path: str) -> int:
    try:
        if file_path.endswith('.ipynb'):
            with open(file_path, 'r', encoding='utf-8') as f:
                notebook = json.load(f)
            return sum(sum(1 for line in cell.get("source", []) if is_logical_line(line))
                       for cell in notebook.get("cells", [])
                       if cell.get("cell_type") == "code")
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for line in f if is_logical_line(line))
    except:
        return 0

def count_steps_in_folder(folder_path: str) -> int:
    total = 0
    SUPPORTED_EXTENSIONS = (
    '.py', '.ipynb', '.c', '.cpp', '.h', '.hpp',
    '.js', '.ts', '.cs', '.R'
    )
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(SUPPORTED_EXTENSIONS):
                total += count_logical_steps_in_file(os.path.join(root, file))
    return total

# --------------------------------
# GUI関連コード
# --------------------------------
class FolderSelectorApp:
    def __init__(self, root_path):
        self.root = tk.Tk()
        self.root.title("📂 フォルダ選択ツール")
        self.tree = ttk.Treeview(self.root, columns=("fullpath",), show='tree')
        self.tree.pack(fill='both', expand=True)

        self.checked_items = {}
        self.populate_tree('', root_path)

        button = tk.Button(self.root, text="✅ カウント実行", command=self.count_selected_folders)
        button.pack(pady=5)

        self.result_label = tk.Label(self.root, text="")
        self.result_label.pack(pady=5)

        self.root.mainloop()

    def populate_tree(self, parent, path):
        node = self.tree.insert(parent, 'end', text=os.path.basename(path) or path,
                                open=False, values=(path,))
        self.tree.item(node, tags=("unchecked",))
        self.tree.tag_bind("unchecked", "<<TreeviewSelect>>", self.toggle_check)

        self.checked_items[node] = False

        for item in sorted(os.listdir(path)):
            fullpath = os.path.join(path, item)
            if os.path.isdir(fullpath):
                self.populate_tree(node, fullpath)

    def toggle_check(self, event):
        selected = self.tree.selection()
        for node in selected:
            self.checked_items[node] = not self.checked_items.get(node, False)
            text = self.tree.item(node, "text")
            if self.checked_items[node]:
                self.tree.item(node, text=f"✅ {text}")
            else:
                self.tree.item(node, text=text.replace("✅ ", ""))

    def get_selected_paths(self):
        selected = []
        for node, checked in self.checked_items.items():
            if checked:
                path = self.tree.item(node, 'values')[0]
                selected.append(path)
        return selected

    def count_selected_folders(self):
        selected_paths = self.get_selected_paths()
        total = 0
        for path in selected_paths:
            steps = count_steps_in_folder(path)
            print(f"{path}: {steps} steps")
            total += steps
        self.result_label.config(text=f"合計論理ステップ数: {total}")
        print(f"合計論理ステップ数: {total}")

# --------------------------------
# 起動
# --------------------------------
if __name__ == '__main__':
    base_dir = os.getcwd()  # Jupyterでも.pyでも対応
    FolderSelectorApp(base_dir)
