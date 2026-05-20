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

This plugin uses Archivator as its backend.

👉 https://github.com/ClaireBenes/Archivator

Archivator is included in this plugin as a vendored dependency under:

```text
vendor/archivator/
```

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
- Windows
- Archivator project registry configured through the standalone Archivator app

---

## Installation

### 1. Install Archivator standalone:

Archivator is available on PyPI:

```bash
pip install archivator
```

Launch the standalone application:

```bash
archivator
```

Use the Archivator UI to register your projects and configure their trash directories.

Archivator stores its configuration in a shared user directory:
```bash
~/.archivator/
```
This configuration is shared between the standalone application and the Prism plugin.

### 2. Install the Prism Plugin

Clone or copy this repository into your Prism plugins directory.

Example:
```bash
git clone https://github.com/ClaireBenes/PrismPlugin-TrashManager
```
Then place the plugin inside your Prism project or global plugin folder.

### 3. Restart Prism
After restarting Prism, the plugin will automatically use the projects configured in Archivator.
No manual Python path setup is required.

### Vendored Dependency

This plugin includes a vendored copy of Archivator under:

```bash
vendor/archivator/
```

This avoids requiring users to install Archivator inside Prism's embedded Python environment.

Prism already provides its own Qt/PySide environment, so only Archivator itself is vendored.
