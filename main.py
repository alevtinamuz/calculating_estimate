from PyQt6.QtCore import QPropertyAnimation, QEasingCurve

import getters
import setters
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path
import sys
from PyQt6.QtWidgets import *
from PyQt6 import uic
from design.app_window import MainWindow

env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

app = QApplication(sys.argv)

window = MainWindow(supabase)
window.show()

sys.exit(app.exec())