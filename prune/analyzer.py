"""Analyzer for Python imports."""

import ast
import os
import sys
from pathlib import Path
from typing import Set, List


class ImportVisitor(ast.NodeVisitor):
    """AST visitor to extract import statements from Python files."""
    
    def __init__(self):
        self.imports: Set[str] = set()
    
    def visit_Import(self, node):
        """Handle 'import module' statements."""
        for alias in node.names:
            # Get the top-level module name
            module_name = alias.name.split('.')[0]
            self.imports.add(module_name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Handle 'from module import ...' statements."""
        if node.module:
            # Get the top-level module name
            module_name = node.module.split('.')[0]
            self.imports.add(module_name)
        self.generic_visit(node)


def extract_imports_from_file(filepath: Path) -> Set[str]:
    """
    Extract all import statements from a Python file.
    
    Args:
        filepath: Path to Python file
        
    Returns:
        Set of imported module names
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(filepath))
        visitor = ImportVisitor()
        visitor.visit(tree)
        return visitor.imports
    except SyntaxError as e:
        print(f"⚠️  Syntax error in {filepath}: {e}", file=sys.stderr)
        return set()
    except Exception as e:
        print(f"⚠️  Error reading {filepath}: {e}", file=sys.stderr)
        return set()


def find_python_files(path: Path) -> List[Path]:
    """
    Recursively find all Python files in the given path.
    
    Args:
        path: Root path to search
        
    Returns:
        List of Python file paths
    """
    python_files = []
    
    for root, dirs, files in os.walk(path):
        # Skip common directories that shouldn't be scanned
        dirs[:] = [d for d in dirs if d not in {
            '__pycache__', '.git', '.venv', 'venv', 'env', 
            'node_modules', '.tox', 'build', 'dist', '.eggs'
        }]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    return python_files
