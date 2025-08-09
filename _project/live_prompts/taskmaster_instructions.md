# Task Master CLI Instructions

## Setup Commands

```bash
# Initialize new project
tm init [--name=<name>] [--description=<desc>] [-y]

# Configure AI models
tm models --setup
tm models --set-main <model_id>
tm models --set-research <model_id>
tm models --set-fallback <model_id>

# Generate tasks from PRD
tm parse-prd --input=<file.txt> [--num-tasks=10]
tm generate
```

## Core Task Management

```bash
# View tasks
tm list [--status=<status>] [--with-subtasks]
tm show <id>
tm next

# Update task status
tm set-status --id=<id> --status=<status>
# Status options: pending, done, in-progress, review, deferred, cancelled

# Modify tasks
tm add-task --prompt="<text>" [--dependencies=<ids>] [--priority=<priority>]
tm update-task --id=<id> --prompt="<context>"
tm update --from=<id> --prompt="<context>"
tm remove-task --id=<id> [-y]
```

## Subtask Operations

```bash
# Add subtasks
tm add-subtask --parent=<id> --title="<title>" [--description="<desc>"]
tm add-subtask --parent=<id> --task-id=<id>  # Convert existing task

# Manage subtasks
tm update-subtask --id=<parentId.subtaskId> --prompt="<context>"
tm remove-subtask --id=<parentId.subtaskId> [--convert]
tm clear-subtasks --id=<id>
tm clear-subtasks --all
```

## Task Analysis & Expansion

```bash
# Analyze complexity
tm analyze-complexity [--research] [--threshold=5]
tm complexity-report [--file=<path>]

# Expand tasks
tm expand --id=<id> [--num=5] [--research] [--prompt="<context>"]
tm expand --all [--force] [--research]

# Research
tm research "<prompt>" [-i=<task_ids>] [-f=<file_paths>] [-c="<context>"] [--tree] [-s=<save_file>] [-d=<detail_level>]
```

## Dependencies

```bash
# Manage dependencies
tm add-dependency --id=<id> --depends-on=<id>
tm remove-dependency --id=<id> --depends-on=<id>
tm validate-dependencies
tm fix-dependencies
```

## Tag Management

```bash
# View and switch tags
tm tags [--show-metadata]
tm use-tag <tagName>

# Create and modify tags
tm add-tag <tagName> [--copy-from-current] [--copy-from=<tag>] [-d="<desc>"]
tm rename-tag <oldName> <newName>
tm copy-tag <sourceName> <targetName> [-d="<desc>"]
tm delete-tag <tagName> [--yes]
```

## Export & Sync

```bash
# Export to README
tm sync-readme [--with-subtasks] [--status=<status>]
```

## Essential Workflow

1. **Setup**: `tm init` → `tm models --setup`
2. **Generate**: `tm parse-prd --input=<file>`
3. **Work**: `tm next` → `tm show <id>` → `tm set-status --id=<id> --status=in-progress`
4. **Complete**: `tm set-status --id=<id> --status=done`
5. **Validate**: `tm validate-dependencies` → `tm list --status=pending`

## Configuration Files

- `.taskmaster/config.json` - AI model settings
- `.env` - API keys (ANTHROPIC_API_KEY, etc.)
- `.cursor/mcp.json` - Cursor integration keys