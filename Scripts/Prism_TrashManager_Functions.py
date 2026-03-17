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


from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from PrismUtils.Decorators import err_catcher_plugin as err_catcher


class Prism_TrashManager_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin

        # Hook into the project start
        self.core.registerCallback(
            "onProjectBrowserStartup",
            self.onProjectBrowserStartup,
            plugin=self.plugin
        )

        # Hook into the Project Browser right-click menu
        self.core.registerCallback(
            "openPBFileContextMenu",
            self.onRighClikAssetFile,
            plugin=self.plugin
        )

        # Hook when an asset version is created
        self.core.registerCallback(
            "onVersionCreated",
            self.onVersionCreated,
            plugin=self.plugin
        )

    # if returns true, the plugin will be loaded by Prism
    @err_catcher(name=__name__)
    def isActive(self):
        return True

    def onProjectBrowserStartup(self, browser):
        import os

        #create trash folder
        self.trashDir = os.path.join(self.core.projectPath, "01_Trash")
        if not os.path.exists(self.trashDir):
            os.makedirs(self.trashDir)

        self.addTrashButton(browser)

    def onRighClikAssetFile(self, origin, menu, path):
        import os
        if not path or not os.path.splitext(path)[1]:
            # no extension - probably a folder - ignore
            return

        trashMenu = QMenu("Trash", menu)
        menu.addMenu(trashMenu)

        isEnabled = self.isAutoDeleteEnabled(path)

        autoDeleteAction = QAction("Auto-delete is active", trashMenu)
        autoDeleteAction.setCheckable(True)
        autoDeleteAction.setChecked(isEnabled)
        autoDeleteAction.toggled.connect(lambda checked: self.toggleAutoDelete(path, checked))

        moveAction = QAction("Move to Trash", trashMenu)
        moveAction.triggered.connect(lambda: self.moveToTrash(path))

        trashMenu.addAction(autoDeleteAction)
        trashMenu.addSeparator()
        trashMenu.addAction(moveAction)

    def onVersionCreated(self, filepath):
        self.toggleAutoDelete(filepath, True)

    # ----- JSON -----
    def getVersionJson(self, filepath):
        import os

        base, _ = os.path.splitext(filepath)
        return base + "versioninfo.json"

    def readJson(self, path):
        import os
        import json

        if not os.path.exists(path):
            return {}

        with open(path, "r") as file:
            try:
                return json.load(file)
            except:
                return {}

    def writeJson(self, path, data):
        import json

        with open(path, "w") as file:
            json.dump(data, file, indent=4)

    # Auto delete logic
    def isAutoDeleteEnabled(self, filepath):
        jsonPath = self.getVersionJson(filepath)
        data = self.readJson(jsonPath)

        return data.get("autoDelete", True) #if key is missing, return True by default

    def toggleAutoDelete(self, filepath, enabled):
        jsonPath = self.getVersionJson(filepath)
        data = self.readJson(jsonPath)

        data["autoDelete"] = enabled

        self.writeJson(jsonPath, data)

    # trash logic
    def addTrashButton(self, browser):
        trashMenu = QMenu("Trash", browser.menubar)
        trashMenu.setObjectName(u"trashMenu")

        openTrashAction = QAction("Open Trash", browser)
        openTrashAction.triggered.connect(self.openTrash)

        recoverTrashAction = QAction("Recover File", browser)
        recoverTrashAction.triggered.connect(self.recoverTrash)

        clearTrashAction = QAction("Clear Trash", browser)
        clearTrashAction.triggered.connect(self.clearTrash)

        browser.menubar.addMenu(trashMenu)
        browser.menubar.addAction(trashMenu.menuAction())

        trashMenu.addAction(openTrashAction)
        trashMenu.addAction(recoverTrashAction)
        trashMenu.addSeparator()
        trashMenu.addAction(clearTrashAction)

    def moveToTrash(self, filepath):
        import os
        import shutil

        folder = os.path.dirname(filepath)
        filename = os.path.basename(filepath)

        # remove extension
        base = os.path.splitext(filename)[0]

        # take all files with base name in folder
        for f in os.listdir(folder):
            if f.startswith(base):
                src = os.path.join(folder, f)
                dst = os.path.join(self.trashDir, f)

                # avoid overwriting (if 2 files with same name)
                i = 1
                while os.path.exists(dst):
                    name, ext = os.path.splitext(f)
                    # create new file that end with _i if the file name already exist in the trash
                    dst = os.path.join(self.trashDir, f"{name}_{i}{ext}")
                    i += 1

                shutil.move(src, dst)

        self.core.pb.refreshUI()
        self.core.popup(f"Moved {base} to Trash")

    def openTrash(self):
        import subprocess
        subprocess.Popen(f'explorer "{self.trashDir}"')

    def recoverTrash(self):
        pass

    def clearTrash(self):
        import os
        import shutil

        #verify folder exist
        if not os.path.exists(self.trashDir):
            return

        # Pop up to make sure the user want to empty the trash
        reply = QMessageBox.question(
            None,
            "Confirm Trash Clear",
            "Are you sure you want to empty the trash?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # delete files in folders
        for filename in os.listdir(self.trashDir):
            path = os.path.join(self.trashDir, filename)
            if os.path.isfile(path) or os.path.islink(path):
                os.remove(path)  # delete file or symlink
            elif os.path.isdir(path):
                shutil.rmtree(path)  # delete folder recursively

        self.core.popup("Trash cleared!")
