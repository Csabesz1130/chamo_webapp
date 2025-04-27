"""
E-mail küldés kezelése különböző szolgáltatókkal.
"""
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import boto3
from postmarker.core import PostmarkClient
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.utils.logger import app_logger
from src.utils.article_fetcher import ArticleFetcher
from src.utils.email_preferences_manager import EmailPreferencesManager
from src.config.deta_config import DetaConfig

class EmailSender:
    """E-mail küldés kezelése."""
    
    def __init__(self):
        """Inicializálja az e-mail küldőt."""
        # E-mail szolgáltató kiválasztása környezeti változó alapján
        self.provider = os.getenv('EMAIL_PROVIDER', 'smtp').lower()
        
        # Szolgáltató specifikus kliensek inicializálása
        if self.provider == 'ses':
            self.client = boto3.client('ses', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        elif self.provider == 'postmark':
            self.client = PostmarkClient(token=os.getenv('POSTMARK_TOKEN'))
        else:  # SMTP
            self.smtp_host = os.getenv('SMTP_HOST', 'localhost')
            self.smtp_port = int(os.getenv('SMTP_PORT', '1025'))
            self.smtp_user = os.getenv('SMTP_USER')
            self.smtp_pass = os.getenv('SMTP_PASS')
        
        # Egyéb komponensek inicializálása
        self.email_manager = EmailPreferencesManager()
        self.article_fetcher = ArticleFetcher(self.email_manager, DetaConfig())
        
        app_logger.info(f"E-mail küldő inicializálva: {self.provider}")
    
    def send_digest(self, user_id: str) -> bool:
        """
        Összeállítja és elküldi a digest e-mailt.
        
        Args:
            user_id: Felhasználó azonosító
            
        Returns:
            bool: Sikeres volt-e a küldés
        """
        try:
            # Felhasználói beállítások lekérése
            user_email = self.email_manager.get_user_email(user_id)
            if not user_email:
                raise ValueError(f"Nem található e-mail cím: {user_id}")
            
            # Ajánlott cikkek lekérése
            articles = self.article_fetcher.get_recommended_articles()
            if not articles:
                app_logger.info(f"Nincs új ajánlott cikk: {user_id}")
                return True
            
            # HTML tartalom összeállítása
            html_content = self._create_digest_html(articles)
            
            # E-mail küldése a megfelelő szolgáltatóval
            subject = "Heti tudományos cikkek ajánlója"
            return self._send_email(user_email, subject, html_content)
            
        except Exception as e:
            app_logger.error(f"Hiba a digest küldésekor: {str(e)}")
            return False
    
    def _create_digest_html(self, articles: List[Dict[str, Any]]) -> str:
        """
        Létrehozza a digest HTML tartalmát.
        
        Args:
            articles: Ajánlott cikkek listája
            
        Returns:
            str: HTML tartalom
        """
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; }
                .article { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
                .title { font-size: 18px; color: #2c3e50; margin-bottom: 10px; }
                .authors { color: #666; margin-bottom: 5px; }
                .source { color: #3498db; }
                .actions { margin-top: 15px; }
                .button {
                    display: inline-block;
                    padding: 8px 15px;
                    margin-right: 10px;
                    background-color: #3498db;
                    color: white;
                    text-decoration: none;
                    border-radius: 3px;
                }
            </style>
        </head>
        <body>
            <h1>Heti tudományos cikkek ajánlója</h1>
        """
        
        for article in articles:
            html += f"""
            <div class="article">
                <div class="title">{article['title']}</div>
                <div class="authors">{article['authors']}</div>
                <div class="source">Forrás: {article['source']}</div>
                <div class="actions">
                    <a href="{article['link']}" class="button">Olvasás</a>
                    <a href="/save/{article['id']}" class="button">Mentés</a>
                    <a href="/share/{article['id']}" class="button">Megosztás</a>
                </div>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        E-mail küldése a kiválasztott szolgáltatóval.
        
        Args:
            to_email: Címzett e-mail címe
            subject: Tárgy
            html_content: HTML tartalom
            
        Returns:
            bool: Sikeres volt-e a küldés
        """
        try:
            from_email = os.getenv('FROM_EMAIL', 'noreply@example.com')
            
            if self.provider == 'ses':
                # AWS SES
                self.client.send_email(
                    Source=from_email,
                    Destination={'ToAddresses': [to_email]},
                    Message={
                        'Subject': {'Data': subject},
                        'Body': {'Html': {'Data': html_content}}
                    }
                )
            elif self.provider == 'postmark':
                # Postmark
                self.client.emails.send(
                    From=from_email,
                    To=to_email,
                    Subject=subject,
                    HtmlBody=html_content
                )
            else:
                # SMTP
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = from_email
                msg['To'] = to_email
                msg.attach(MIMEText(html_content, 'html'))
                
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    if self.smtp_user and self.smtp_pass:
                        server.login(self.smtp_user, self.smtp_pass)
                    server.send_message(msg)
            
            app_logger.info(f"E-mail elküldve: {to_email}")
            return True
            
        except Exception as e:
            app_logger.error(f"Hiba az e-mail küldésekor: {str(e)}")
            return False 