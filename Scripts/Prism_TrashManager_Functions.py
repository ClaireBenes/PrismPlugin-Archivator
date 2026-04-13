# -*- coding: utf-8 -*-
#
####################################################
#
# PRISM - Pipeline for animation and VFX projects
#
# www.prism-pipeline.com
#
# contact: contact@prism-pipeline.com
#
####################################################
#
#
# Copyright (C) 2016-2023 Richard Frangenberg
# Copyright (C) 2023 Prism Software GmbH
#
# Licensed under GNU LGPL-3.0-or-later
#
# This file is part of Prism.
#
# Prism is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Prism is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Prism.  If not, see <https://www.gnu.org/licenses/>.

import sys
import os

# ---------------------------
# Add Archivator to Python path
# ---------------------------
archivator_root = r"C:\Users\claire.benes\Documents\PythonProject\Archivator\python"
if archivator_root not in sys.path:
    sys.path.append(archivator_root)

# safely import Archivator modules
from services.archive_service import ArchiveService
from core.registry import ProjectRegistry
from core.exceptions import ProjectNotFoundError, ArchivatorError

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from PrismUtils.Decorators import err_catcher_plugin as err_catcher

class PrismArchivatorPlugin:
    """
    Prism plugin that integrates with Archivator.

    Responsibilities:
    - Hook into Prism UI
    - Forward trash/restore operations to Archivator
    - Ensure Archivator is required
    """

    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin

        # Initialize Archivator
        config_path = os.path.join(archivator_root, "config", "projects.json")
        self.registry = ProjectRegistry(config_path)
        self.registry.load()
        self.archivator = ArchiveService(self.registry)

        # Hook into Prism callbacks
        self.core.registerCallback(
            "onProjectBrowserStartup",
            self.onProjectBrowserStartup,
            plugin=self.plugin
        )

        self.core.registerCallback(
            "openPBFileContextMenu",
            self.onRightClickAssetFile,
            plugin=self.plugin
        )

        self.core.registerCallback(
            "onVersionCreated",
            self.onVersionCreated,
            plugin=self.plugin
        )

    # if returns true, the plugin will be loaded by Prism
    @err_catcher(name=__name__)
    def isActive(self):
        return True

    # -----------------------------
    # Prism hooks
    # -----------------------------
    def onProjectBrowserStartup(self, browser):
        # Add trash menu to Prism project browser
        self.addTrashMenu(browser)

    def onRightClickAssetFile(self, origin, menu, path):
        if not path or not os.path.splitext(path)[1]:
            return  # ignore folders

        trashMenu = QMenu("Trash", menu)
        menu.addMenu(trashMenu)

        moveAction = QAction("Move to Trash", trashMenu)
        moveAction.triggered.connect(lambda: self.moveToTrash(path))
        trashMenu.addAction(moveAction)

    def onVersionCreated(self, filepath):
        # Example: automatically mark new versions as auto-delete (optional)
        pass

    # -----------------------------
    # Menu / UI
    # -----------------------------
    def addTrashMenu(self, browser):
        trashMenu = QMenu("Trash", browser.menubar)
        browser.menubar.addMenu(trashMenu)

        openTrashAction = QAction("Open Trash", browser)
        openTrashAction.triggered.connect(self.openTrash)
        trashMenu.addAction(openTrashAction)

        recoverAction = QAction("Recover File", browser)
        recoverAction.triggered.connect(self.recoverTrash)
        trashMenu.addAction(recoverAction)

        clearAction = QAction("Clear Trash", browser)
        clearAction.triggered.connect(self.clearTrash)
        trashMenu.addAction(clearAction)

    # -----------------------------
    # Archivator integration
    # -----------------------------
    def moveToTrash(self, filepath):
        import os

        try:
            dest = self.archivator.move_to_trash(filepath)

            # Extract asset name (last part before extension)
            asset_name = os.path.splitext(os.path.basename(filepath))[0]

            self.core.pb.refreshUI()
            self.core.popup(f"Moved '{asset_name}' to trash")

        except ArchivatorError as e:
            self.core.popup(f"[Error] {e}")

    def recoverTrash(self):
        """
        Let the user select one recoverable trash group and restore it.
        """
        try:
            from ui.dialogs.recover_trash_dialog import RecoverTrashDialog

            project = self.archivator.get_project_from_path(self.core.projectPath)
            trash_folder = project.trash_dir

            if not os.path.exists(trash_folder):
                self.core.popup(f"Trash folder does not exist:\n{trash_folder}")
                return

            dialog = RecoverTrashDialog(trash_folder)

            if dialog.exec() != QDialog.Accepted:
                return

            selected_file = dialog.get_selected_file()
            if not selected_file:
                return

            restored_path = self.archivator.restore(selected_file)
            filename = os.path.basename(restored_path)

            try:
                self.core.configs.clearCache()
            except Exception:
                pass

            try:
                self.core.pb.refreshUI()
            except Exception:
                pass

            self.core.popup(f"Recovered:\n{filename}")

        except ProjectNotFoundError as e:
            self.core.popup(f"Cannot recover from trash: {e}")

        except FileNotFoundError as e:
            self.core.popup(f"Cannot recover file: {e}")

        except ArchivatorError as e:
            self.core.popup(f"Archivator error: {e}")

        except Exception as e:
            self.core.popup(f"Unexpected error recovering trash: {e}")

    def openTrash(self):
        """
        Open the trash folder for the current Prism project.
        """
        try:
            self.archivator.open_trash_from_path(self.core.projectPath)

        except ProjectNotFoundError as e:
            self.core.popup(f"Cannot open trash: {e}")

        except Exception as e:
            self.core.popup(f"Unexpected error opening trash: {e}")

    def clearTrash(self):
        """
        Delete all files in the trash folder for the current project
        using Archivator's service.
        """
        try:
            # Resolve project from current folder (or selected asset)
            project = self.archivator.resolver.resolve(self.core.projectPath)

            # Ask user to confirm
            reply = QMessageBox.question(
                None,
                "Confirm Trash Clear",
                f"Are you sure you want to empty the trash for project '{project.name}'?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply != QMessageBox.Yes:
                return

            # Call Archivator service to empty trash
            self.archivator.empty_project_trash(project.id)

            self.core.popup(f"Trash cleared for project '{project.name}'.")

        except ProjectNotFoundError as e:
            self.core.popup(f"Cannot clear trash: {e}")
        except Exception as e:
            self.core.popup(f"Unexpected error clearing trash: {e}")