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

PLUGIN_ROOT = os.path.dirname(os.path.dirname(__file__))
VENDOR_PATH = os.path.join(PLUGIN_ROOT, "vendor")

if VENDOR_PATH not in sys.path:
    sys.path.insert(0, VENDOR_PATH)

from archivator.core.paths import CONFIG_PATH, ensure_app_dirs
from archivator.services.archive_service import ArchiveService
from archivator.core.registry import ProjectRegistry
from archivator.core.exceptions import ProjectNotFoundError, ArchivatorError
from archivator.core.paths import CONFIG_PATH

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
        ensure_app_dirs()
        self.registry = ProjectRegistry(str(CONFIG_PATH))
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
        self.addDeleteShortcut(browser)

    def onRightClickAssetFile(self, origin, menu, path):
        if not path or not os.path.splitext(path)[1]:
            return  # ignore folders

        trashMenu = QMenu("Trash", menu)
        menu.addMenu(trashMenu)

        moveAction = QAction("Move to Trash", trashMenu)
        moveAction.triggered.connect(lambda: self.moveToTrash(path))
        trashMenu.addAction(moveAction)

    def onVersionCreated(self, filepath):
        # automatically mark new versions as auto-delete
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

        trashMenu.addSeparator()

        clearAction = QAction("Clear Trash", browser)
        clearAction.triggered.connect(self.clearTrash)
        trashMenu.addAction(clearAction)

    # -----------------------------
    # Archivator integration
    # -----------------------------
    def moveToTrash(self, filepath):
        import os

        try:
            asset_name = os.path.splitext(os.path.basename(filepath))[0]

            reply = QMessageBox.question(
                None,
                "Move to Trash",
                f"Move '{asset_name}' to trash?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply != QMessageBox.Yes:
                return

            self.archivator.move_to_trash(filepath)

            self.core.pb.refreshUI()

        except ArchivatorError as e:
            self.core.popup(f"[Error] {e}")

    def recoverTrash(self):
        """
        Let the user select one recoverable trash group and restore it.
        """
        try:
            from archivator.ui.dialogs.recover_trash_dialog import RecoverTrashDialog

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

            self.archivator.restore(selected_file)

            self.core.pb.refreshUI()
            self.core.configs.clearCache()

        except ProjectNotFoundError as e:
            self.core.popup(f"Cannot recover from trash: {e}")

        except FileNotFoundError as e:
            self.core.popup(f"Cannot recover file: {e}")

        except ArchivatorError as e:
            self.core.popup(f"Archivator error: {e}")

        except Exception as e:
            self.core.popup(f"Unexpected error recovering trash: {e}")

    def openTrash(self):
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


    def addDeleteShortcut(self, browser):
        """
        Add Delete key shortcut to move the selected asset/version file to trash.
        """
        self.delete_shortcut = QShortcut(QKeySequence(Qt.Key_Delete), browser)
        self.delete_shortcut.activated.connect(self.moveSelectedFileToTrash)

    def moveSelectedFileToTrash(self):
        """
        Move the selected Project Browser file to trash.
        """
        filepath = self.getSelectedProjectBrowserFile()

        self.moveToTrash(filepath)

    def getSelectedProjectBrowserFile(self):
        """
        Return the currently selected scene file from Prism's Project Browser.
        """
        scene_browser = self.core.pb.sceneBrowser
        path = scene_browser.getSelectedScenefile()

        if path and os.path.isfile(path):
            return path

        return None