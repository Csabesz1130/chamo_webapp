import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import time
import threading
from typing import List, Dict, Any
from src.utils.logger import app_logger
from src.utils.email_preferences_manager import EmailPreferencesManager


class EmailSender:
    """
    Az e-mail értesítések küldéséért felelős osztály.
    """

    def __init__(
        self, email_manager: EmailPreferencesManager, smtp_config: Dict[str, Any]
    ):
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

        app_logger.info("E-mail küldő inicializálva")

    def start(self):
        """Elindítja az e-mail küldő szolgáltatást."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()

        app_logger.info("E-mail küldő szolgáltatás elindítva")

    def stop(self):
        """Leállítja az e-mail küldő szolgáltatást."""
        self.running = False
        if self.thread:
            self.thread.join()

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
        if now.weekday() == schedule["day"]:
            scheduled_time = datetime.strptime(schedule["time"], "%H:%M").time()
            current_time = now.time()

            # Ha az aktuális idő megegyezik a beállított idővel (1 perces tolerancia)
            if (
                abs(
                    (
                        datetime.combine(datetime.today(), current_time)
                        - datetime.combine(datetime.today(), scheduled_time)
                    ).total_seconds()
                )
                < 60
            ):
                self._send_digest()

    def _send_digest(self):
        """Küldi a heti összefoglalót."""
        try:
            # Összeállítjuk az e-mail tartalmát
            message = self._create_digest_message()

            # Küldjük az e-mailt
            with smtplib.SMTP(
                self.smtp_config["host"], self.smtp_config["port"]
            ) as server:
                if self.smtp_config.get("use_tls", True):
                    server.starttls()

                if self.smtp_config.get("username") and self.smtp_config.get(
                    "password"
                ):
                    server.login(
                        self.smtp_config["username"], self.smtp_config["password"]
                    )

                server.send_message(message)

            app_logger.info("Heti összefoglaló e-mail elküldve")
        except Exception as e:
            app_logger.error(f"Hiba az e-mail küldésekor: {str(e)}")

    def _create_digest_message(self) -> MIMEMultipart:
        """Létrehozza a heti összefoglaló e-mail üzenetet."""
        message = MIMEMultipart("alternative")
        message["Subject"] = "Heti Tudományos Összefoglaló"
        message["From"] = self.smtp_config["from_email"]
        message["To"] = self.smtp_config["to_email"]

        # HTML tartalom
        html = """
        <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; }
                    .article { margin-bottom: 20px; padding: 10px; border: 1px solid #ddd; }
                    .title { font-size: 16px; font-weight: bold; }
                    .authors { color: #666; }
                    .source { color: #888; }
                    .date { color: #888; }
                    .score { height: 20px; background: linear-gradient(to right, #ff0000, #00ff00); }
                </style>
            </head>
            <body>
                <h2>Heti Tudományos Összefoglaló</h2>
                <p>Kedves Felhasználó,</p>
                <p>Íme a heti tudományos összefoglaló a beállított kulcsszavak alapján:</p>
        """

        # Példa cikkek (valós implementációban ezeket a forrásokból kell lekérni)
        articles = self._get_recommended_articles()

        for article in articles:
            html += f"""
                <div class="article">
                    <div class="title">{article['title']}</div>
                    <div class="authors">{article['authors']}</div>
                    <div class="source">{article['source']}</div>
                    <div class="date">{article['date']}</div>
                    <div class="score" style="width: {article['score']}%;"></div>
                    <p><a href="{article['link']}">Olvasás</a> | 
                       <a href="save:{article['id']}">Mentés</a> | 
                       <a href="share:{article['id']}">Megosztás</a></p>
                </div>
            """

        html += """
                <p>Üdvözlettel,<br>Az Ön Tudományos Összefoglaló Csapata</p>
            </body>
        </html>
        """

        message.attach(MIMEText(html, "html"))
        return message

    def _get_recommended_articles(self) -> List[Dict[str, Any]]:
        """Lekéri a javasolt cikkeket a forrásokból."""
        # Ez egy példa implementáció
        # Valós implementációban itt kell lekérni a cikkeket a PubMed, bioRxiv és arXiv API-kból
        return [
            {
                "id": "1",
                "title": "Példa cikk címe",
                "authors": "Kovács János, Nagy Péter",
                "source": "PubMed",
                "date": "2024-03-20",
                "link": "https://example.com/article1",
                "score": 85,
            },
            # További cikkek...
        ]
