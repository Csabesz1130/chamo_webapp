"""
Modul a perzisztens alkalmazásbeállítások kezelésére.
"""

import os
import json
from platformdirs import user_config_dir
from typing import Optional, Dict, Any
from src.utils.logger import app_logger

class PersistentSettingsManager:
    """
    Kezeli az alkalmazás beállításainak mentését és betöltését egy JSON fájlba.
    Platformfüggetlen konfigurációs könyvtárat használ.
    """
    APP_NAME = "DataChamo"
    APP_AUTHOR = "User" # Vagy a fejlesztő neve/cégneve

    def __init__(self, filename: str = "settings.json"):
        """
        Inicializálja a beállításkezelőt.

        Args:
            filename (str): A beállításokat tartalmazó JSON fájl neve.
        """
        config_dir = user_config_dir(self.APP_NAME, self.APP_AUTHOR)
        self.settings_path = os.path.join(config_dir, filename)
        self.settings: Dict[str, Any] = {}
        app_logger.info(f"Beállítások fájl elérési útja: {self.settings_path}")

        try:
            self._load_settings()
        except Exception as e:
            app_logger.error(f"Hiba történt a beállítások kezdeti betöltésekor: {e}", exc_info=True)
            app_logger.warning("Üres beállításokkal folytatódik a működés.")
            self.settings = {} # Biztosítjuk, hogy üres legyen hiba esetén

    def _load_settings(self):
        """Betölti a beállításokat a JSON fájlból."""
        if not os.path.exists(self.settings_path):
            app_logger.info("Beállításfájl nem található. Új létrehozása mentéskor.")
            self.settings = {}
            return

        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                self.settings = json.load(f)
            app_logger.info(f"Beállítások sikeresen betöltve innen: {self.settings_path}")
        except FileNotFoundError:
            app_logger.warning(f"Beállításfájl nem található itt: {self.settings_path}. Üres beállítások használata.")
            self.settings = {}
        except json.JSONDecodeError as e:
            app_logger.error(f"Hiba a beállításfájl dekódolásakor ({self.settings_path}): {e}")
            app_logger.warning("Sérült beállításfájl? Üres beállításokkal való felülírás mentéskor.")
            self.settings = {} # Sérült fájl esetén üres beállításokkal kezdünk
        except Exception as e:
            app_logger.error(f"Ismeretlen hiba a beállítások betöltésekor ({self.settings_path}): {e}", exc_info=True)
            self.settings = {} # Egyéb hiba esetén is biztonságos alapállapot

    def save_settings(self):
        """Elmenti az aktuális beállításokat a JSON fájlba."""
        try:
            # Győződjünk meg róla, hogy a könyvtár létezik
            config_dir = os.path.dirname(self.settings_path)
            os.makedirs(config_dir, exist_ok=True)

            # Mentsük a beállításokat JSON formátumban
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            app_logger.info(f"Beállítások sikeresen elmentve ide: {self.settings_path}")
        except IOError as e:
            app_logger.error(f"I/O Hiba a beállítások mentésekor ({self.settings_path}): {e}", exc_info=True)
        except Exception as e:
            app_logger.error(f"Ismeretlen hiba a beállítások mentésekor ({self.settings_path}): {e}", exc_info=True)

    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Lekér egy általános beállítást a kulcs alapján.

        Args:
            key (str): A beállítás kulcsa.
            default (Any, optional): Visszatérési érték, ha a kulcs nem található. Defaults to None.

        Returns:
            Any: A beállítás értéke vagy a default érték.
        """
        return self.settings.get(key, default)

    def set_setting(self, key: str, value: Any):
        """
        Beállít egy általános beállítást.

        Args:
            key (str): A beállítás kulcsa.
            value (Any): A beállítás új értéke.
        """
        self.settings[key] = value
        # Opcionálisan azonnali mentés: self.save_settings()
        # De általában jobb később, kötegelve menteni.

    def get_optimal_start_point(self, filepath: str) -> Optional[int]:
        """
        Lekéri az optimális kezdőpontot egy adott fájlhoz.

        Args:
            filepath (str): A fájl elérési útja, ami kulcsként szolgál.

        Returns:
            Optional[int]: A tárolt optimális kezdőpont (index) vagy None, ha nincs tárolva.
        """
        try:
            start_points = self.settings.get('optimal_start_points', {})
            # Biztosítjuk, hogy a start_points szótár legyen
            if not isinstance(start_points, dict):
                app_logger.warning("Az 'optimal_start_points' beállítás nem szótár. Adat visszaállítása.")
                self.settings['optimal_start_points'] = {}
                return None
            
            value = start_points.get(filepath)
            if value is not None and isinstance(value, int):
                return value
            elif value is not None:
                 app_logger.warning(f"Nem egész szám érték található az optimal_start_points alatt a '{filepath}' kulcshoz: {value}. None visszaadva.")
                 return None
            else:
                return None # Nincs ilyen kulcs
        except Exception as e:
            app_logger.error(f"Hiba az optimal_start_point lekérésekor ('{filepath}'): {e}", exc_info=True)
            return None

    def set_optimal_start_point(self, filepath: str, value: int):
        """
        Beállítja az optimális kezdőpontot egy adott fájlhoz.

        Args:
            filepath (str): A fájl elérési útja, ami kulcsként szolgál.
            value (int): Az optimális kezdőpont (index).
        """
        if not isinstance(value, int):
            app_logger.error(f"Érvénytelen típus az optimális kezdőpont beállításához: {type(value)}. Csak int elfogadott.")
            return

        try:
            # Biztosítja, hogy a 'optimal_start_points' kulcs létezzen és szótár legyen
            start_points = self.settings.setdefault('optimal_start_points', {})

            # Ha valamiért nem szótár (pl. sérült fájl után), inicializáljuk újra
            if not isinstance(start_points, dict):
                 app_logger.warning("Az 'optimal_start_points' beállítás nem szótár volt. Üres szótár létrehozása.")
                 start_points = {}
                 self.settings['optimal_start_points'] = start_points

            start_points[filepath] = value
            app_logger.debug(f"Optimális kezdőpont beállítva '{filepath}': {value}")
            # Fontos: Itt nem mentünk automatikusan, a hívó felelőssége menteni,
            # amikor végzett a módosításokkal (pl. ablak bezárásakor).
        except Exception as e:
            app_logger.error(f"Hiba az optimal_start_point beállításakor ('{filepath}'={value}): {e}", exc_info=True)

# Példányosítás a modul szintjén, hogy könnyen importálható legyen máshol
# Singleton-szerű használat
persistent_settings = PersistentSettingsManager()

# Példa használat (teszteléshez, ha közvetlenül futtatjuk)
if __name__ == '__main__':
    print(f"Beállítások fájl: {persistent_settings.settings_path}")
    print(f"Kezdeti beállítások: {persistent_settings.settings}")

    # Teszt optimális pontok beállítása
    file1 = "/path/to/data/file1.csv"
    file2 = "C:\Users\Test\Documents\data2.txt"

    print(f"Kezdőpont lekérése '{file1}' előtt: {persistent_settings.get_optimal_start_point(file1)}")
    persistent_settings.set_optimal_start_point(file1, 150)
    print(f"Kezdőpont beállítása '{file1}': 150")
    print(f"Kezdőpont lekérése '{file1}' után: {persistent_settings.get_optimal_start_point(file1)}")

    persistent_settings.set_optimal_start_point(file2, 300)
    print(f"Kezdőpont beállítása '{file2}': 300")

    # Teszt általános beállítás
    print(f"Ablakméret lekérése előtt: {persistent_settings.get_setting('window_size')}")
    persistent_settings.set_setting('window_size', {'width': 800, 'height': 600})
    print(f"Ablakméret beállítva: {{'width': 800, 'height': 600}}")
    print(f"Ablakméret lekérése után: {persistent_settings.get_setting('window_size')}")

    print(f"Jelenlegi beállítások mentés előtt: {persistent_settings.settings}")

    # Mentés
    persistent_settings.save_settings()
    print("\nBeállítások elmentve.")

    # Új példány létrehozása a betöltés teszteléséhez
    print("\nÚj beállításkezelő példány létrehozása a betöltés teszteléséhez...")
    new_settings_manager = PersistentSettingsManager()
    print(f"Betöltött beállítások: {new_settings_manager.settings}")
    print(f"Lekérés új példányból '{file1}': {new_settings_manager.get_optimal_start_point(file1)}")
    print(f"Lekérés új példányból 'window_size': {new_settings_manager.get_setting('window_size')}")

    # Sérült fájl szimulálása (manuálisan kellene)
    # print("\nSérült fájl szimulálása (manuálisan módosítsd a settings.json-t hibásra)...")
    # input("Nyomj Entert a folytatáshoz a fájl módosítása után...")
    # faulty_manager = PersistentSettingsManager()
    # print(f"Beállítások sérült fájl után: {faulty_manager.settings}") 