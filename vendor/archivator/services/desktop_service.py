import os
import platform
import subprocess


class DesktopService:
    """
    OS integration layer.

    Responsibilities:
    - Open folders in the system file browser
    """

    def open_folder(self, path: str) -> None:
        """
        Open a folder in the OS file browser.

        Args:
            path (str): Folder path to open.

        Raises:
            FileNotFoundError: If the path does not exist.
            RuntimeError: If the OS command fails.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path does not exist: {path}")

        system = platform.system()

        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":
            subprocess.run(["open", path], check=True)
        else:
            subprocess.run(["xdg-open", path], check=True)