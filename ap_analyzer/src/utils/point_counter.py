import numpy as np
import matplotlib.patches as patches
from src.utils.logger import app_logger

class CurvePointTracker:
    """
    Enhanced point tracker that shows point information in the status bar.
    Always tracks points but only shows annotations when enabled.
    """
    
    def __init__(self, figure, ax, status_var=None):
        """
        Initialize the curve point tracker.
        
        Args:
            figure: Matplotlib figure
            ax: Matplotlib axes
            status_var: StringVar for status display
        """
        import os, time
        class_version = "1.0.1"  # Increment when modifying
        app_logger.debug(f"Initializing CurvePointTracker version {class_version}")
        
        self.fig = figure
        self.ax = ax
        self.status_var = status_var  # For status bar display
        self.annotations = {}
        self.curve_data = {
            'orange': {'data': None, 'times': None, 'visible': True},
            'blue': {'data': None, 'times': None, 'visible': True},
            'magenta': {'data': None, 'times': None, 'visible': True},
            'purple_hyperpol': {'data': None, 'times': None, 'visible': True},
            'purple_depol': {'data': None, 'times': None, 'visible': True}
        }
        
        # Use separate flags for different features:
        # - show_points remains for backward compatibility
        # - show_annotations controls visual annotations specifically
        self.show_points = False
        self.show_annotations = False
        
        self.last_cursor_pos = None
        self.current_time = 0
        self.current_value = 0
        
        # Display names for the curves
        self.curve_names = {
            'orange': 'Orange',
            'blue': 'Blue',
            'magenta': 'Magenta',
            'purple_hyperpol': 'Purple Hyperpol',
            'purple_depol': 'Purple Depol'
        }
        
        # Text position offsets for each curve to prevent overlap
        self.offsets = {
            'orange': (10, 10),
            'blue': (10, 30),
            'magenta': (10, 50),
            'purple_hyperpol': (10, 70),
            'purple_depol': (10, 90)
        }
        
        # Color mapping for annotation text
        self.colors = {
            'orange': 'orange',
            'blue': 'blue',
            'magenta': 'magenta',
            'purple_hyperpol': 'purple',
            'purple_depol': 'darkviolet'
        }
        
        # Known slice indices from logs for reference mapping
        self._hyperpol_slice = (1028, 1227)  # From logs
        self._depol_slice = (828, 1028)      # From logs
        
        # Setup event connections - make sure these are active
        self._connect()
        
    def _connect(self):
        """Connect to matplotlib event callbacks with improved error handling"""
        try:
            # Disconnect existing connections if they exist
            if hasattr(self, 'cid_move'):
                try:
                    self.fig.canvas.mpl_disconnect(self.cid_move)
                except:
                    pass
                
            if hasattr(self, 'cid_figure'):
                try:
                    self.fig.canvas.mpl_disconnect(self.cid_figure)
                except:
                    pass
                
            # Create new connections
            self.cid_move = self.fig.canvas.mpl_connect('motion_notify_event', self._on_mouse_move)
            self.cid_figure = self.fig.canvas.mpl_connect('figure_leave_event', self._on_figure_leave)
            
            # Force a canvas draw to ensure connections are active
            self.fig.canvas.draw_idle()
            
            app_logger.info("Point tracker event connections established")
            return True
            
        except Exception as e:
            app_logger.error(f"Failed to connect point tracker events: {str(e)}")
            return False
    
    def _on_mouse_move(self, event):
        """
        Handle mouse movement events - always track points but only show
        annotations if enabled.
        """
        # Quick exit if not over axes
        if not event.inaxes or event.inaxes != self.ax:
            if hasattr(self, 'status_var') and self.status_var:
                self.status_var.set("")
            self.clear_annotations()
            return
        
        # Store basic position info
        self.last_cursor_pos = (event.x, event.y)
        self.current_time = event.xdata  # In ms
        self.current_value = event.ydata  # In pA
        basic_info = f"Time: {self.current_time:.1f} ms, Current: {self.current_value:.1f} pA"
        
        # ALWAYS check for nearby points regardless of show_points flag
        found_point = False
        status_parts = [basic_info]
        
        # Check curves in priority order for better performance
        priority_curves = ['orange', 'purple_hyperpol', 'purple_depol', 'magenta', 'blue']
        
        for curve_type in priority_curves:
            # Skip if curve data isn't available
            if (self.curve_data[curve_type]['data'] is None or 
                len(self.curve_data[curve_type]['data']) == 0):
                continue
                
            # Try to find nearest point
            point_info = self._get_nearest_point(event.x, event.y, curve_type)
            if point_info is not None:
                idx, distance, x_val, y_val = point_info
                
                # Get corresponding orange point
                orange_idx = self._get_corresponding_orange_point(curve_type, idx)
                
                # Format for status bar (use 1-based indexing for display)
                point_text = f"{self.curve_names[curve_type]} Point: {idx+1}"
                if orange_idx is not None and curve_type != 'orange':
                    point_text += f" (Orange: {orange_idx+1})"
                
                status_parts.append(point_text)
                found_point = True
                
                # Only show annotations if that feature is enabled
                if hasattr(self, 'show_annotations') and self.show_annotations:
                    self._add_annotation(curve_type, idx, x_val, y_val, orange_idx)
                elif self.show_points:  # Backward compatibility
                    self._add_annotation(curve_type, idx, x_val, y_val, orange_idx)
                
                # For better performance, only show the first point found
                break
        
        # ALWAYS update status bar with point info (the key part is that this
        # happens regardless of show_points or show_annotations flags)
        if hasattr(self, 'status_var') and self.status_var:
            if found_point:
                self.status_var.set(" | ".join(status_parts))
            else:
                self.status_var.set(basic_info)
                # Clear annotations when no point is found
                self.clear_annotations()
    
    def _get_nearest_point(self, x, y, curve_type):
        """
        Find the nearest point on a curve to the cursor position with 
        optimized performance and adaptive thresholds.
        
        Args:
            x: Cursor x-position (in pixel coordinates)
            y: Cursor y-position (in pixel coordinates)
            curve_type: Type of curve ('orange', 'blue', etc.)
            
        Returns:
            Tuple of (index, distance, x_val, y_val) or None if no point found
        """
        # Quick exit if curve data is missing
        curve_data = self.curve_data[curve_type]
        if curve_data['data'] is None or len(curve_data['data']) == 0:
            return None
            
        data = curve_data['data']
        times = curve_data['times']
        
        if times is None or len(times) == 0:
            return None
        
        # Convert mouse coordinates to data coordinates 
        data_x, data_y = self.ax.transData.inverted().transform((x, y))
        
        # For time data that's in seconds but displayed in milliseconds
        # Check units based on axis label or data range
        x_label = self.ax.get_xlabel().lower()
        if 'ms' in x_label or np.max(times) < 10:  # Likely in seconds if max is small
            compare_x = data_x / 1000.0  # Convert ms to s for comparison
        else:
            compare_x = data_x  # Already in same units
        
        # Use vectorized operations for performance
        distances = np.abs(times - compare_x)
        idx = np.argmin(distances)
        
        # Calculate distances in both dimensions
        x_distance = distances[idx]
        y_distance = abs(data[idx] - data_y)
        
        # Get axis ranges for adaptive thresholds
        x_range = self.ax.get_xlim()
        y_range = self.ax.get_ylim()
        
        # Adaptive thresholds based on data and axis ranges
        # Use smaller of percentage-based or absolute thresholds
        x_threshold = min(0.02 * abs(x_range[1] - x_range[0]), 5) / 1000.0  # Convert ms to s, max 5ms
        y_threshold = max(0.05 * abs(y_range[1] - y_range[0]), 50)  # Min 50pA for usability
        
        # Accept the point if it's within threshold
        if x_distance <= x_threshold and y_distance <= y_threshold:
            return (idx, np.sqrt(x_distance**2 + y_distance**2), times[idx], data[idx])
        
        return None
    
    def _get_corresponding_orange_point(self, curve_type, point_idx):
        """
        Get the corresponding orange curve point index using known offsets
        from the logs.
        
        Args:
            curve_type: Type of curve
            point_idx: Index of the point on the curve
                
        Returns:
            Corresponding orange point index or None
        """
        # Quick exit if orange curve not available
        if 'orange' not in self.curve_data or self.curve_data['orange']['data'] is None:
            return None
            
        # Get orange curve length for bounds checking
        orange_len = len(self.curve_data['orange']['data'])
        
        if curve_type == 'blue' or curve_type == 'normalized':
            # Blue curve: offset by starting point (28)
            offset_idx = point_idx + 28
            if offset_idx < orange_len:
                return offset_idx
        
        elif curve_type == 'magenta' or curve_type == 'average':
            # Magenta curve: also offset by starting point (28)
            offset_idx = point_idx + 28
            if offset_idx < orange_len:
                return offset_idx
        
        elif curve_type == 'purple_hyperpol':
            # Use hardcoded slice from logs: 1028-1227
            if hasattr(self, '_hyperpol_slice'):
                start_idx = self._hyperpol_slice[0]
            else:
                start_idx = 1028  # Default from logs
                
            offset_idx = point_idx + start_idx
            if offset_idx < orange_len:
                return offset_idx
        
        elif curve_type == 'purple_depol':
            # Use hardcoded slice from logs: 828-1028
            if hasattr(self, '_depol_slice'):
                start_idx = self._depol_slice[0]
            else:
                start_idx = 828  # Default from logs
                
            offset_idx = point_idx + start_idx
            if offset_idx < orange_len:
                return offset_idx
        
        return None
    
    def _add_annotation(self, curve_type, idx, x_val, y_val, orange_idx=None):
        """Helper function to add or update a single annotation"""
        # Clear all existing annotations first
        self.clear_annotations()
        
        # Create annotation text (use 1-based indexing for display)
        curve_name = self.curve_names.get(curve_type, curve_type.capitalize())
        
        if orange_idx is not None and curve_type != 'orange':
            text = f"{curve_name} point: {idx+1} [Orange: {orange_idx+1}]"
        else:
            text = f"{curve_name} point: {idx+1}"
        
        # Create annotation with arrow
        self.annotations[curve_type] = self.ax.annotate(
            text, 
            xy=(x_val * 1000, y_val),  # Convert s to ms if needed
            xytext=self.offsets.get(curve_type, (10, 10)),
            textcoords='offset points',
            color=self.colors.get(curve_type, 'black'),
            bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8),
            arrowprops=dict(arrowstyle="->", color=self.colors.get(curve_type, 'black'))
        )
        
        # Redraw canvas - only needed for annotations
        self.ax.figure.canvas.draw_idle()
    
    def clear_annotations(self):
        """Remove all point annotations"""
        for ann in self.annotations.values():
            if ann is not None:
                try:
                    ann.remove()
                except:
                    pass
        self.annotations = {}
        
    def set_curve_data(self, curve_type, data, times=None, visible=True):
        """
        Set data for a specific curve type.
        
        Args:
            curve_type: Type of curve ('orange', 'blue', 'magenta', 'purple_hyperpol', 'purple_depol')
            data: Array of y-values
            times: Array of x-values (timestamps)
            visible: Whether the curve is visible
        """
        if curve_type in self.curve_data:
            if data is None:
                app_logger.debug(f"Ignoring None data for {curve_type}")
                return
                
            self.curve_data[curve_type]['data'] = data
            self.curve_data[curve_type]['times'] = times
            self.curve_data[curve_type]['visible'] = visible
            app_logger.debug(f"Set {curve_type} curve data with {len(data)} points, visible={visible}")
    
    def set_show_points(self, show):
        """
        Set whether to show point annotations (backwards compatibility).
        
        Args:
            show: Boolean flag to show or hide point annotations
        """
        self.show_points = show
        if hasattr(self, 'show_annotations'):
            self.show_annotations = show
            
        app_logger.debug(f"Point annotation display set to {show}")
        
        # Clear annotations if they are being hidden
        if not show:
            self.clear_annotations()

class PurpleIntegrationController:
    """Vezérli a lila görbék integrálási pontjait."""
    
    def __init__(self, figure, ax, processor=None):
        """Inicializálja az integrálási pont vezérlőt."""
        app_logger.info("PurpleIntegrationController inicializálása kezdődik")
        try:
            self.fig = figure
            self.ax = ax
            self.processor = processor
            self.is_active = False
            self.integration_points = {
                'hyperpol': None,
                'depol': None
            }
            self.annotations = {}
            
            # Eseménykezelők csatlakoztatása
            self._connect()
            app_logger.info("PurpleIntegrationController sikeresen inicializálva")
            
        except Exception as e:
            app_logger.error(f"Hiba a PurpleIntegrationController inicializálásakor: {str(e)}")
            raise
        
    def _connect(self):
        """Csatlakoztatja az eseménykezelőket."""
        try:
            app_logger.debug("Eseménykezelők csatlakoztatása kezdődik")
            self.cid_press = self.fig.canvas.mpl_connect('button_press_event', self._on_press)
            self.cid_release = self.fig.canvas.mpl_connect('button_release_event', self._on_release)
            self.cid_motion = self.fig.canvas.mpl_connect('motion_notify_event', self._on_motion)
            app_logger.info("Eseménykezelők sikeresen csatlakoztatva")
        except Exception as e:
            app_logger.error(f"Hiba az eseménykezelők csatlakoztatásakor: {str(e)}")
            raise

    def _disconnect(self):
        """Leválasztja az eseménykezelőket."""
        if hasattr(self, 'cid_press'):
            self.fig.canvas.mpl_disconnect(self.cid_press)
        if hasattr(self, 'cid_release'):
            self.fig.canvas.mpl_disconnect(self.cid_release)
        if hasattr(self, 'cid_motion'):
            self.fig.canvas.mpl_disconnect(self.cid_motion)
            
    def _on_press(self, event):
        """Egérgomb lenyomás kezelése."""
        if not self.is_active or not event.inaxes:
            return
            
        # Ellenőrizzük, hogy a lila görbék tartományában vagyunk-e
        if self._is_in_purple_range(event.xdata):
            self.start_point = event.xdata
            self._create_selection_rectangle(event)
            
    def _on_release(self, event):
        """Egérgomb felengedés kezelése."""
        if not self.is_active or not hasattr(self, 'start_point'):
            return
            
        if event.inaxes:
            end_point = event.xdata
            self._update_integration_points(self.start_point, end_point)
            
        self._remove_selection_rectangle()
        delattr(self, 'start_point')
        
    def _on_motion(self, event):
        """Egér mozgás kezelése."""
        if not self.is_active or not hasattr(self, 'start_point') or not event.inaxes:
            return
            
        self._update_selection_rectangle(event)
        
    def _is_in_purple_range(self, x):
        """Ellenőrzi, hogy az x koordináta a lila görbék tartományában van-e."""
        if not hasattr(self.processor, '_hyperpol_slice') or not hasattr(self.processor, '_depol_slice'):
            return False
            
        hyperpol_start = self.processor._hyperpol_slice[0]
        depol_end = self.processor._depol_slice[1]
        
        return hyperpol_start <= x <= depol_end
        
    def _create_selection_rectangle(self, event):
        """Létrehozza a kijelölési téglalapot."""
        self.rect = patches.Rectangle(
            (self.start_point, self.ax.get_ylim()[0]),
            0,
            self.ax.get_ylim()[1] - self.ax.get_ylim()[0],
            fill=True,
            alpha=0.3,
            color='gray'
        )
        self.ax.add_patch(self.rect)
        self.fig.canvas.draw_idle()
        
    def _update_selection_rectangle(self, event):
        """Frissíti a kijelölési téglalapot."""
        if hasattr(self, 'rect'):
            width = event.xdata - self.start_point
            self.rect.set_width(width)
            self.fig.canvas.draw_idle()
            
    def _remove_selection_rectangle(self):
        """Eltávolítja a kijelölési téglalapot."""
        if hasattr(self, 'rect'):
            self.rect.remove()
            delattr(self, 'rect')
            self.fig.canvas.draw_idle()
            
    def _update_integration_points(self, start, end):
        """Frissíti az integrálási pontokat."""
        if start > end:
            start, end = end, start
            
        # Meghatározzuk, hogy melyik tartományba esik a kijelölés
        if hasattr(self.processor, '_hyperpol_slice') and hasattr(self.processor, '_depol_slice'):
            hyperpol_start = self.processor._hyperpol_slice[0]
            depol_end = self.processor._depol_slice[1]
            
            if start >= hyperpol_start and end <= depol_end:
                # Meghatározzuk, hogy hyperpol vagy depol tartományba esik
                if start < (hyperpol_start + depol_end) / 2:
                    self.integration_points['hyperpol'] = start
                else:
                    self.integration_points['depol'] = start
                    
                # Frissítjük a processzort
                if self.processor:
                    self.processor.set_custom_integration_points(self.integration_points)
                    
                # Frissítjük az annotációkat
                self._update_annotations()
                
    def _update_annotations(self):
        """Frissíti az annotációkat."""
        # Töröljük a régi annotációkat
        for ann in self.annotations.values():
            if ann:
                ann.remove()
        self.annotations.clear()
        
        # Új annotációk hozzáadása
        for point_type, point in self.integration_points.items():
            if point is not None:
                text = f"{point_type} start: {point:.2f}"
                self.annotations[point_type] = self.ax.annotate(
                    text,
                    xy=(point, self.ax.get_ylim()[1]),
                    xytext=(10, 10),
                    textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
                    arrowprops=dict(arrowstyle='->')
                )
                
        self.fig.canvas.draw_idle()
        
    def reset(self):
        """Visszaállítja az integrálási pontokat."""
        self.integration_points = {
            'hyperpol': None,
            'depol': None
        }
        
        # Töröljük az annotációkat
        for ann in self.annotations.values():
            if ann:
                ann.remove()
        self.annotations.clear()
        
        # Frissítjük a processzort
        if self.processor:
            self.processor.set_custom_integration_points(None)
            
        self.fig.canvas.draw_idle()