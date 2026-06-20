import os
import ast
import warnings

# Suppress regex warnings from other libraries
warnings.filterwarnings("ignore", category=SyntaxWarning)

def extract_functions(file_path):
    functions = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                params = [arg.arg for arg in node.args.args]
                params_str = ', '.join(params) if params else ''
                func = f"{node.name}({params_str})"
                functions.append(func)
    except:
        pass
    return functions

def main():
    target_folder = "backend"   # ← Only this folder
    
    print(f"Python Functions in '{target_folder}' folder")
    print("=" * 65)
    
    for root, dirs, files in os.walk(target_folder):
        # Skip unwanted subfolders
        dirs[:] = [d for d in dirs if d not in [
            '__pycache__', 'venv', 'env', '.git', 'node_modules', 
            'chroma_db', 'dist', 'build', '.pytest_cache'
        ]]
        
        for file in sorted([f for f in files if f.endswith('.py')]):
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, target_folder)
            
            functions = extract_functions(filepath)
            
            print(f"\n{file}")
            print("-" * (len(file) + 6))
            
            if functions:
                for func in functions:
                    print(f"• {func}")
            else:
                print("  (No functions found)")
            print()

if __name__ == "__main__":
    main()