import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import time
import threading
from typing import List, Dict, Any
from src.utils.logger import app_logger
from src.utils.email_preferences_manager import EmailPreferencesManager
from src.utils.article_fetcher import ArticleFetcher
from src.utils.click_tracker import ClickTracker
from src.utils.tracking_server import TrackingServer
from src.utils.article_manager import ArticleManager

class EmailSender:
    """
    Az e-mail értesítések küldéséért felelős osztály.
    """
    
    def __init__(self, email_manager: EmailPreferencesManager, smtp_config: Dict[str, Any]):
        """
        Inicializálja az EmailSender-t.
        
        Args:
            email_manager: Az EmailPreferencesManager példány
            smtp_config: SMTP szerver beállítások
        """
        self.email_manager = email_manager
        self.smtp_config = smtp_config
        self.running = False
        self.thread = None
        
        # Cikk lekérő inicializálása
        self.article_fetcher = ArticleFetcher(email_manager)
        
        # Cikk kezelő inicializálása
        self.article_manager = ArticleManager(email_manager.settings_manager)
        
        # Kattintás követő inicializálása
        self.click_tracker = ClickTracker(email_manager.settings_manager)
        
        # Kattintás követő szerver inicializálása
        self.tracking_server = TrackingServer(self)
        
        app_logger.info("E-mail küldő inicializálva")
    
    def start(self):
        """Elindítja az e-mail küldő szolgáltatást."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        
        # Elindítjuk a kattintás követő szervert
        self.tracking_server.start()
        
        app_logger.info("E-mail küldő szolgáltatás elindítva")
    
    def stop(self):
        """Leállítja az e-mail küldő szolgáltatást."""
        self.running = False
        if self.thread:
            self.thread.join()
        
        # Leállítjuk a kattintás követő szervert
        self.tracking_server.stop()
        
        app_logger.info("E-mail küldő szolgáltatás leállítva")
    
    def _run_scheduler(self):
        """Futtatja az e-mail küldő ütemezőt."""
        while self.running:
            try:
                if self.email_manager.is_enabled():
                    self._check_and_send_emails()
                
                # Vár 1 percet a következő ellenőrzésig
                time.sleep(60)
            except Exception as e:
                app_logger.error(f"Hiba az e-mail küldő szolgáltatásban: {str(e)}")
                time.sleep(300)  # Vár 5 percet hiba esetén
    
    def _check_and_send_emails(self):
        """Ellenőrzi és küldi az e-maileket, ha szükséges."""
        now = datetime.now()
        schedule = self.email_manager.get_delivery_schedule()
        
        # Ellenőrizzük, hogy a megfelelő napon és időben vagyunk-e
        if now.weekday() == schedule['day']:
            scheduled_time = datetime.strptime(schedule['time'], '%H:%M').time()
            current_time = now.time()
            
            # Ha az aktuális idő megegyezik a beállított idővel (1 perces tolerancia)
            if abs((datetime.combine(datetime.today(), current_time) - 
                   datetime.combine(datetime.today(), scheduled_time)).total_seconds()) < 60:
                self._send_digest()
    
    def _send_digest(self):
        """Küldi a heti összefoglalót."""
        try:
            # Összeállítjuk az e-mail tartalmát
            message = self._create_digest_message()
            
            # Küldjük az e-mailt
            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                if self.smtp_config.get('use_tls', True):
                    server.starttls()
                
                if self.smtp_config.get('username') and self.smtp_config.get('password'):
                    server.login(self.smtp_config['username'], self.smtp_config['password'])
                
                server.send_message(message)
            
            app_logger.info("Heti összefoglaló e-mail elküldve")
        except Exception as e:
            app_logger.error(f"Hiba az e-mail küldésekor: {str(e)}")
    
    def _create_digest_message(self) -> MIMEMultipart:
        """Létrehozza a heti összefoglaló e-mail üzenetet."""
        message = MIMEMultipart('alternative')
        message['Subject'] = "Heti Tudományos Összefoglaló"
        message['From'] = self.smtp_config['from_email']
        message['To'] = self.smtp_config['to_email']
        
        # HTML tartalom
        html = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .article {{ margin-bottom: 20px; padding: 10px; border: 1px solid #ddd; }}
                    .title {{ font-size: 16px; font-weight: bold; }}
                    .authors {{ color: #666; }}
                    .source {{ color: #888; }}
                    .date {{ color: #888; }}
                    .score {{ height: 20px; background: linear-gradient(to right, #ff0000, #00ff00); }}
                    .tracking-pixel {{ width: 1px; height: 1px; }}
                </style>
            </head>
            <body>
                <h2>Heti Tudományos Összefoglaló</h2>
                <p>Kedves Felhasználó,</p>
                <p>Íme a heti tudományos összefoglaló a beállított kulcsszavak alapján:</p>
        """
        
        # Cikkek lekérése
        articles = self._get_recommended_articles()
        
        for article in articles:
            # Kattintás követéshez egyedi azonosítók
            read_id = f"read_{article['id']}"
            save_id = f"save_{article['id']}"
            share_id = f"share_{article['id']}"
            
            # Kattintás követés URL-ek
            tracking_url = f"http://{self.tracking_server.host}:{self.tracking_server.port}"
            
            # Ellenőrizzük, hogy a cikk már mentve van-e
            is_saved = any(a['id'] == article['id'] for a in self.article_manager.get_reading_list())
            
            html += f"""
                <div class="article">
                    <div class="title">{article['title']}</div>
                    <div class="authors">{article['authors']}</div>
                    <div class="source">{article['source']}</div>
                    <div class="date">{article['date']}</div>
                    <div class="score" style="width: {article['score']}%;"></div>
                    <p>
                        <a href="{article['link']}" onclick="trackClick('{read_id}')">Olvasás</a> | 
                        <a href="save:{article['id']}" onclick="trackClick('{save_id}')" {'disabled' if is_saved else ''}>{'Mentve' if is_saved else 'Mentés'}</a> | 
                        <a href="share:{article['id']}" onclick="trackClick('{share_id}')">Megosztás</a>
                    </p>
                    <img src="{tracking_url}/track/{read_id}" class="tracking-pixel" alt="">
                </div>
            """
        
        # Kattintás követés JavaScript
        html += f"""
            <script>
                function trackClick(id) {{
                    var img = new Image();
                    img.src = '{tracking_url}/track/' + id;
                    
                    // Ha mentés vagy megosztás, akkor frissítjük a gombot
                    if (id.startsWith('save_')) {{
                        var link = event.target;
                        link.textContent = 'Mentve';
                        link.disabled = true;
                    }}
                }}
            </script>
            <p>Üdvözlettel,<br>Az Ön Tudományos Összefoglaló Csapata</p>
            </body>
        </html>
        """
        
        message.attach(MIMEText(html, 'html'))
        return message
    
    def _get_recommended_articles(self) -> List[Dict[str, Any]]:
        """Lekéri a javasolt cikkeket az ArticleFetcher-től."""
        try:
            return self.article_fetcher.get_recommended_articles()
        except Exception as e:
            app_logger.error(f"Hiba a cikkek lekérésekor: {str(e)}")
            return []
    
    def track_click(self, click_id: str):
        """
        Nyomon követi egy kattintást.
        
        Args:
            click_id: A kattintás azonosítója (pl. 'read_1', 'save_1', 'share_1')
        """
        try:
            action, article_id = click_id.split('_', 1)
            
            # Kattintás követése
            self.click_tracker.track_article_click(article_id, action)
            
            # Ha mentés vagy megosztás, akkor elmentjük a cikket
            if action == 'save':
                # Megkeressük a cikket
                articles = self._get_recommended_articles()
                article = next((a for a in articles if a['id'] == article_id), None)
                
                if article:
                    self.article_manager.save_to_reading_list(article)
            
            elif action == 'share':
                # Megkeressük a cikket
                articles = self._get_recommended_articles()
                article = next((a for a in articles if a['id'] == article_id), None)
                
                if article:
                    # Itt kellene egy projekt azonosító, de most csak egy példa
                    self.article_manager.share_article(article, 'default_project')
            
            app_logger.debug(f"Kattintás rögzítve: {click_id}")
        except Exception as e:
            app_logger.error(f"Hiba a kattintás rögzítésekor: {str(e)}") 