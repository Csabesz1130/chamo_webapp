import tkinter as tk
from .gui.app import SignalAnalyzerApp  # Fixed import
from .utils.logger import app_logger

def main():
    """Fő program indítása."""
    try:
        app_logger.info("Signal Analyzer alkalmazás indítása")
        root = tk.Tk()
        root.title("Signal Analyzer")
        
        # Set minimum window size
        root.minsize(1200, 800)
        
        # Start maximized
        root.state('zoomed')
        
        # Create and start application
        app = SignalAnalyzerApp(root)
        
        # Inicializáljuk a funkció modulokat
        app_logger.info("Funkció modulok inicializálása...")
        if hasattr(app, 'initialize_purple_regression_support'):
            app_logger.info("Lila regresszió funkció inicializálása")
            app.initialize_purple_regression_support()
            
        if hasattr(app, 'initialize_integration_point_control'):
            app_logger.info("Integrálási pont vezérlő funkció inicializálása")
            app.initialize_integration_point_control()
        
        # Start main event loop
        root.mainloop()
        
    except Exception as e:
        app_logger.critical(f"Alkalmazás indítása sikertelen: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()