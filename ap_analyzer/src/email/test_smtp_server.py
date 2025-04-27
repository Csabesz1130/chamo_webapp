"""
Egyszerű SMTP szerver teszteléshez.
"""
import asyncio
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP
from src.utils.logger import app_logger

class TestSMTPHandler:
    """SMTP üzenetek kezelése teszteléshez."""
    
    async def handle_RCPT(self, server, session, envelope, address, rcpt_options):
        """Címzett kezelése."""
        envelope.rcpt_tos.append(address)
        return '250 OK'
    
    async def handle_DATA(self, server, session, envelope):
        """E-mail tartalom kezelése."""
        app_logger.info(f'Teszt e-mail fogadva:')
        app_logger.info(f'Feladó: {envelope.mail_from}')
        app_logger.info(f'Címzettek: {envelope.rcpt_tos}')
        app_logger.info(f'Tartalom:\n{envelope.content.decode()}')
        return '250 Message accepted for delivery'

class TestSMTPServer:
    """Teszt SMTP szerver."""
    
    def __init__(self, host: str = 'localhost', port: int = 1025):
        """
        Inicializálja a teszt SMTP szervert.
        
        Args:
            host: A szerver címe
            port: A szerver portja
        """
        self.host = host
        self.port = port
        self.controller = None
        
    def start(self) -> None:
        """Elindítja a szervert."""
        try:
            self.controller = Controller(
                TestSMTPHandler(),
                hostname=self.host,
                port=self.port
            )
            self.controller.start()
            app_logger.info(f'Teszt SMTP szerver elindult: {self.host}:{self.port}')
            
        except Exception as e:
            app_logger.error(f'Hiba a teszt SMTP szerver indításakor: {str(e)}')
    
    def stop(self) -> None:
        """Leállítja a szervert."""
        if self.controller:
            self.controller.stop()
            app_logger.info('Teszt SMTP szerver leállítva') 