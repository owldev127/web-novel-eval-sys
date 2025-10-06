# 🔄 API Workflow Diagram

## Setup Phase (Run Once)

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   npm install   │───▶│ ./setup-python-  │───▶│   npm run dev   │
│                 │    │    env.sh        │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │ Creates venv/    │
                       │ Installs deps    │
                       │ Tests Python     │
                       └──────────────────┘
```

## Runtime Phase (Every API Call)

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Request   │───▶│ Python Executor │───▶│ Python Script   │
│                 │    │                 │    │ (in venv)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │ Uses existing   │
                       │ venv (no setup) │
                       │ Returns results │
                       └──────────────────┘
```

## Key Points

- **Setup Script**: Run once during project initialization
- **API Calls**: Use existing virtual environment automatically
- **No Re-setup**: Unless dependencies change or environment is corrupted
