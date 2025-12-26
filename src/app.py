"""Main application module."""

from .ui import MainWindow


class App:
    """Main application class."""
    
    def __init__(self):
        self.window = MainWindow()
    
    def run(self):
        """Run the application."""
        self.window.mainloop()
