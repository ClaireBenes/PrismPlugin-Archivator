# Prism Archivator Plugin

A Prism plugin that integrates with Archivator to provide safe file deletion and recovery through a project-based trash system.

---

## Overview

This plugin replaces destructive delete operations in Prism with a **non-destructive workflow**:

- Files are moved to a project-specific trash directory
- Files can be restored at any time
- Trash can be accessed directly from Prism

All storage and trash logic is handled by Archivator.

---

## Dependency

This plugin requires Archivator:

👉 https://github.com/ClaireBenes/Archivator

Archivator must be installed and configured with your projects before using this plugin.

---

## Features

- Send files to trash instead of deleting permanently
- Restore files from trash
- Open trash directory directly from Prism
- Integrates with Prism version management workflows

---

## Screenshots

### Send to Trash from Prism
<img width="1341" height="645" alt="image" src="https://github.com/user-attachments/assets/cd7c0cff-e1da-497e-85df-2719dad21d22" />

### Trash Recovery Window
<img width="1069" height="643" alt="image" src="https://github.com/user-attachments/assets/7a72d93c-b218-44b5-8d20-dc29a29ddfca" />

---

## How It Works

1. A user deletes a file or version in Prism  
2. The plugin intercepts the action  
3. The file is moved to the Archivator trash directory  
4. The file can later be:
   - Restored to its original location
   - Permanently removed via Archivator  

Archivator acts as the backend system managing:
- Project paths
- Trash structure
- Recovery operations

---

## Requirements

- Prism 2.0.18
- Python 3.11
- Archivator (local installation required)
- Windows

---

## Installation (Current)

The plugin currently depends on a local Archivator setup.

1. Clone both repositories:

```bash
git clone https://github.com/ClaireBenes/Archivator
git clone https://github.com/ClaireBenes/PrismPlugin-TrashManager

