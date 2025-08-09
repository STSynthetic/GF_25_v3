You are an AI coder. Execute these EXACT commands in sequence:

## MANDATORY COMMAND SEQUENCE

### 1. GET WORK
```bash
tm next
```
If nothing shown, check:
```bash
tm list --status=pending
tm list --status=in-progress
```
**CRITICAL: Always continue in-progress tasks before starting new ones.**

### 2. EXAMINE TASK  
```bash
tm show <taskId>
```
**For in-progress tasks:**
1. **Check existing codebase** to see what's already implemented
2. **Compare against task requirements** to identify remaining work
3. **Continue from where previous work left off**

**Identify work item from output:**
- Has subtasks → find next incomplete subtask (check codebase vs requirements)
- No subtasks → continue remaining parts of main task

### 3. SET TASK STATUS
**Only if task is NOT already in-progress:**
```bash
tm set-status --id=<taskId> --status=in-progress
```
**If already in-progress: Skip this step - you're continuing existing work**

### 4. IMPLEMENT WORK ITEM
**Code the work item completely, then run:**

```bash
# Quality checks
ruff check --fix .
ruff format .

# Test everything  
pytest tests/

# Commit and push
git add .
git commit -m "feat: [Task <taskId>] <work item description>"
git push
```

### 5. MARK COMPLETE
**Subtask completed (no command needed - just move to next subtask)**
Check for more subtasks:
```bash
tm show <taskId>
```

**All subtasks done OR main task without subtasks completed:**
```bash
tm set-status --id=<taskId> --status=done
```

### 6. REPEAT
Go to step 1

## ESSENTIAL COMMANDS

**Complex task:**
```bash
tm expand --id=<taskId> --num=5
```

**Blocked task:**
```bash
tm set-status --id=<taskId> --status=deferred
```

**Check progress:**
```bash
tm list --status=pending
tm list --with-subtasks
```

**Every 10 tasks:**
```bash
tm validate-dependencies
```

## ABSOLUTE RULES
- **ALWAYS continue in-progress tasks before starting new ones**
- **Check codebase state before continuing in-progress work**
- ONE work item at a time
- UV only: `uv install <package>`
- Always run: `ruff check --fix . && ruff format .`
- Always test before push
- Always push after work item complete: `git push`
- Use exact commands shown above
- **DO NOT restart or duplicate existing work**

**Complete when:** `tm list --status=pending` shows nothing