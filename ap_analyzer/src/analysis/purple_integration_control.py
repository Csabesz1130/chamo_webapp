"""
A lila görbék integrálási pontjainak vezérléséhez szükséges osztály.
"""

import numpy as np
import tkinter as tk
from tkinter import ttk
from src.utils.logger import app_logger
from matplotlib.patches import Polygon
from matplotlib.collections import PolyCollection

class PurpleIntegrationController:
    """
    Vezérli a lila görbék integrálási kezdő- és végpontjait.
    Vizuális jelzőket biztosít és pontos vezérlést ad az integrálás határainak meghatározásához.
    """
    
    MARKER_ZORDER = 5
    PATCH_ZORDER = 1
    LABEL_ZORDER = 6

    def __init__(self, parent, canvas, ax, callback=None):
        """
        Inicializálja a vezérlőt.
        
        Args:
            parent: Szülő widget (általában ActionPotentialTab)
            canvas: Matplotlib canvas
            ax: Matplotlib tengely
            callback: Hívandó függvény az integrálási pontok változásakor (kap egy dict-et és egy apply bool-t)
        """
        self.parent = parent
        self.canvas = canvas
        self.ax = ax
        self.update_callback = callback
        self.processor = None # ActionPotentialProcessor
        
        # Integrálási pontok tárolása (indexek)
        self.integration_points = {
            'hyperpol_start': 0,
            'hyperpol_end': -1,  # Alapértelmezett: görbe vége
            'depol_start': 0,
            'depol_end': -1     # Alapértelmezett: görbe vége
        }
        
        # Vizuális elemek
        self.markers = {
            'hyperpol_start': None, 'hyperpol_end': None,
            'depol_start': None, 'depol_end': None
        }
        # A fill_between által visszaadott Collection-t tároljuk itt
        self.integration_patches = {
            'hyperpol': None,
            'depol': None
        }
        self.text_labels = {
            'hyperpol_start': None, 'hyperpol_end': None,
            'depol_start': None, 'depol_end': None
        }
        
        # Állapot követés
        self.is_active = False
        self.custom_points_enabled = False
        
        # Létrehozzuk a felhasználói felület vezérlőit
        self._create_ui_controls()
    
    def _create_ui_controls(self):
        """Létrehozza a felhasználói felület vezérlőit."""
        # Fő konténer (összecsukható LabelFrame)
        self.container = ttk.LabelFrame(self.parent.frame, text="Integrálási Pontok")
        
        # Váltó az egyéni integrálási pontok engedélyezéséhez
        self.enable_custom_points = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.container,
            text="Egyéni integrálási pontok engedélyezése",
            variable=self.enable_custom_points,
            command=self._toggle_custom_points
        ).pack(pady=2, anchor='w')
        
        # Vezérlők létrehozása beágyazott keretben
        self.controls_frame = ttk.Frame(self.container)
        self.controls_frame.pack(fill='x', padx=5, pady=2)
        
        # --- Hiperpolarizációs pont vezérlők ---
        hyperpol_frame = ttk.LabelFrame(self.controls_frame, text="Hiperpolarizáció")
        hyperpol_frame.pack(fill='x', pady=2)
        
        # Kezdőpont
        hyperpol_start_frame = ttk.Frame(hyperpol_frame)
        hyperpol_start_frame.pack(fill='x')
        ttk.Label(hyperpol_start_frame, text="Kezdet:", width=7).pack(side='left')
        self.hyperpol_start_point_var = tk.IntVar(value=0)
        self.hyperpol_start_spinbox = ttk.Spinbox(
            hyperpol_start_frame, from_=0, to=199, width=5,
            textvariable=self.hyperpol_start_point_var,
            command=lambda: self._update_integration_point('hyperpol', 'start')
        )
        self.hyperpol_start_spinbox.pack(side='left', padx=5)
        self.hyperpol_start_spinbox.bind('<Return>', lambda e: self._update_integration_point('hyperpol', 'start'))
        ttk.Button(hyperpol_start_frame, text="Reset", width=5, command=lambda: self._reset_integration_point('hyperpol', 'start')).pack(side='left', padx=2)
        self.hyperpol_start_time_var = tk.StringVar(value="0.0 ms")
        ttk.Label(hyperpol_start_frame, textvariable=self.hyperpol_start_time_var, font=('TkDefaultFont', 8, 'italic')).pack(side='left', padx=5)
        
        # Végpont
        hyperpol_end_frame = ttk.Frame(hyperpol_frame)
        hyperpol_end_frame.pack(fill='x')
        ttk.Label(hyperpol_end_frame, text="Vég:", width=7).pack(side='left')
        self.hyperpol_end_point_var = tk.IntVar(value=-1) # -1 jelzi a végét
        self.hyperpol_end_spinbox = ttk.Spinbox(
            hyperpol_end_frame, from_=-1, to=199, width=5, # -1 engedélyezve
            textvariable=self.hyperpol_end_point_var,
            command=lambda: self._update_integration_point('hyperpol', 'end')
        )
        self.hyperpol_end_spinbox.pack(side='left', padx=5)
        self.hyperpol_end_spinbox.bind('<Return>', lambda e: self._update_integration_point('hyperpol', 'end'))
        ttk.Button(hyperpol_end_frame, text="Reset", width=5, command=lambda: self._reset_integration_point('hyperpol', 'end')).pack(side='left', padx=2)
        self.hyperpol_end_time_var = tk.StringVar(value="Vége")
        ttk.Label(hyperpol_end_frame, textvariable=self.hyperpol_end_time_var, font=('TkDefaultFont', 8, 'italic')).pack(side='left', padx=5)
        
        # --- Depolarizációs pont vezérlők ---
        depol_frame = ttk.LabelFrame(self.controls_frame, text="Depolarizáció")
        depol_frame.pack(fill='x', pady=2)
        
        # Kezdőpont
        depol_start_frame = ttk.Frame(depol_frame)
        depol_start_frame.pack(fill='x')
        ttk.Label(depol_start_frame, text="Kezdet:", width=7).pack(side='left')
        self.depol_start_point_var = tk.IntVar(value=0)
        self.depol_start_spinbox = ttk.Spinbox(
            depol_start_frame, from_=0, to=199, width=5,
            textvariable=self.depol_start_point_var,
            command=lambda: self._update_integration_point('depol', 'start')
        )
        self.depol_start_spinbox.pack(side='left', padx=5)
        self.depol_start_spinbox.bind('<Return>', lambda e: self._update_integration_point('depol', 'start'))
        ttk.Button(depol_start_frame, text="Reset", width=5, command=lambda: self._reset_integration_point('depol', 'start')).pack(side='left', padx=2)
        self.depol_start_time_var = tk.StringVar(value="0.0 ms")
        ttk.Label(depol_start_frame, textvariable=self.depol_start_time_var, font=('TkDefaultFont', 8, 'italic')).pack(side='left', padx=5)
        
        # Végpont
        depol_end_frame = ttk.Frame(depol_frame)
        depol_end_frame.pack(fill='x')
        ttk.Label(depol_end_frame, text="Vég:", width=7).pack(side='left')
        self.depol_end_point_var = tk.IntVar(value=-1) # -1 jelzi a végét
        self.depol_end_spinbox = ttk.Spinbox(
            depol_end_frame, from_=-1, to=199, width=5, # -1 engedélyezve
            textvariable=self.depol_end_point_var,
            command=lambda: self._update_integration_point('depol', 'end')
        )
        self.depol_end_spinbox.pack(side='left', padx=5)
        self.depol_end_spinbox.bind('<Return>', lambda e: self._update_integration_point('depol', 'end'))
        ttk.Button(depol_end_frame, text="Reset", width=5, command=lambda: self._reset_integration_point('depol', 'end')).pack(side='left', padx=2)
        self.depol_end_time_var = tk.StringVar(value="Vége")
        ttk.Label(depol_end_frame, textvariable=self.depol_end_time_var, font=('TkDefaultFont', 8, 'italic')).pack(side='left', padx=5)
        
        # Alkalmaz és Mindent visszaállít gombok
        self.button_frame = ttk.Frame(self.container)
        self.button_frame.pack(fill='x', pady=5)
        
        self.apply_button = ttk.Button(
            self.button_frame, 
            text="Mindre alkalmaz",
            command=self._apply_integration_points
        )
        self.apply_button.pack(side='left', padx=5)
        
        self.reset_all_button = ttk.Button(
            self.button_frame, 
            text="Mindent visszaállít",
            command=self._reset_all_integration_points
        )
        self.reset_all_button.pack(side='left', padx=5)
        
        # Kezdetben letiltjuk a vezérlőket
        self._enable_controls(False)
    
    def _toggle_custom_points(self):
        """Váltja az egyéni integrálási pontok engedélyezését."""
        enabled = self.enable_custom_points.get()
        self.custom_points_enabled = enabled
        app_logger.debug(f"Egyéni integrálási pontok {'engedélyezve' if enabled else 'letiltva'}.")
        
        # Engedélyezzük/letiltjuk a vezérlőket
        self._enable_controls(enabled)
        
        # Frissítjük a vizuális jelzőket
        if self.processor:
            if enabled:
                self._add_integration_markers()
                # Pozíciók frissítése a jelenlegi értékekkel
                self._update_marker('hyperpol', 'start')
                self._update_marker('hyperpol', 'end')
                self._update_marker('depol', 'start')
                self._update_marker('depol', 'end')
            else:
                self._remove_integration_markers()
                # Reset points to default when disabling
                self._reset_all_integration_points(apply_callback=False) # Avoid double update
            
            # Frissítjük az integrálokat ha van callback
            if self.update_callback:
                # Pass apply=False when disabling to signal reset, True otherwise?
                # Let's pass apply=False always on toggle, user needs to press Apply explicitly
                self.update_callback(self.get_integration_data(), apply=False)
    
    def _enable_controls(self, enabled):
        """Engedélyezi vagy letiltja az integrálási pont vezérlőket."""
        state = 'normal' if enabled else 'disabled'
        
        # Iterate through all Spinbox and Button widgets in the controls frame
        for frame in self.controls_frame.winfo_children(): # Iterates through LabelFrames (hyperpol, depol)
             if isinstance(frame, ttk.LabelFrame):
                 for sub_frame in frame.winfo_children(): # Iterates through inner Frames (start, end)
                    for widget in sub_frame.winfo_children(): # Iterates through Label, Spinbox, Button
                        if isinstance(widget, (ttk.Spinbox, ttk.Button)):
                            try:
                                widget.configure(state=state)
                            except tk.TclError:
                                pass # Widget might be destroyed
        
        # Also enable/disable Apply and Reset All buttons
        try:
            self.apply_button.configure(state=state)
            self.reset_all_button.configure(state=state)
        except tk.TclError:
            pass # Buttons might not exist yet or be destroyed
    
    def _update_integration_point(self, curve_type, point_type, evt=None):
        """Frissíti egy görbe integrálási kezdő- vagy végpontját."""
        if curve_type not in ['hyperpol', 'depol'] or point_type not in ['start', 'end']:
            app_logger.warning(f"Érvénytelen curve_type ({curve_type}) vagy point_type ({point_type})")
            return
        
        point_key = f"{curve_type}_{point_type}"
        
        # Érték lekérése a megfelelő vezérlőből
        try:
            if curve_type == 'hyperpol':
                spinbox_var = self.hyperpol_start_point_var if point_type == 'start' else self.hyperpol_end_point_var
            else: # depol
                spinbox_var = self.depol_start_point_var if point_type == 'start' else self.depol_end_point_var
            new_point_idx = spinbox_var.get()
        except tk.TclError as e:
            app_logger.error(f"Hiba a spinbox értékének olvasásakor ({point_key}): {e}")
            return
        
        # Határok ellenőrzése és érvényesítés
        max_point_idx = -1
        curve_data = None
        if self.processor:
            curve_data = getattr(self.processor, f"modified_{curve_type}", None)
            if curve_data is not None and len(curve_data) > 0:
                 max_point_idx = len(curve_data) - 1
            else:
                 app_logger.warning(f"Nincs elérhető {curve_type} görbe adat a processzorban.")
                 # Optional: Reset UI if no data?
                 return # Cannot validate without data
        else:
            # No processor, cannot proceed
             app_logger.warning("Processzor nincs beállítva, nem lehet pontot frissíteni.")
             return
        
        # Végpont speciális kezelése (-1 = utolsó pont)
        is_end_point = point_type == 'end'
        validated_point_idx = new_point_idx # Kezdő érték
        
        if is_end_point:
            if new_point_idx == -1:
                validated_point_idx = -1 # Keep -1 as the internal representation for 'last point'
            else:
                start_point_key = f"{curve_type}_start"
                current_start_idx = self.integration_points.get(start_point_key, 0)
                # Ensure end >= start and end <= max
                validated_point_idx = min(max(current_start_idx, new_point_idx), max_point_idx)
        else: # start point
            end_point_key = f"{curve_type}_end"
            current_end_idx_stored = self.integration_points.get(end_point_key, -1)
            # Use actual last index if end is -1
            effective_end_idx = current_end_idx_stored if current_end_idx_stored != -1 else max_point_idx
            # Ensure start >= 0 and start <= effective end
            validated_point_idx = min(max(0, new_point_idx), effective_end_idx)
        
        # Ha a validálás megváltoztatta az értéket, frissítsük a UI-t is
        if validated_point_idx != new_point_idx:
            app_logger.debug(f"Érvényesítés módosította az indexet: {new_point_idx} -> {validated_point_idx}")
            spinbox_var.set(validated_point_idx)
        
        # Érvényesített pont tárolása
        self.integration_points[point_key] = validated_point_idx
        app_logger.debug(f"Integrálási pont frissítve: {point_key} = {validated_point_idx}")
        
        # Vizuális jelzők frissítése (marker, patch, label)
        self._update_marker(curve_type, point_type)
        
        # Időértékek megjelenítésének frissítése a UI-ban
        self._update_time_display(curve_type, point_type)
        
        # Változásokról értesítés (ha a callback létezik és az egyéni pontok aktívak)
        if self.update_callback and self.custom_points_enabled:
            self.update_callback(self.get_integration_data(), apply=False) # Csak frissítés, nem végleges alkalmazás itt
    
    def _reset_integration_point(self, curve_type, point_type):
        """Visszaállítja egy görbe kezdő- vagy végpontját alapértelmezettre."""
        if curve_type not in ['hyperpol', 'depol'] or point_type not in ['start', 'end']:
            return
        
        default_value = 0 if point_type == 'start' else -1
        point_key = f"{curve_type}_{point_type}"
        app_logger.debug(f"Integrálási pont visszaállítása: {point_key} -> {default_value}")
        
        # Visszaállítás alapértelmezettre
        self.integration_points[point_key] = default_value
        
        # Vezérlő frissítése
        try:
            if curve_type == 'hyperpol':
                var = self.hyperpol_start_point_var if point_type == 'start' else self.hyperpol_end_point_var
            else: # depol
                var = self.depol_start_point_var if point_type == 'start' else self.depol_end_point_var
            var.set(default_value)
        except tk.TclError:
            pass # Control might not exist
        
        # Vizuális jelzők frissítése (ha aktív)
        if self.custom_points_enabled:
            self._update_marker(curve_type, point_type)
        
        # Időértékek megjelenítésének frissítése
        self._update_time_display(curve_type, point_type)
        
        # Változásokról értesítés (ha aktív)
        if self.update_callback and self.custom_points_enabled:
            # Hívjuk meg a callback-et apply=False-al, hogy a fő alkalmazás frissíthesse a számolt értékeket (pl. integrál)
             self.update_callback(self.get_integration_data(), apply=False)
    
    def _reset_all_integration_points(self, apply_callback=True):
        """Visszaállítja az összes integrálási pontot alapértelmezettre."""
        app_logger.debug("Összes integrálási pont visszaállítása.")
        # Sorrend fontos lehet a callback miatt, de most mindegyiket False-al hívjuk a resetben
        self._reset_integration_point('hyperpol', 'start')
        self._reset_integration_point('hyperpol', 'end')
        self._reset_integration_point('depol', 'start')
        self._reset_integration_point('depol', 'end')
        
        # Ha kell, egyetlen callback hívás a végén
        if apply_callback and self.update_callback and self.custom_points_enabled:
            self.update_callback(self.get_integration_data(), apply=False) # Reset always means apply=False until user clicks Apply
    
    def _apply_integration_points(self):
        """Alkalmazza az aktuális integrálási pontokat a számításokra (callback hívás apply=True)."""
        app_logger.info("Integrálási pontok alkalmazása.")
        if self.update_callback and self.custom_points_enabled:
            self.update_callback(self.get_integration_data(), apply=True) # Explicit apply=True
        elif not self.custom_points_enabled:
             app_logger.warning("Egyéni pontok nincsenek engedélyezve, nincs mit alkalmazni.")
    
    def _update_marker(self, curve_type, point_type):
        """
        Frissíti a vizuális jelzőt (marker, label) egy adott pontra.
        Meghívja a patch frissítését is.
        """
        if not self.custom_points_enabled or not self.processor or not self.is_active:
            app_logger.debug(f"Marker frissítés kihagyva ({curve_type}_{point_type}): custom_enabled={self.custom_points_enabled}, processor_set={self.processor is not None}, is_active={self.is_active}")
            # Ensure patch is also hidden if controls are off
            self._update_integration_patch(curve_type) # This will hide it if needed
            return
        
        point_key = f"{curve_type}_{point_type}"
        marker = self.markers.get(point_key)
        text_label = self.text_labels.get(point_key)
        
        # Ha a marker/label még nem létezik (pl. show után), hozzuk létre
        if marker is None or text_label is None:
            app_logger.warning(f"Marker vagy label nem található ({point_key}), újrahúzás kísérlete.")
            self._add_integration_markers() # Ez létrehozza őket és frissíti is
            # A _add_integration_markers már meghívja ezt a függvényt a végén, így itt kiléphetünk,
            # hogy elkerüljük a végtelen rekurziót, ha a létrehozás sem sikerül.
            # Viszont ha csak egy marker/label hiányzik, akkor nem akarunk mindent újrahúzni.
            # Próbáljuk meg újra lekérni:
            marker = self.markers.get(point_key)
            text_label = self.text_labels.get(point_key)
            if marker is None or text_label is None:
                app_logger.error(f"Nem sikerült létrehozni/megtalálni a marker/label-t: {point_key}")
                return
        
        idx_stored = self.integration_points.get(point_key)
        curve_data = getattr(self.processor, f"modified_{curve_type}", None)
        time_data = getattr(self.processor, 'time', None)
        
        if curve_data is None or time_data is None or len(curve_data) != len(time_data):
            app_logger.warning(f"Hiányzó vagy inkonzisztens adatok a(z) {curve_type} görbéhez marker frissítéshez.")
            marker.set_visible(False)
            text_label.set_visible(False)
            self._update_integration_patch(curve_type) # Próbáljuk meg eltüntetni a patch-et is
            self.canvas.draw_idle()
            return
        
        max_idx = len(curve_data) - 1
        # Tényleges index kezelése (-1 esetén)
        idx = idx_stored if not (point_type == 'end' and idx_stored == -1) else max_idx
        
        if 0 <= idx <= max_idx:
            x_val = time_data[idx]
            y_val = curve_data[idx]
            
            marker.set_data([x_val], [y_val])
            marker.set_visible(True)
            
            # Label frissítése
            label_text = f"{x_val:.2f} ms" # Vagy f"idx: {idx}"
            text_label.set_text(label_text)
            text_label.set_position((x_val, y_val))
            # Label igazítása a markerhez képest
            ha = 'left' if point_type == 'start' else 'right'
            va = 'bottom' # Vagy 'top'
            # Kis eltolás, hogy ne takarja a markert
            offset = 5 # pontban
            text_label.set_horizontalalignment(ha)
            text_label.set_verticalalignment(va)
            text_label.set_transform(self.ax.transData)
            # Need to consider marker size and label padding for offset
            # This is complex with transforms, maybe simpler alignment is better
            # Or use Annotation instead of Text?
            # Let's keep it simple for now.
            
            text_label.set_visible(True)
        else:
            app_logger.warning(f"Érvénytelen index ({idx}, stored: {idx_stored}) a(z) {point_key} marker frissítéséhez. Max index: {max_idx}")
            marker.set_visible(False)
            text_label.set_visible(False)
        
        # Patch frissítése (mindig, hogy a start/end változásokat tükrözze)
        # Ezt csak akkor kell meghívni, ha a start vagy end pont változott
        self._update_integration_patch(curve_type)
        
        self.canvas.draw_idle()
    
    def _update_integration_patch(self, curve_type):
        """Frissíti vagy eltávolítja az integrációs területet jelző patch-et (fill_between)."""
        patch_collection = self.integration_patches.get(curve_type)
        
        # Ha nem aktív, vagy nincs adat, távolítsuk el a meglévő patch-et
        if not self.custom_points_enabled or not self.processor or not self.is_active:
            if patch_collection is not None:
                app_logger.debug(f"Patch eltávolítása ({curve_type}), mert a vezérlő inaktív.")
                try:
                    patch_collection.remove()
                except ValueError:
                    pass # Lehet már el lett távolítva
                self.integration_patches[curve_type] = None
            # Ensure canvas is redrawn if patch was removed
            # self.canvas.draw_idle() # Called by _update_marker usually
            return
        
        # Adatok lekérése
        start_idx_stored = self.integration_points.get(f"{curve_type}_start", 0)
        end_idx_stored = self.integration_points.get(f"{curve_type}_end", -1)
        curve_data = getattr(self.processor, f"modified_{curve_type}", None)
        time_data = getattr(self.processor, 'time', None)
        
        # Ellenőrzések
        if curve_data is None or time_data is None or len(curve_data) < 2:
            app_logger.debug(f"Patch ({curve_type}) frissítés kihagyva: nincs elég adat.")
            if patch_collection is not None:
                try:
                    patch_collection.remove()
                except ValueError:
                    pass
                self.integration_patches[curve_type] = None
            return
        
        max_idx = len(curve_data) - 1
        start_idx = max(0, start_idx_stored) # Biztosítjuk, hogy ne legyen negatív
        actual_end_idx = end_idx_stored if end_idx_stored != -1 else max_idx
        actual_end_idx = min(max_idx, actual_end_idx) # Biztosítjuk, hogy ne lógjon túl
        
        # Érvényes tartomány ellenőrzése (start <= end)
        if start_idx > actual_end_idx:
            app_logger.warning(f"Érvénytelen indexek a patch-hez ({curve_type}): start={start_idx}, end={actual_end_idx}. Patch elrejtve.")
            if patch_collection is not None:
                try:
                    patch_collection.remove()
                except ValueError:
                    pass
                self.integration_patches[curve_type] = None
            return
        
        # Slice adatok (actual_end_idx + 1 kell a slice végéhez)
        time_slice = time_data[start_idx : actual_end_idx + 1]
        curve_slice = curve_data[start_idx : actual_end_idx + 1]
        
        if len(time_slice) < 2: # Legalább 2 pont kell a fill_between-hez
            app_logger.debug(f"Patch ({curve_type}) frissítés kihagyva: a szelet túl rövid ({len(time_slice)} pont). Start={start_idx}, End={actual_end_idx}")
            if patch_collection is not None:
                try:
                    patch_collection.remove()
                except ValueError:
                    pass
                self.integration_patches[curve_type] = None
            return
        
        # Patch frissítése fill_between használatával
        # Először töröljük a régit, ha van
        if patch_collection is not None:
            try:
                patch_collection.remove()
            except ValueError:
                pass # Már el volt távolítva
        
        # Létrehozunk egy újat
        color = 'purple' if curve_type == 'hyperpol' else 'magenta'
        new_patch_collection = self.ax.fill_between(
             time_slice, curve_slice, 0, # 0 a referencia vonal
             color=color,
             alpha=0.2, # Lehetne állítható?
             zorder=self.PATCH_ZORDER,
             label=f'_{curve_type}_integration_area' # '_' elrejti a legendából
         )
        self.integration_patches[curve_type] = new_patch_collection # Tároljuk az új collection referenciát
        app_logger.debug(f"Patch frissítve ({curve_type}): {start_idx}-{actual_end_idx}")
        # Nem kell set_visible, a fill_between láthatóvá teszi
        # self.canvas.draw_idle() # Called by _update_marker
    
    def _add_integration_markers(self):
        """
        Hozzáadja vagy láthatóvá teszi a vizuális jelzőket (markerek, labelek) a plot-hoz.
        Az _update_marker gondoskodik a pozíciókról.
        """
        if not self.processor or not self.is_active:
             return
        
        marker_styles = {'start': 'o', 'end': 's'} # Kör a kezdő, négyzet a vég
        marker_colors = {'hyperpol': 'darkviolet', 'depol': 'deeppink'} # Különböző árnyalatok
        label_colors = {'hyperpol': 'darkviolet', 'depol': 'deeppink'}
        
        something_created = False
        for curve_type in ['hyperpol', 'depol']:
            for point_type in ['start', 'end']:
                point_key = f"{curve_type}_{point_type}"
                color = marker_colors[curve_type]
                style = marker_styles[point_type]
                
                # Marker létrehozása vagy láthatóvá tétele
                if self.markers.get(point_key) is None:
                    marker, = self.ax.plot([], [], marker=style, color=color, linestyle='None', markersize=8, zorder=self.MARKER_ZORDER, label=f'_{point_key}_marker')
                    self.markers[point_key] = marker
                    something_created = True
                    app_logger.debug(f"Marker létrehozva: {point_key}")
                else:
                    self.markers[point_key].set_visible(True)
                
                # Label létrehozása vagy láthatóvá tétele
                if self.text_labels.get(point_key) is None:
                    # Használjunk Annotation-t a jobb pozícionáláshoz?
                    # Próbáljuk meg a Text-et egyelőre háttérrel.
                    label = self.ax.text(0, 0, '', color=label_colors[curve_type], fontsize=8,
                                        zorder=self.LABEL_ZORDER, visible=False,
                                        bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.7, ec='none'))
                    self.text_labels[point_key] = label
                    something_created = True
                    app_logger.debug(f"Label létrehozva: {point_key}")
                else:
                    self.text_labels[point_key].set_visible(True)
        
        # A patch-eket az _update_patch kezeli, itt nem kell létrehozni.
        # Kezdeti patch frissítés (ha még nincs)
        self._update_integration_patch('hyperpol')
        self._update_integration_patch('depol')
        
        app_logger.debug("Integrálási markerek és labelek hozzáadva/aktiválva.")
        
        # Már nem kell itt _update_marker hívás, mert a _toggle_custom_points vagy
        # a set_processor gondoskodik a kezdeti pozíciók beállításáról.
        # Ha valami új jött létre, rajzoljuk újra a vásznat
        # if something_created:
        #     self.canvas.draw_idle()
    
    def _remove_integration_markers(self):
        """
        Elrejti a vizuális jelzőket (markerek, labelek, patch-ek) a plot-ról.
        """
        app_logger.debug("Integrálási markerek eltávolítása/elrejtése.")
        needs_redraw = False
        for curve_type in ['hyperpol', 'depol']:
            # Patch eltávolítása
            patch = self.integration_patches.get(curve_type)
            if patch is not None:
                 try:
                     patch.remove()
                     needs_redraw = True
                 except ValueError:
                     pass # Már el lett távolítva?
                 self.integration_patches[curve_type] = None # Töröljük a referenciát
            
            for point_type in ['start', 'end']:
                point_key = f"{curve_type}_{point_type}"
                # Marker elrejtése
                marker = self.markers.get(point_key)
                if marker and marker.get_visible():
                    marker.set_visible(False)
                    needs_redraw = True
                
                # Label elrejtése
                label = self.text_labels.get(point_key)
                if label and label.get_visible():
                    label.set_visible(False)
                    needs_redraw = True
        
        if needs_redraw:
             self.canvas.draw_idle()
    
    def _update_time_display(self, curve_type, point_type):
        """Frissíti a UI-ban a megfelelő pont időértékének kijelzését."""
        point_key = f"{curve_type}_{point_type}"
        idx_stored = self.integration_points.get(point_key)
        
        time_str = "N/A"
        if self.processor and self.processor.time is not None:
            time_data = self.processor.time
            max_idx = len(time_data) - 1
            
            if point_type == 'end' and idx_stored == -1:
                time_str = "Vége"
                # Opcionálisan hozzáadhatjuk a tényleges időt zárójelben
                # if max_idx >= 0:
                #    time_str += f" ({time_data[max_idx]:.2f} ms)"
            elif 0 <= idx_stored <= max_idx:
                time_val = time_data[idx_stored]
                time_str = f"{time_val:.2f} ms"
            else:
                # Ha az index érvénytelen (nem -1 és nem a tartományban)
                # De a validálásnak ezt el kéne kerülnie
                time_str = "Érv?"
        
        # Megfelelő StringVar frissítése
        try:
            if curve_type == 'hyperpol':
                var = self.hyperpol_start_time_var if point_type == 'start' else self.hyperpol_end_time_var
            else: # depol
                var = self.depol_start_time_var if point_type == 'start' else self.depol_end_time_var
            var.set(time_str)
        except tk.TclError:
            pass # Control might not exist
    
    def set_processor(self, processor):
        """
        Beállítja az ActionPotentialProcessor példányt és frissíti a vezérlő állapotát.
        """
        self.processor = processor
        app_logger.debug(f"PurpleIntegrationController processzor beállítva: {processor}")
        
        if self.processor and self.processor.time is not None and len(self.processor.time) > 0:
            max_len_idx = len(self.processor.time) - 1 # Maximális index
            # Frissítjük a Spinboxok 'to' értékét
            try:
                self.hyperpol_start_spinbox.config(to=max_len_idx)
                self.hyperpol_end_spinbox.config(to=max_len_idx)
                self.depol_start_spinbox.config(to=max_len_idx)
                self.depol_end_spinbox.config(to=max_len_idx)
            except tk.TclError:
                 app_logger.warning("Hiba a spinboxok 'to' értékének beállításakor.")
            
            # Reseteljük a pontokat az új adatokhoz (lehet, hogy a régi indexek érvénytelenek)
            # és frissítsük a markereket, ha aktívak
            # Itt a callbacket False-ra állítjuk, mert a processzor beállításakor
            # valószínűleg újraszámolás történik a fő alkalmazásban.
            self._reset_all_integration_points(apply_callback=False)
            
            # Frissítsük a vizuális elemeket, ha az egyéni pontok engedélyezve vannak
            if self.custom_points_enabled:
                self._add_integration_markers() # Biztosítjuk, hogy létezzenek/láthatóak legyenek
                # A reset már frissítette a markerek pozícióját 0/-1-re, és hívta az update_marker-t
                # De biztos ami biztos, frissítsünk expliciten:
                self._update_marker('hyperpol', 'start')
                self._update_marker('hyperpol', 'end')
                self._update_marker('depol', 'start')
                self._update_marker('depol', 'end')
        else:
             app_logger.warning("Processzor nincs beállítva vagy nincs időadat, integrációs vezérlők korlátozva.")
             # Nincs processzor vagy időadat, letiltjuk a vezérlőket?
             if self.custom_points_enabled:
                 self.enable_custom_points.set(False) # Kapcsoljuk ki az egyéni pontokat
                 self._toggle_custom_points() # Ez letiltja a vezérlőket és eltünteti a markereket
             else:
                 # Ha már ki volt kapcsolva, csak biztosítsuk, hogy a vezérlők le legyenek tiltva
                 self._enable_controls(False)
    
    def get_integration_data(self):
        """
        Visszaadja az aktuális integrálási pontok indexeit.
        A végpont (-1) itt még nincs feloldva a tényleges indexre.
        A callback függvény felelőssége ezt kezelni, ha szükséges.
        """
        # Közvetlenül a tárolt értékeket adjuk vissza
        data = self.integration_points.copy()
        app_logger.debug(f"Nyers integrációs adatok lekérve: {data}")
        return data
    
    def get_effective_integration_indices(self):
        """
        Visszaadja az effektív integrálási pontok indexeit, ahol a -1 már fel van oldva.
        Returns: Dict vagy None ha nincs processzor/adat.
        """
        if not self.processor or not self.processor.time:
            return None
        
        effective_data = {}
        max_idx = len(self.processor.time) - 1
        
        for curve in ['hyperpol', 'depol']:
            start_key = f"{curve}_start"
            end_key = f"{curve}_end"
            
            start_idx = self.integration_points.get(start_key, 0)
            end_idx_stored = self.integration_points.get(end_key, -1)
            
            effective_start = max(0, start_idx)
            effective_end = end_idx_stored if end_idx_stored != -1 else max_idx
            effective_end = min(max_idx, effective_end)
            
            # Biztosítjuk, hogy start <= end
            effective_start = min(effective_start, effective_end)
            
            effective_data[start_key] = effective_start
            effective_data[end_key] = effective_end
        
        app_logger.debug(f"Effektív integrációs indexek lekérve: {effective_data}")
        return effective_data
    
    def show(self):
        """
        Megjeleníti a vezérlő UI konténerét.
        """
        if not self.is_active:
            self.container.pack(fill='x', expand=False, padx=5, pady=5, anchor='n') # expand=False
            self.is_active = True
            app_logger.debug("PurpleIntegrationController UI megjelenítve.")
            # Frissítsük a markereket, ha szükséges és engedélyezve van
            if self.custom_points_enabled:
                 self._add_integration_markers()
                 # Explicit update markers after show, maybe processor was set while hidden
                 self._update_marker('hyperpol', 'start')
                 self._update_marker('hyperpol', 'end')
                 self._update_marker('depol', 'start')
                 self._update_marker('depol', 'end')
    
    def hide(self):
        """
        Elrejti a vezérlő UI konténerét és a plot elemeket.
        """
        if self.is_active:
            self.container.pack_forget()
            self.is_active = False
            app_logger.debug("PurpleIntegrationController UI elrejtve.")
            # Markerek eltávolítása/elrejtése, ha a UI eltűnik
            self._remove_integration_markers()
    
    def toggle_visibility(self):
        """
        Váltja a vezérlő UI és a plot elemek láthatóságát.
        """
        if self.is_active:
            self.hide()
        else:
            self.show()
        return self.is_active 