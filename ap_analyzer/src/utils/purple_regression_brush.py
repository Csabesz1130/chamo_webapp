import numpy as np
from matplotlib import pyplot as plt
from src.utils.logger import app_logger

class PurpleRegressionBrushMixin:
    """
    Mixin osztály a lila regressziós ecset funkcionalitásához.
    Ez a mixin hozzáadja a lila görbe regressziós ecset funkcióját a CurvePointTracker osztályhoz.
    """
    
    def __init__(self, *args, **kwargs):
        """Inicializálja a lila regressziós ecset tulajdonságait."""
        super().__init__(*args, **kwargs)
        
        # Lila regressziós ecset állapotváltozók
        self._purple_regression_enabled = False
        self._purple_regression_points = []
        self._purple_regression_line = None
        self._purple_regression_brush = None
        
        # Eredeti görbék tárolása
        self._original_hyperpol = None
        self._original_depol = None
        
        # Regressziós együtthatók
        self._regression_coeffs = None
        
        app_logger.debug("PurpleRegressionBrushMixin inicializálva")
    
    def toggle_purple_regression_brush(self, enable):
        """
        Engedélyezi vagy letiltja a lila regressziós ecsetet.
        
        Args:
            enable: True ha engedélyezni kell, False ha letiltani
        """
        self._purple_regression_enabled = enable
        
        if enable:
            # Mentjük az eredeti görbéket
            if 'purple_hyperpol' in self.curve_data:
                self._original_hyperpol = self.curve_data['purple_hyperpol']['data'].copy()
            if 'purple_depol' in self.curve_data:
                self._original_depol = self.curve_data['purple_depol']['data'].copy()
            
            # Létrehozzuk az ecsetet
            self._create_regression_brush()
            app_logger.info("Lila regressziós ecset engedélyezve")
        else:
            # Töröljük az ecsetet
            self._remove_regression_brush()
            app_logger.info("Lila regressziós ecset letiltva")
    
    def _create_regression_brush(self):
        """Létrehozza a regressziós ecsetet."""
        if self._purple_regression_brush is None:
            self._purple_regression_brush = self.ax.plot([], [], 'r-', alpha=0.5)[0]
            self._purple_regression_line = self.ax.plot([], [], 'g--', alpha=0.7)[0]
    
    def _remove_regression_brush(self):
        """Eltávolítja a regressziós ecsetet."""
        if self._purple_regression_brush is not None:
            self._purple_regression_brush.remove()
            self._purple_regression_brush = None
        
        if self._purple_regression_line is not None:
            self._purple_regression_line.remove()
            self._purple_regression_line = None
        
        self._purple_regression_points = []
        self._regression_coeffs = None
    
    def _on_mouse_move(self, event):
        """
        Feldolgozza az egér mozgását a regressziós ecset használatakor.
        """
        if not self._purple_regression_enabled or not event.inaxes:
            return super()._on_mouse_move(event)
        
        # Kijelölési logika
        if event.button == 1:  # Bal egérgomb
            x, y = event.xdata, event.ydata
            self._purple_regression_points.append((x, y))
            
            # Frissítjük az ecset vonalat
            if len(self._purple_regression_points) > 1:
                points = np.array(self._purple_regression_points)
                self._purple_regression_brush.set_data(points[:, 0], points[:, 1])
                self.fig.canvas.draw_idle()
        
        return super()._on_mouse_move(event)
    
    def _on_mouse_release(self, event):
        """
        Feldolgozza az egérgomb felengedését a regressziós ecset használatakor.
        """
        if not self._purple_regression_enabled or not event.inaxes:
            return super()._on_mouse_release(event)
        
        if event.button == 1 and len(self._purple_regression_points) > 1:
            # Számítjuk ki a regressziót
            points = np.array(self._purple_regression_points)
            self._calculate_regression(points)
            
            # Frissítjük a görbéket
            self._update_purple_curves()
            
            # Töröljük a kijelölést
            self._purple_regression_points = []
            self._purple_regression_brush.set_data([], [])
            self.fig.canvas.draw_idle()
        
        return super()._on_mouse_release(event)
    
    def _calculate_regression(self, points):
        """
        Kiszámítja a regressziós együtthatókat a kijelölt pontok alapján.
        
        Args:
            points: A kijelölt pontok koordinátái
        """
        x = points[:, 0]
        y = points[:, 1]
        
        # Elsőfokú regresszió
        self._regression_coeffs = np.polyfit(x, y, 1)
        
        # Frissítjük a regressziós vonalat
        x_fit = np.linspace(min(x), max(x), 100)
        y_fit = np.polyval(self._regression_coeffs, x_fit)
        self._purple_regression_line.set_data(x_fit, y_fit)
        
        app_logger.info(f"Regresszió kiszámítva: m={self._regression_coeffs[0]:.3f}, b={self._regression_coeffs[1]:.3f}")
    
    def _update_purple_curves(self):
        """
        Frissíti a lila görbéket a regresszió alapján.
        """
        if self._regression_coeffs is None:
            return
        
        # Frissítjük a hiperpolarizációs görbét
        if 'purple_hyperpol' in self.curve_data:
            times = self.curve_data['purple_hyperpol']['times']
            if times is not None:
                new_data = np.polyval(self._regression_coeffs, times)
                self.curve_data['purple_hyperpol']['data'] = new_data
        
        # Frissítjük a depolarizációs görbét
        if 'purple_depol' in self.curve_data:
            times = self.curve_data['purple_depol']['times']
            if times is not None:
                new_data = np.polyval(self._regression_coeffs, times)
                self.curve_data['purple_depol']['data'] = new_data
        
        # Frissítjük a rajzot
        self.fig.canvas.draw_idle()
        app_logger.info("Lila görbék frissítve a regresszió alapján")
    
    def reset_purple_regression(self):
        """
        Visszaállítja a lila görbéket az eredeti állapotukba.
        """
        if self._original_hyperpol is not None and 'purple_hyperpol' in self.curve_data:
            self.curve_data['purple_hyperpol']['data'] = self._original_hyperpol.copy()
        
        if self._original_depol is not None and 'purple_depol' in self.curve_data:
            self.curve_data['purple_depol']['data'] = self._original_depol.copy()
        
        # Töröljük a regressziós vonalat
        if self._purple_regression_line is not None:
            self._purple_regression_line.set_data([], [])
        
        self._regression_coeffs = None
        self.fig.canvas.draw_idle()
        
        app_logger.info("Lila regresszió visszaállítva az eredeti állapotba") 