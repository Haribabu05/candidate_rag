import os

IGNORE = {
    "__pycache__",
    ".git",
    "node_modules",
    "venv",
    "paddle_env",
    ".idea",
    ".vscode",
    "build",
    "dist",
    ".pytest_cache"
}

def print_tree(path, prefix=""):
    items = sorted(os.listdir(path))

    items = [i for i in items if i not in IGNORE]

    for index, item in enumerate(items):
        full_path = os.path.join(path, item)
        connector = "└── " if index == len(items) - 1 else "├── "

        print(prefix + connector + item)

        if os.path.isdir(full_path):
            extension = "    " if index == len(items) - 1 else "│   "
            print_tree(full_path, prefix + extension)

if __name__ == "__main__":
    root = os.getcwd()
    print(os.path.basename(root))
    print_tree(root)