#!/usr/bin/env python3
"""
Enhanced Code Spider Script
Recursively extracts all code files from any project into a single markdown document.
Focuses on actual source code while excluding libraries and dependencies.
"""

import os
import sys
from datetime import datetime


class CodeSpider:
    def __init__(self, root_dir=None):
        """Initialize with target directory (current directory if None)."""
        if root_dir:
            self.root_dir = os.path.abspath(root_dir)
        else:
            self.root_dir = os.getcwd()

        if not os.path.exists(self.root_dir):
            raise ValueError(f"Target directory does not exist: {self.root_dir}")

    def should_ignore_directory(self, dir_path):
        """Check if directory should be ignored (libraries, dependencies, etc)."""
        ignore_dirs = {
            # Python
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".tox",
            "dist",
            "build",
            ".egg-info",
            "venv",
            ".venv",
            "env",
            ".env",
            "site-packages",
            # Node.js/JavaScript
            "node_modules",
            ".next",
            ".nuxt",
            "coverage",
            ".nyc_output",
            "bower_components",
            # Version control
            ".git",
            ".svn",
            ".hg",
            # IDEs
            ".vscode",
            ".idea",
            "__MACOSX",
            # Build/temp
            "tmp",
            "temp",
            ".tmp",
            ".cache",
            # Logs
            "logs",
            "log",
            # Testing
            ".coverage",
            "htmlcov",
            # Documentation builds
            "_build",
            "docs/_build",
            ".sphinx-build",
        }

        dir_name = os.path.basename(dir_path)

        # Check exact matches
        if dir_name in ignore_dirs:
            return True

        # Check patterns
        if (
            (dir_name.startswith(".") and dir_name not in {".github", ".vscode"})
            or dir_name.endswith(".egg-info")
            or "cache" in dir_name.lower()
            or "backup" in dir_name.lower()
            or "__pycache__" in dir_name
        ):
            return True

        return False

    def should_ignore_file(self, file_path):
        """Check if file should be ignored."""
        filename = os.path.basename(file_path)

        # Ignore hidden files (except some exceptions)
        if filename.startswith(".") and filename not in {
            ".gitignore",
            ".env.example",
            ".eslintrc.js",
            ".babelrc",
            ".prettierrc",
            ".editorconfig",
        }:
            return True

        # Ignore common non-code files
        ignore_extensions = {
            ".pyc",
            ".pyo",
            ".pyd",
            ".so",
            ".dll",
            ".dylib",
            ".log",
            ".tmp",
            ".temp",
            ".bak",
            ".backup",
            ".exe",
            ".msi",
            ".dmg",
            ".deb",
            ".rpm",
            ".zip",
            ".tar",
            ".gz",
            ".rar",
            ".7z",
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".svg",
            ".ico",
            ".mp3",
            ".mp4",
            ".avi",
            ".mov",
            ".wav",
            ".woff",
            ".woff2",
            ".ttf",
            ".eot",
        }

        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext in ignore_extensions:
            return True

        # Ignore specific files
        ignore_files = {
            "package-lock.json",
            "yarn.lock",
            "poetry.lock",
            "Pipfile.lock",
            ".DS_Store",
            "Thumbs.db",
            "desktop.ini",
            "node_modules",
            ".coverage",
        }

        if filename in ignore_files:
            return True

        return False

    def is_code_file(self, filepath):
        """Check if file is a code file that should be included."""
        code_extensions = {
            # Python
            ".py",
            ".pyx",
            ".pyi",
            # JavaScript/TypeScript
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
            ".mjs",
            ".cjs",
            # Web frontend
            ".html",
            ".htm",
            ".css",
            ".scss",
            ".sass",
            ".less",
            ".vue",
            ".svelte",
            ".astro",
            # Config files (often code-like)
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".ini",
            ".cfg",
            ".xml",
            ".config",
            # Shell scripts
            ".sh",
            ".bash",
            ".zsh",
            ".fish",
            ".ps1",
            ".bat",
            ".cmd",
            # Other common languages
            ".java",
            ".kt",
            ".scala",
            ".go",
            ".rs",
            ".c",
            ".cpp",
            ".cc",
            ".cxx",
            ".h",
            ".hpp",
            ".cs",
            ".php",
            ".rb",
            ".swift",
            ".m",
            ".mm",
            ".sql",
            ".r",
            ".R",
            ".matlab",
            # Markup/Documentation as code
            ".md",
            ".rst",
            ".txt",
            # Build files
            ".dockerfile",
            ".containerfile",
            # Data formats that might contain code
            ".graphql",
            ".proto",
            # Template files
            ".jinja",
            ".j2",
            ".handlebars",
            ".mustache",
        }

        file_ext = os.path.splitext(filepath)[1].lower()
        filename = os.path.basename(filepath).lower()

        # Check extension
        if file_ext in code_extensions:
            return True

        # Check special filenames (no extension)
        special_files = {
            "makefile",
            "dockerfile",
            "containerfile",
            "vagrantfile",
            "rakefile",
            "gruntfile.js",
            "gulpfile.js",
            "webpack.config.js",
            "rollup.config.js",
            "vite.config.js",
            "package.json",
            "composer.json",
            "requirements.txt",
            "setup.py",
            "setup.cfg",
            "pyproject.toml",
            "poetry.toml",
            "__init__.py",
            "conftest.py",
            ".gitignore",
            ".dockerignore",
            ".eslintrc.js",
            ".babelrc",
            ".prettierrc",
            ".editorconfig",
        }

        if filename in special_files:
            return True

        return False

    def get_target_files(self):
        """Get all target code files recursively."""
        target_files = []

        for root, dirs, files in os.walk(self.root_dir):
            # Remove ignored directories from dirs list to prevent os.walk from entering them
            dirs[:] = [d for d in dirs if not self.should_ignore_directory(os.path.join(root, d))]

            for file in files:
                file_path = os.path.join(root, file)

                # Skip ignored files
                if self.should_ignore_file(file_path):
                    continue

                # Include only code files
                if self.is_code_file(file_path):
                    target_files.append(file_path)

        return sorted(target_files)

    def read_file_content(self, file_path):
        """Read file content with robust error handling."""
        try:
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                # Try with different encoding
                with open(file_path, encoding="latin-1") as f:
                    return f.read()
            except FileNotFoundError:
                return f"Error: File not found: {file_path}"
            except PermissionError:
                return f"Error: Permission denied: {file_path}"
            except OSError as e:
                return f"Error reading file with latin-1 encoding: {e}"
        except FileNotFoundError:
            return f"Error: File not found: {file_path}"
        except PermissionError:
            return f"Error: Permission denied: {file_path}"
        except OSError as e:
            return f"Error reading file: {e}"

    def get_file_language(self, file_path):
        """Determine the language for markdown code blocks."""
        ext = os.path.splitext(file_path)[1].lower()
        filename = os.path.basename(file_path).lower()

        language_map = {
            ".py": "python",
            ".pyx": "python",
            ".pyi": "python",
            ".js": "javascript",
            ".jsx": "jsx",
            ".ts": "typescript",
            ".tsx": "tsx",
            ".mjs": "javascript",
            ".cjs": "javascript",
            ".html": "html",
            ".htm": "html",
            ".css": "css",
            ".scss": "scss",
            ".sass": "sass",
            ".less": "less",
            ".vue": "vue",
            ".svelte": "svelte",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".xml": "xml",
            ".sh": "bash",
            ".bash": "bash",
            ".zsh": "zsh",
            ".fish": "fish",
            ".ps1": "powershell",
            ".bat": "batch",
            ".cmd": "batch",
            ".java": "java",
            ".kt": "kotlin",
            ".scala": "scala",
            ".go": "go",
            ".rs": "rust",
            ".c": "c",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".h": "c",
            ".hpp": "cpp",
            ".cs": "csharp",
            ".php": "php",
            ".rb": "ruby",
            ".swift": "swift",
            ".m": "objective-c",
            ".mm": "objective-c",
            ".sql": "sql",
            ".r": "r",
            ".R": "r",
            ".md": "markdown",
            ".rst": "rst",
            ".txt": "text",
            ".ini": "ini",
            ".cfg": "ini",
            ".config": "xml",
            ".graphql": "graphql",
            ".proto": "protobuf",
        }

        # Check filename-based languages
        if filename in ["dockerfile", "containerfile"] or "dockerfile" in filename:
            return "dockerfile"
        elif filename == "makefile" or filename.endswith("makefile"):
            return "makefile"
        elif filename == "vagrantfile":
            return "ruby"
        elif filename in ["package.json", "composer.json"]:
            return "json"
        elif filename in [".gitignore", ".dockerignore"]:
            return "gitignore"
        elif filename in [
            ".eslintrc.js",
            "webpack.config.js",
            "rollup.config.js",
            "vite.config.js",
        ]:
            return "javascript"
        elif filename == "__init__.py":
            return "python"

        return language_map.get(ext, "text")

    def get_relative_path(self, file_path):
        """Get relative path from project root."""
        try:
            return os.path.relpath(file_path, self.root_dir)
        except ValueError:
            # Fallback if paths are on different drives (Windows)
            return file_path

    def create_codebase_markdown(self, output_file=None):
        """Create the consolidated codebase markdown file."""
        target_files = self.get_target_files()

        if not target_files:
            print("No code files found in the specified directory.")
            return

        # Generate output filename if not provided
        if output_file is None:
            project_name = os.path.basename(self.root_dir)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"codebase_{project_name}_{timestamp}.md"

        # Always save in current working directory
        output_path = os.path.join(os.getcwd(), output_file)

        print(f"Processing {len(target_files)} files...")
        print(f"Output will be saved to: {output_path}")

        with open(output_path, "w", encoding="utf-8") as out_file:
            project_name = os.path.basename(self.root_dir)

            # Write header
            out_file.write(f"# Codebase Documentation: {project_name}\n\n")
            out_file.write(f"**Source Directory:** `{os.path.abspath(self.root_dir)}`  \n")
            out_file.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
            out_file.write(f"**Total Files:** {len(target_files)}\n\n")

            # Write table of contents
            out_file.write("## Table of Contents\n\n")
            for i, file_path in enumerate(target_files, 1):
                rel_path = self.get_relative_path(file_path)
                anchor = rel_path.replace("/", "").replace(".", "").replace(" ", "-").lower()
                out_file.write(f"{i}. [{rel_path}](#{anchor})\n")
            out_file.write("\n---\n\n")

            # Write file contents
            for i, file_path in enumerate(target_files, 1):
                rel_path = self.get_relative_path(file_path)

                # Progress indicator
                if i % 10 == 0:
                    print(f"Processed {i}/{len(target_files)} files...")

                # File header
                out_file.write(f"## {i}. {rel_path}\n\n")
                out_file.write(f"**Full Path:** `{os.path.abspath(file_path)}`\n\n")

                # Read and write file content
                content = self.read_file_content(file_path)
                language = self.get_file_language(file_path)

                out_file.write(f"```{language}\n")
                out_file.write(content)
                if not content.endswith("\n"):
                    out_file.write("\n")
                out_file.write("```\n\n")
                out_file.write("---\n\n")

        print(f"Codebase documentation saved to: {output_path}")
        return output_path


def main():
    """Main function with command line argument support."""
    try:
        # Parse command line arguments
        if len(sys.argv) > 3:
            print("Usage: python code_spider.py [target_directory] [output_filename]")
            print("  target_directory: Directory to analyze (default: current directory)")
            print("  output_filename: Output markdown filename (default: auto-generated)")
            sys.exit(1)

        target_dir = sys.argv[1] if len(sys.argv) > 1 else None
        output_file = sys.argv[2] if len(sys.argv) > 2 else None

        # Validate target directory
        if target_dir and not os.path.exists(target_dir):
            print(f"Error: Directory '{target_dir}' does not exist.")
            sys.exit(1)

        # Create spider and process
        spider = CodeSpider(target_dir)
        print(f"Analyzing codebase in: {spider.root_dir}")

        spider.create_codebase_markdown(output_file)
        print("Analysis complete!")

    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
