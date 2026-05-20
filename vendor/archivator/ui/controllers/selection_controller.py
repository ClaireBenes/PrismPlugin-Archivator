from PySide6.QtCore import Qt


class ProjectSelectionController:
    """
    Manage project card selection state.

    Responsibilities:
    - Store selected projects/cards
    - Handle click, Ctrl-click, Shift-click selection
    - Clear selection
    - Return selected projects
    """

    def __init__(self) -> None:
        self.selected_projects = {}
        self.project_cards = []
        self.last_selected_card = None

    def set_cards(self, cards: list) -> None:
        """
        Store the current ordered list of project cards.
        """
        self.project_cards = cards

    def select_project(self, project, card, modifiers=None) -> None:
        """
        Select a project card based on keyboard modifiers.
        """
        ctrl_pressed = modifiers and bool(modifiers & Qt.ControlModifier)
        shift_pressed = modifiers and bool(modifiers & Qt.ShiftModifier)

        if shift_pressed and self.last_selected_card in self.project_cards:
            self.select_range(self.last_selected_card, card)
            return

        if ctrl_pressed:
            self.toggle_project(project, card)
            self.last_selected_card = card
            return

        self.clear_selection()
        self.add_project(project, card)
        self.last_selected_card = card

    def add_project(self, project, card) -> None:
        """
        Add a project card to the selection.
        """
        card.set_selected(True)
        self.selected_projects[project.id] = (project, card)

    def remove_project(self, project, card) -> None:
        """
        Remove a project card from the selection.
        """
        card.set_selected(False)
        self.selected_projects.pop(project.id, None)

    def toggle_project(self, project, card) -> None:
        """
        Toggle project selection.
        """
        if project.id in self.selected_projects:
            self.remove_project(project, card)
        else:
            self.add_project(project, card)

    def select_range(self, start_card, end_card) -> None:
        """
        Select all project cards between two cards.
        """
        if start_card not in self.project_cards or end_card not in self.project_cards:
            return

        start_index = self.project_cards.index(start_card)
        end_index = self.project_cards.index(end_card)

        if start_index > end_index:
            start_index, end_index = end_index, start_index

        self.clear_selection()

        for card in self.project_cards[start_index:end_index + 1]:
            self.add_project(card.project, card)

        self.last_selected_card = end_card

    def clear_selection(self) -> None:
        """
        Clear all selected project cards.
        """
        for project, card in self.selected_projects.values():
            card.set_selected(False)

        self.selected_projects.clear()
        self.last_selected_card = None

    def get_selected_projects(self) -> list:
        """
        Return selected Project objects.
        """
        return [
            project
            for project, card in self.selected_projects.values()
        ]

    def has_selection(self) -> bool:
        """
        Return True if at least one project is selected.
        """
        return bool(self.selected_projects)

    def count(self) -> int:
        """
        Return selected project count.
        """
        return len(self.selected_projects)