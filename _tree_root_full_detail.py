import ast
import logging
import os

from treelib import Tree

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class ProjectAnalyzer:
    def __init__(self) -> None:
        # Set project_root to the parent directory of this script's location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = script_dir
        logging.info(f"Project root set to: {self.project_root}")
        self.tree = Tree()
        self.tree.create_node("Project Root/", "Project Root")  # Append / to indicate directory

    def parse_python_file(self, filepath, parent_id) -> None:
        """Parse Python file to extract classes, methods, functions."""
        try:
            with open(filepath) as file:
                node = ast.parse(file.read(), filename=filepath)
                for elem in node.body:
                    if isinstance(elem, ast.ClassDef):
                        class_id = f"{parent_id}-{elem.name}"
                        self.tree.create_node(f"Class: {elem.name}", class_id, parent=parent_id)
                        for method in [n for n in elem.body if isinstance(n, ast.FunctionDef)]:
                            method_id = f"{class_id}-{method.name}"
                            self.tree.create_node(
                                f"Method: {method.name}", method_id, parent=class_id
                            )
                    elif isinstance(elem, ast.FunctionDef):
                        func_id = f"{parent_id}-{elem.name}"
                        self.tree.create_node(f"Function: {elem.name}", func_id, parent=parent_id)
        except Exception as e:
            logging.exception(f"Failed to parse {filepath}: {e}")

    def analyze_project(self) -> None:
        """Traverse and parse project files."""
        for root, dirs, files in os.walk(self.project_root, topdown=True):
            # Ignore __pycache__ directories
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            # Ignore directories starting with '.' or '_' and any 'backup' directories
            dirs[:] = [
                d for d in dirs if not d.startswith(".") and not d.startswith("_") and d != "backup"
            ]
            # Ignore files starting with '.' or '_'
            files = [f for f in files if not f.startswith(".") and not f.startswith("_")]

            relative_root_path = os.path.relpath(root, self.project_root)
            parent_id = (
                "Project Root"
                if relative_root_path == "."
                else os.path.join("Project Root", relative_root_path.replace(os.sep, "/"))
            )

            if relative_root_path != ".":
                directory_tag = os.path.basename(root) + "/"
                self.tree.create_node(
                    tag=directory_tag,
                    identifier=parent_id,
                    parent=os.path.dirname(parent_id) or "Project Root",
                )

            for name in files:
                if name.endswith(".py"):
                    filepath = os.path.join(root, name)
                    file_id = os.path.join(parent_id, name)
                    self.tree.create_node(tag=name, identifier=file_id, parent=parent_id)
                    self.parse_python_file(filepath, file_id)
                elif name.endswith((".yaml", ".yml")):
                    filepath = os.path.join(root, name)
                    file_id = os.path.join(parent_id, name)
                    self.tree.create_node(tag=f"📄 {name}", identifier=file_id, parent=parent_id)

    def generate_reports(self) -> None:
        """Generate and save project analysis reports."""
        report_content = "PROJECT STRUCTURE REPORT\n\n"
        report_content += self.tree.show(line_type="ascii-em", stdout=False)
        self.save_report(report_content, "_tree_diagram_full_detail.txt")

    def save_report(self, report_content, filename) -> None:
        """Save report to a file."""
        try:
            filepath = os.path.join(self.project_root, filename)
            with open(filepath, "w") as file:
                file.write(report_content)
            logging.info(f"Report saved to {filepath}")
        except Exception as e:
            logging.exception(f"Failed to save report: {e}")


def main() -> None:
    try:
        analyzer = ProjectAnalyzer()
        analyzer.analyze_project()
        analyzer.generate_reports()
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
