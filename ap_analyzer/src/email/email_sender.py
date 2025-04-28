"""
E-mail küldés kezelése különböző szolgáltatókkal.
"""
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from postmarker.core import PostmarkClient
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
from src.utils.logger import app_logger
from src.utils.article_fetcher import ArticleFetcher
from src.utils.email_preferences_manager import EmailPreferencesManager
from src.config.deta_config import DetaConfig
from src.config.email_config import EmailConfig

class EmailSender:
    """E-mail küldés kezelése."""
    
    def __init__(self, config: Optional[EmailConfig] = None):
        """
        Inicializálja az e-mail küldőt.
        
        Args:
            config: E-mail konfigurációs objektum
        """
        self.config = config or EmailConfig.from_env()
        
        # Szolgáltató specifikus kliensek inicializálása
        if self.config.provider == 'ses':
            self.client = boto3.client(
                'ses',
                region_name=self.config.aws_region,
                aws_access_key_id=self.config.aws_access_key_id,
                aws_secret_access_key=self.config.aws_secret_access_key
            )
        elif self.config.provider == 'postmark':
            self.client = PostmarkClient(token=self.config.postmark_token)
        else:  # SMTP
            self._init_smtp_client()
        
        # Egyéb komponensek inicializálása
        self.email_manager = EmailPreferencesManager()
        self.article_fetcher = ArticleFetcher(self.email_manager, DetaConfig())
        
        app_logger.info(f"E-mail küldő inicializálva: {self.config.provider}")
    
    def _init_smtp_client(self) -> None:
        """SMTP kliens inicializálása."""
        if self.config.smtp_use_tls:
            self.smtp_class = smtplib.SMTP_SSL
            self.smtp_context = ssl.create_default_context()
        else:
            self.smtp_class = smtplib.SMTP
            self.smtp_context = None
    
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
            
            # Csak a megadott számú cikket küldjük el
            articles = articles[:self.config.max_articles_per_digest]
            
            # HTML tartalom összeállítása
            html_content = self._create_digest_html(articles)
            
            # E-mail küldése
            subject = self.config.digest_subject_template.format(
                date=datetime.now().strftime('%Y-%m-%d')
            )
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
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Tudományos cikkek ajánlója</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #2c3e50;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f6fa;
                }
                .container {
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                }
                .article {
                    margin: 20px 0;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    background-color: #fff;
                }
                .title {
                    font-size: 18px;
                    color: #2c3e50;
                    margin-bottom: 10px;
                    font-weight: bold;
                }
                .authors {
                    color: #666;
                    margin-bottom: 10px;
                    font-style: italic;
                }
                .source {
                    color: #3498db;
                    margin-bottom: 15px;
                }
                .actions {
                    margin-top: 15px;
                }
                .button {
                    display: inline-block;
                    padding: 8px 15px;
                    margin-right: 10px;
                    background-color: #3498db;
                    color: white;
                    text-decoration: none;
                    border-radius: 3px;
                }
                .button:hover {
                    background-color: #2980b9;
                }
                .footer {
                    margin-top: 30px;
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                }
                @media only screen and (max-width: 600px) {
                    body {
                        padding: 10px;
                    }
                    .container {
                        padding: 15px;
                    }
                    .article {
                        padding: 15px;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Heti tudományos cikkek ajánlója</h1>
                    <p>Az Ön érdeklődési köre alapján válogatva</p>
                </div>
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
                <div class="footer">
                    <p>Ez egy automatikus értesítés. Kérjük, ne válaszoljon erre az e-mailre.</p>
                    <p>A beállításait módosíthatja a felhasználói fiókjában.</p>
                </div>
            </div>
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
            if self.config.provider == 'ses':
                # AWS SES
                try:
                    self.client.send_email(
                        Source=self.config.from_email,
                        Destination={'ToAddresses': [to_email]},
                        Message={
                            'Subject': {'Data': subject},
                            'Body': {'Html': {'Data': html_content}}
                        }
                    )
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    error_msg = e.response['Error']['Message']
                    app_logger.error(f"AWS SES hiba: {error_code} - {error_msg}")
                    raise
                    
            elif self.config.provider == 'postmark':
                # Postmark
                try:
                    self.client.emails.send(
                        From=self.config.from_email,
                        To=to_email,
                        Subject=subject,
                        HtmlBody=html_content,
                        ReplyTo=self.config.reply_to_email or self.config.from_email,
                        MessageStream='outbound'
                    )
                except Exception as e:
                    app_logger.error(f"Postmark hiba: {str(e)}")
                    raise
                    
            else:
                # SMTP
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = self.config.from_email
                msg['To'] = to_email
                msg['Date'] = formatdate(localtime=True)
                msg['Message-ID'] = make_msgid(domain=self.config.from_email.split('@')[1])
                if self.config.reply_to_email:
                    msg['Reply-To'] = self.config.reply_to_email
                msg.attach(MIMEText(html_content, 'html'))
                
                try:
                    with self.smtp_class(
                        self.config.smtp_host,
                        self.config.smtp_port,
                        context=self.smtp_context
                    ) as server:
                        if self.config.smtp_user and self.config.smtp_pass:
                            server.login(self.config.smtp_user, self.config.smtp_pass)
                        server.send_message(msg)
                except Exception as e:
                    app_logger.error(f"SMTP hiba: {str(e)}")
                    raise
            
            app_logger.info(f"E-mail elküldve: {to_email}")
            return True
            
        except Exception as e:
            app_logger.error(f"Hiba az e-mail küldésekor: {str(e)}")
            return False 