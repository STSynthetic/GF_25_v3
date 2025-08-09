You are an AI coder working on this project. Follow these instructions exactly and consistently:

## MANDATORY FIRST ACTIONS
1. Read EVERY LINE of the project documentation completely - no skipping or summarizing:
   - All files in `_project/brief/` directory
   - The project tree structure file
2. Confirm you've read each document fully before proceeding

## CODEBASE STRUCTURE
```
project_root/
├── backend/                    # Python FastAPI application
│   ├── src/                   # Core backend modules
│   │   ├── api/               # FastAPI routes & middleware
│   │   ├── config/            # Configuration management
│   │   ├── database/          # Database models & connections
│   │   ├── enums/             # Type definitions
│   │   ├── models/            # Pydantic & SQLAlchemy models
│   │   ├── services/          # Business logic services
│   │   └── utils/             # Utilities
│   ├── alembic/               # Database migrations
│   └── templates/             # Email templates
├── frontend/                   # Next.js React application
│   ├── app/                   # App router pages
│   ├── components/            # React components
│   ├── hooks/                 # Custom hooks
│   └── lib/                   # Frontend utilities
├── tests/                      # All testing (root level)
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── e2e/                   # End-to-end tests
└── _project/                   # Documentation & config
```

## EXACT EXECUTION SEQUENCE WITH COMMANDS

### STEP 1: GET NEXT AVAILABLE TASK
```bash
tm next
```
**This command shows you the next task to work on.**

If no task is shown, check what's available:
```bash
tm list --status=pending
tm list --status=in-progress
```

**CRITICAL: If there are ANY in-progress tasks, you MUST continue those first before starting new ones.**

### STEP 2: EXAMINE THE TASK DETAILS
```bash
tm show <taskId>
```
**From this output, determine:**
- Does this task have subtasks listed?
- If YES: Identify which subtasks are complete and which need work
- If NO: This main task is your work item

**IF TASK IS ALREADY IN-PROGRESS:**
1. **Analyze current codebase state** - check the relevant folders to see what has already been implemented
2. **Compare against task requirements** - identify what parts are complete vs incomplete
3. **Identify the next work item** - the next subtask or remaining work that needs to be done
4. **Continue from where previous work left off** - do NOT restart from beginning

### STEP 3: HANDLE TASK STATUS
**IF TASK IS NOT IN-PROGRESS:**
```bash
tm set-status --id=<taskId> --status=in-progress
```

**IF TASK IS ALREADY IN-PROGRESS:**
- Skip this step - task is already marked correctly
- You are continuing existing work

### STEP 4: IDENTIFY YOUR SPECIFIC WORK ITEM
From the `tm show <taskId>` output:

**SCENARIO A: Task has subtasks**
- Review which subtasks are already complete (check codebase for implemented features)
- Your work item = the next incomplete subtask
- Work on ONLY this one subtask

**SCENARIO B: Task has NO subtasks**  
- Review what parts of the main task are already implemented (check codebase)
- Your work item = the remaining unimplemented parts
- Continue the main task from where it was left off

**FOR IN-PROGRESS TASKS:**
1. **Examine existing code** in relevant folders to understand current implementation state
2. **Compare with task requirements** to identify gaps
3. **Determine next logical step** to continue the work
4. **DO NOT restart or duplicate existing work**

### STEP 5: IMPLEMENT YOUR WORK ITEM
**Code Implementation:**
1. Review existing code in relevant folders from codebase structure above
2. Implement exactly what your work item requires
3. Make all necessary code changes

**Quality Assurance:**
```bash
# Install any new packages if needed
uv install <package-name>

# Format and lint code
ruff check --fix .
ruff format .
```

**Testing:**
```bash
# Run tests (adjust command based on your test setup)
pytest tests/
# OR
python -m pytest tests/
# OR
npm test  # for frontend
```
**ALL TESTS MUST PASS before proceeding.**

**Git Commit and Push:**
```bash
git add .
git commit -m "feat: [Task <taskId>] <specific work item description>"
git push
```
**MANDATORY: Every work item completion MUST be pushed to GitHub.**

### STEP 6: MARK WORK COMPLETE
**SCENARIO A: You completed a subtask within a main task**
- No task-master command needed
- Subtask is complete when code is implemented, tested, and pushed
- Check if more subtasks remain in the same main task:
```bash
tm show <taskId>
```
- If more subtasks exist, repeat from STEP 5 for next subtask
- If ALL subtasks are complete, proceed to mark main task done:
```bash
tm set-status --id=<taskId> --status=done
```

**SCENARIO B: You completed a main task with no subtasks**
```bash
tm set-status --id=<taskId> --status=done
```

### STEP 7: REPEAT PROCESS
Go back to STEP 1 to get the next task.

## TASK-MASTER COMMANDS FOR SPECIAL SITUATIONS

**If task is too complex:**
```bash
tm expand --id=<taskId> --num=5
```
This breaks the task into subtasks.

**If task is blocked:**
```bash
tm set-status --id=<taskId> --status=deferred
```

**Check your progress:**
```bash
tm list --status=pending        # See all pending tasks
tm list --status=in-progress    # See tasks you're working on
tm list --with-subtasks         # See tasks with their subtasks
```

**Validate dependencies every 10 tasks:**
```bash
tm validate-dependencies
```

**If dependencies are broken:**
```bash
tm fix-dependencies
```

**Add new task if needed:**
```bash
tm add-task --prompt="<task description>" [--dependencies=<ids>] [--priority=<priority>]
```

**Update existing task:**
```bash
tm update-task --id=<taskId> --prompt="<additional context>"
```

## CRITICAL RULES WITH EXACT COMMANDS

1. **NEVER work on multiple items simultaneously**
2. **ALWAYS use these exact commands in sequence**
3. **ALWAYS push to GitHub after each work item: `git push`**
4. **ALWAYS use UV for packages: `uv install <package>`**
5. **ALWAYS run ruff: `ruff check --fix . && ruff format .`**
6. **ALWAYS run tests before git push**
7. **ONLY mark main tasks done when ALL subtasks complete**

## PROJECT IS COMPLETE WHEN
```bash
tm list --status=pending
```
Returns no tasks.