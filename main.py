"""Entry point for the Fast Food POS desktop application."""
import sys

from PySide6.QtWidgets import QApplication

from database import init_db
from ui.login_window import LoginDialog
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    init_db()

    while True:
        login = LoginDialog()
        if login.exec() != LoginDialog.Accepted or login.user is None:
            break

        window = MainWindow(login.user)
        loop_result = {"logged_out": False}

        def on_logout():
            loop_result["logged_out"] = True

        window.logout_requested.connect(on_logout)
        window.show()
        app.exec()

        if not loop_result["logged_out"]:
            break

    sys.exit(0)


if __name__ == "__main__":
    main()
