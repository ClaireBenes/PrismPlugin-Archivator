import json
import os
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import *

from archivator.core.trash.trash_metadata import METADATA_SUFFIX

class RecoverTrashDialog(QDialog):
    """
    Dialog used to browse recoverable trash entries.
    """

    def __init__(self, trash_dir: str, parent=None) -> None:
        super().__init__(parent)

        self.trash_dir = trash_dir
        self.entries: list[dict] = []

        self.setWindowTitle("Recover From Trash")
        self.resize(950, 550)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search by file name...")

        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Last Deleted",
            "Name",
        ])
        self.sort_combo.setFixedWidth(140)

        top_row = QHBoxLayout()
        top_row.addWidget(self.search_edit)
        top_row.addWidget(self.sort_combo)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            "Name",
            "Trash Path",
            "Deleted At",
            "Related Files",
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(False)
        self.table.setTextElideMode(Qt.ElideLeft)

        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)

        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Trash Path
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Deleted At
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Related Files

        self.table.setColumnWidth(0, 260)

        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #9aa0aa;")

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.restore_button = self.buttons.button(QDialogButtonBox.Ok)
        self.restore_button.setText("Restore")
        self.restore_button.setEnabled(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addLayout(top_row)
        layout.addWidget(self.table)
        layout.addWidget(self.info_label)
        layout.addWidget(self.buttons)

        self.search_edit.textChanged.connect(self.apply_filter)
        self.sort_combo.currentIndexChanged.connect(self.apply_filter)
        self.table.itemSelectionChanged.connect(self.update_restore_state)
        self.table.itemDoubleClicked.connect(self.accept)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.reload_entries()

    def reload_entries(self) -> None:
        self.entries = self.collect_main_entries()
        self.apply_filter()

    def collect_main_entries(self) -> list[dict]:
        """
        Build a list of recoverable trash entries.

        Groups metadata by ``group_id``, selects one main file per group,
        and prepares entries for UI display.

        Returns:
            list[dict]: Recoverable entries with name, trash path,
            deletion date, and related file count.
        """

        # If trash folder doesn't exist, nothing to show
        if not os.path.exists(self.trash_dir):
            return []

        # Dictionary to group metadata by group_id (str)
        metadata_by_group: dict[str, list[dict]] = {}

        # Walk through all files in the trash directory
        for root, _, files in os.walk(self.trash_dir):
            for filename in files:

                # Only process metadata files (ignore real files)
                if not filename.endswith(METADATA_SUFFIX):
                    continue

                metadata_path = os.path.join(root, filename)

                # Read metadata JSON safely
                try:
                    with open(metadata_path, "r", encoding="utf-8") as handle:
                        data = json.load(handle)
                except Exception:
                    continue

                # Get the group_id (used to group related files)
                group_id = data.get("group_id")
                if not group_id:
                    continue

                # Create list for this group if it doesn't exist
                if group_id not in metadata_by_group:
                    metadata_by_group[group_id] = []

                # Add this metadata entry to its group
                metadata_by_group[group_id].append(data)

        # Final list used by the UI
        results = []

        # Process each group of related files
        for group_id, entries in metadata_by_group.items():
            main_entry = None

            # Try to find the "main" file (the one originally selected)
            for entry in entries:
                if entry.get("is_main_file"):
                    main_entry = entry
                    break

            # Fallback: if no main file found, take the first one
            if main_entry is None and entries:
                main_entry = entries[0]

            # If still nothing, skip this group
            if main_entry is None:
                continue

            # Get the actual trashed file path
            trashed_path = main_entry.get("trashed_path")

            # Skip if file is missing (e.g. manually deleted)
            if not trashed_path or not os.path.exists(trashed_path):
                continue

            # Build a relative path from trash root (for cleaner UI display)
            relative_trash_path = os.path.relpath(
                os.path.dirname(trashed_path),
                self.trash_dir
            ).replace("\\", "/")

            # Add a clean entry for the UI table
            results.append({
                "group_id": group_id,
                "name": main_entry.get("original_name", os.path.basename(trashed_path)),
                "trash_path": relative_trash_path,
                "trashed_path": trashed_path,  # used later for restore
                "deleted_at": self.format_deleted_at(main_entry.get("deleted_at", "")),
                "related_count": len(entries),  # number of files in this group
            })

        # Sort by deletion date (newest first)
        results.sort(key=lambda item: item["deleted_at"], reverse=True)

        return results

    def format_deleted_at(self, value: str) -> str:
        """
        Convert ISO datetime to a more readable format.
        """
        if not value:
            return ""

        try:
            dt = datetime.fromisoformat(value)
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return value

    def apply_filter(self) -> None:
        search_text = self.search_edit.text().strip().lower()

        if not search_text:
            visible = list(self.entries)
        else:
            visible = [
                entry for entry in self.entries
                if search_text in entry["name"].lower()
            ]

        sort_mode = self.sort_combo.currentText()

        if sort_mode == "Name":
            visible.sort(key=lambda entry: entry["name"].lower())
        else:
            visible.sort(key=lambda entry: entry["deleted_at"], reverse=True)

        self.populate_table(visible)

    def populate_table(self, entries: list[dict]) -> None:
        self.table.setRowCount(0)

        for row, entry in enumerate(entries):
            self.table.insertRow(row)

            name_item = QTableWidgetItem(entry["name"])
            path_item = QTableWidgetItem(entry["trash_path"])
            deleted_item = QTableWidgetItem(entry["deleted_at"])
            count_item = QTableWidgetItem(str(entry["related_count"]))

            #set path data for restoration to the name. Qt.UserRole makes it hidden for the user
            name_item.setData(Qt.UserRole, entry["trashed_path"])
            count_item.setTextAlignment(Qt.AlignCenter)

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, path_item)
            self.table.setItem(row, 2, deleted_item)
            self.table.setItem(row, 3, count_item)

        self.info_label.setText(f"{len(entries)} recoverable entr{'y' if len(entries) == 1 else 'ies'}")
        self.update_restore_state()

    def update_restore_state(self) -> None:
        self.restore_button.setEnabled(bool(self.table.selectedItems()))

    def get_selected_file(self) -> str | None:
        """
        Finds the currently selected row

        Returns:
            The hidden real trash file path attached to that row
        """
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            return None

        row = selected_ranges[0].topRow()
        item = self.table.item(row, 0)
        if item is None:
            return None

        return item.data(Qt.UserRole)

    def accept(self) -> None:
        selected_file = self.get_selected_file()
        if not selected_file:
            QMessageBox.warning(self, "No Selection", "Please select a file group to restore.")
            return

        super().accept()