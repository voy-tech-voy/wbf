---
description: how to run the application from the terminal
---

### Prerequisites
- Ensure children of `imgapp_venv` are present.
- Ensure you are in the project root directory.

### Run Command
// turbo
1. Run the application using the local virtual environment:
```powershell
& "v:\_MY_APPS\ImgApp_1\imgapp_venv\Scripts\python.exe" -m client.main
```

### Notes
- The command uses `-m client.main` to ensure proper absolute imports.
- It bypasses the login window if `dev_mode` is set to `True` in `client/main.py`.
