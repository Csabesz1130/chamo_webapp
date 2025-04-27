from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from typing import Dict, Any
from urllib.parse import urlparse, parse_qs
from src.utils.logger import app_logger

class TrackingHandler(BaseHTTPRequestHandler):
    """
    A kattintások követéséért felelős HTTP kérés kezelő.
    """
    
    def __init__(self, email_sender, *args, **kwargs):
        """
        Inicializálja a TrackingHandler-t.
        
        Args:
            email_sender: Az EmailSender példány
            *args: További argumentumok
            **kwargs: További kulcsszó argumentumok
        """
        self.email_sender = email_sender
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Feldolgozza a GET kéréseket."""
        try:
            # Feldolgozzuk az URL-t
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            # Kattintás követés
            if path.startswith('/track/'):
                click_id = path[7:]  # '/track/' után következő rész
                self.email_sender.track_click(click_id)
                
                # Válasz küldése
                self.send_response(200)
                self.send_header('Content-type', 'image/gif')
                self.end_headers()
                self.wfile.write(b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')
            else:
                self.send_response(404)
                self.end_headers()
        except Exception as e:
            app_logger.error(f"Hiba a kérés feldolgozásakor: {str(e)}")
            self.send_response(500)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Letiltja a naplózást."""
        pass

class TrackingServer:
    """
    A kattintások követéséért felelős HTTP szerver.
    """
    
    def __init__(self, email_sender, host: str = 'localhost', port: int = 8000):
        """
        Inicializálja a TrackingServer-t.
        
        Args:
            email_sender: Az EmailSender példány
            host: A szerver hosztja
            port: A szerver portja
        """
        self.email_sender = email_sender
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
        self.running = False
        
        app_logger.info("Kattintás követő szerver inicializálva")
    
    def start(self):
        """Elindítja a szervert."""
        if self.running:
            return
        
        # Létrehozzuk a szervert
        def handler(*args, **kwargs):
            return TrackingHandler(self.email_sender, *args, **kwargs)
        
        self.server = HTTPServer((self.host, self.port), handler)
        
        # Elindítjuk a szervert egy külön szálon
        self.running = True
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()
        
        app_logger.info(f"Kattintás követő szerver elindítva: {self.host}:{self.port}")
    
    def stop(self):
        """Leállítja a szervert."""
        if not self.running:
            return
        
        self.running = False
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        
        if self.thread:
            self.thread.join()
        
        app_logger.info("Kattintás követő szerver leállítva")
    
    def _run_server(self):
        """Futtatja a szervert."""
        try:
            while self.running:
                self.server.handle_request()
        except Exception as e:
            app_logger.error(f"Hiba a szerver futtatásakor: {str(e)}")
            self.running = False 