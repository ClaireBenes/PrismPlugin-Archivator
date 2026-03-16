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
        import os

        self.core = core
        self.plugin = plugin

        #create trash folder
        self.trashDir = os.path.join(self.core.projectPath, "01_Trash")
        if not os.path.exists(self.trashDir):
            os.makedirs(self.trashDir)

        # Hook into the project start
        self.core.registerCallback(
            "onProjectBrowserStartup",
            self.onProjectBrowserStartup,
            plugin=self.plugin
        )

        # Hook into the Project Browser right-click menu
        self.core.registerCallback(
            "openPBFileContextMenu",
            self.onAssetMenu,
            plugin=self.plugin
        )

    # if returns true, the plugin will be loaded by Prism
    @err_catcher(name=__name__)
    def isActive(self):
        return True

    def onProjectBrowserStartup(self, browser):
        self.addTrashButton(browser)
        #TODO: Have a Trash shelf with button like open but also recover file

    def onAssetMenu(self, origin, menu, path):
        moveAction = QAction("Move to Trash", origin)
        moveAction.triggered.connect(lambda: self.moveToTrash(path))
        menu.addAction(moveAction)

    def moveToTrash(self, filepath):
        #TODO: Move with the json file (and maybe preview)
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

    def addTrashButton(self, browser):
        trashAction = QAction("Open Trash", browser)
        trashAction.triggered.connect(self.openTrash)

        browser.menubar.addAction(trashAction)

    def openTrash(self):
        import subprocess

        subprocess.Popen(f'explorer "{self.trashDir}"')
