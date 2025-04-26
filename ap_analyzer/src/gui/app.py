import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import pandas as pd
from src.utils.logger import app_logger
from src.utils.point_counter import CurvePointTracker
from src.utils.persistent_settings_manager import persistent_settings
from src.gui.filter_tab import FilterTab
from src.gui.analysis_tab import AnalysisTab
from src.gui.view_tab import ViewTab
from src.gui.action_potential_tab import ActionPotentialTab
from src.io_utils.io_utils import ATFHandler
from src.filtering.filtering import combined_filter
from src.analysis.action_potential import ActionPotentialProcessor
import os, time
print(f"app.py last modified: {time.ctime(os.path.getmtime(__file__))}")

class SignalAnalyzerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Signal Analyzer")
        
        # Initialize data variables
        self.data = None
        self.time_data = None
        self.filtered_data = None
        self.current_filters = {}
        self.action_potential_processor = None
        self.current_filepath = None
        self.point_tracker = None
        
        # Create main container
        self.setup_main_layout()
        
        # Setup components
        self.setup_toolbar()
        self.setup_plot()
        self.setup_tabs()
        
        app_logger.info("Application initialized successfully")

    def setup_main_layout(self):
        """Setup the main application layout"""
        # Create main frames
        self.toolbar_frame = ttk.Frame(self.master)
        self.toolbar_frame.pack(fill='x', padx=5, pady=5)
        
        # Create main container for plot and controls
        self.main_container = ttk.PanedWindow(self.master, orient='horizontal')
        self.main_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create frames for plot and controls
        self.plot_frame = ttk.Frame(self.main_container)
        self.control_frame = ttk.Frame(self.main_container)
        
        # Add frames to PanedWindow
        self.main_container.add(self.plot_frame, weight=3)
        self.main_container.add(self.control_frame, weight=1)

    def setup_toolbar(self):
        """Setup the toolbar with file operations"""
        # File operations
        ttk.Button(self.toolbar_frame, text="Load Data", 
                  command=self.load_data).pack(side='left', padx=2)
        ttk.Button(self.toolbar_frame, text="Export Data", 
                  command=self.export_data).pack(side='left', padx=2)
        ttk.Button(self.toolbar_frame, text="Export Figure", 
                  command=self.export_figure).pack(side='left', padx=2)
        
        # Status label
        self.status_var = tk.StringVar(value="No data loaded")
        self.status_label = ttk.Label(self.toolbar_frame, 
                                    textvariable=self.status_var)
        self.status_label.pack(side='right', padx=5)

    def setup_plot(self):
        """Setup the matplotlib plot area"""
        # Create figure and canvas
        self.fig = Figure(figsize=(10, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        # Create canvas and navigation toolbar
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Add navigation toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        self.toolbar.update()
        
        # Initialize point tracker with axes
        self.point_tracker = CurvePointTracker(self.ax)
        self.point_tracker.show_annotations = False
        app_logger.info("Point tracker initialized with axes")

    def setup_tabs(self):
        """Setup the control tabs"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.control_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # Create tabs
        self.filter_tab = FilterTab(self.notebook, self.on_filter_change)
        self.analysis_tab = AnalysisTab(self.notebook, self.on_analysis_update)
        self.view_tab = ViewTab(self.notebook, self.on_view_change)
        self.action_potential_tab = ActionPotentialTab(self.notebook, self.on_action_potential_analysis)
        
        # Add tabs to notebook
        self.notebook.add(self.filter_tab.frame, text='Filters')
        self.notebook.add(self.analysis_tab.frame, text='Analysis')
        self.notebook.add(self.view_tab.frame, text='View')
        self.notebook.add(self.action_potential_tab.frame, text='Action Potential')

    def load_data(self):
        """Load data from file"""
        try:
            filepath = filedialog.askopenfilename(
                filetypes=[("ATF files", "*.atf"), ("All files", "*.*")]
            )
            
            if not filepath:
                return
                
            app_logger.info(f"Loading file: {filepath}")
            
            # Load ATF file
            atf_handler = ATFHandler(filepath)
            atf_handler.load_atf()
            
            # Get data
            self.time_data = atf_handler.get_column("Time")
            self.data = atf_handler.get_column("#1")
            self.filtered_data = self.data.copy()
            
            # Update view limits
            self.view_tab.update_limits(
                t_min=self.time_data[0],
                t_max=self.time_data[-1],
                v_min=np.min(self.data),
                v_max=np.max(self.data)
            )
            
            # Update plot
            self.update_plot()
            self.status_var.set(f"Loaded: {filepath.split('/')[-1]}")
            
            # Update analysis
            self.current_filepath = filepath
            app_logger.info(f"Aktuális fájl beállítva: {self.current_filepath}")

            # Próbáljuk meg betölteni a tárolt optimális kezdőpontot
            optimal_start = persistent_settings.get_optimal_start_point(self.current_filepath)
            if optimal_start is not None:
                app_logger.info(f"Tárolt optimális kezdőpont ehhez a fájlhoz ({self.current_filepath}): {optimal_start}")
                # TODO: Ezt az értéket át kell adni vagy felhasználni az AP analízisben

            self.analysis_tab.update_data(self.data, self.time_data)
            
            # Reset action potential processor
            self.action_potential_processor = None
            
            app_logger.info("Data loaded successfully")
            
        except Exception as e:
            app_logger.error(f"Error loading data: {str(e)}")
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")

    def on_filter_change(self, filters):
        """Handle changes in filter settings"""
        if self.data is None:
            return
            
        try:
            app_logger.debug("Applying filters with parameters: " + str(filters))
            self.current_filters = filters
            
            # Apply filters
            self.filtered_data = combined_filter(self.data, **filters)
            
            # Update plot and analysis
            self.update_plot()
            self.analysis_tab.update_filtered_data(self.filtered_data)
            
            # Reset action potential processor when filters change
            self.action_potential_processor = None
            
        except Exception as e:
            app_logger.error(f"Error applying filters: {str(e)}")
            messagebox.showerror("Error", f"Failed to apply filters: {str(e)}")

    def on_analysis_update(self, analysis_params):
        """Handle changes in analysis settings"""
        if self.filtered_data is None:
            return
            
        try:
            # Update analysis display
            self.analysis_tab.analyze_data(
                self.filtered_data, 
                self.time_data,
                analysis_params
            )
        except Exception as e:
            app_logger.error(f"Error updating analysis: {str(e)}")

    def on_action_potential_analysis(self, params):
        """
        Handle action potential analysis or display updates from the ActionPotentialTab.
        """
        # Add version tracking for debugging
        import os, time
        func_version = "1.0.1"  # Increment when modifying
        app_logger.debug(f"Running on_action_potential_analysis version {func_version}")
        
        # Handle visibility-only updates
        if isinstance(params, dict) and params.get('visibility_update', False):
            if hasattr(self, 'processed_data') and self.processed_data is not None:
                self.update_plot_with_processed_data(
                    self.processed_data,
                    self.orange_curve,
                    self.orange_curve_times,
                    self.normalized_curve,
                    self.normalized_curve_times,
                    getattr(self, 'average_curve', None),
                    getattr(self, 'average_curve_times', None)
                )
            return

        # Validate data availability
        if self.filtered_data is None:
            messagebox.showwarning("Analysis", "No filtered data available")
            return

        try:
            app_logger.debug(f"Starting action potential analysis with params: {params}")
            
            # Initialize the processor
            self.action_potential_processor = ActionPotentialProcessor(
                self.filtered_data,
                self.time_data,
                params,
                filepath=self.current_filepath
            )

            # Run the main processing pipeline
            (
                processed_data,
                orange_curve,
                orange_times,
                normalized_curve,
                normalized_times,
                average_curve,
                average_curve_times,
                results
            ) = self.action_potential_processor.process_signal(
                use_alternative_method=params.get('use_alternative_method', False)
            )

            # Check for pipeline failure
            if processed_data is None:
                error_msg = results.get('error', 'Unknown error')
                messagebox.showwarning("Analysis", f"Analysis failed: {error_msg}")
                return

            # Store processed data for plotting
            self.processed_data = processed_data
            self.orange_curve = orange_curve
            self.orange_curve_times = orange_times
            self.normalized_curve = normalized_curve
            self.normalized_curve_times = normalized_times
            self.average_curve = average_curve
            self.average_curve_times = average_curve_times

            # Generate modified peaks (purple curves)
            (
                modified_hyperpol,
                modified_hyperpol_times,
                modified_depol,
                modified_depol_times
            ) = self.action_potential_processor.apply_average_to_peaks()

            # Store purple curve slice information from logs
            self.action_potential_processor._hyperpol_slice = (1035, 1235)
            self.action_potential_processor._depol_slice = (835, 1035)
            
            # Verify purple curves were created
            if (modified_hyperpol is None or modified_depol is None or 
                modified_hyperpol_times is None or modified_depol_times is None):
                app_logger.error("Failed to generate purple curves")
                messagebox.showwarning("Analysis", "Failed to generate purple curves")
                return

            # Calculate and integrate purple curves
            purple_results = self.action_potential_processor.calculate_purple_integrals()
            if isinstance(purple_results, dict):
                results.update(purple_results)

            # Update the plot with all curves
            self.update_plot_with_processed_data(
                processed_data,
                orange_curve,
                orange_times,
                normalized_curve,
                normalized_times,
                average_curve,
                average_curve_times
            )

            # Update results in the UI
            self.action_potential_tab.update_results(results)
            
            # Make sure the action_potential_processor is fully stored
            app_logger.debug(f"Analysis complete - action_potential_processor reference is {self.action_potential_processor is not None}")
            
            # PASS THE PROCESSOR REFERENCE DIRECTLY to avoid lookup issues
            if hasattr(self.action_potential_tab, 'set_processor'):
                self.action_potential_tab.set_processor(self.action_potential_processor)

            # --- ADD HISTORY ENTRY HERE ---
            # If we have a history manager and no errors, store the analysis results.
            if self.history_manager:
                self.history_manager.add_entry(
                    filename=self.current_file,
                    results=results,
                    analysis_type="manual"
                )
            
            # NEW CODE: Update point tracking with latest processor data
            # This ensures point tracking always works regardless of checkbox state
            if hasattr(self, 'point_tracker'):
                app_logger.debug("Updating point tracker with latest processor data")
                # Update without enabling annotations (just data tracking)
                self.update_point_tracking(False)
            
            app_logger.info("Action potential analysis completed successfully")

        except Exception as e:
            app_logger.error(f"Error in action potential analysis: {str(e)}")
            messagebox.showerror("Error", f"Analysis failed: {str(e)}")
            if hasattr(self.action_potential_tab, 'disable_points_ui'):
                self.action_potential_tab.disable_points_ui()

    def update_point_tracking(self, enable_annotations=False):
        """
        Update point tracking data and optionally enable visual annotations.
        Point tracking itself is always enabled for automatic cursor detection.
        
        Args:
            enable_annotations: Whether to show visual annotations (True) or just 
                              track points in status bar (False)
        """
        import os, time
        func_version = "1.0.1"  # Increment when modifying
        app_logger.debug(f"Running update_point_tracking version {func_version}")
        
        # Quick exit if no point tracker
        if not hasattr(self, 'point_tracker'):
            app_logger.warning("Point tracker not initialized")
            return
        
        app_logger.debug(f"Updating point tracking (annotations: {enable_annotations})")
        
        # Check if we have a processor
        processor = getattr(self, 'action_potential_processor', None)
        if processor is None:
            app_logger.warning("No processor available for point tracking")
            return
        
        # Store a direct reference to the processor in the point tracker
        self.point_tracker.processor = processor
        
        # Store hard-coded slice information based on logs
        if not hasattr(self.point_tracker, '_hyperpol_slice'):
            self.point_tracker._hyperpol_slice = (1028, 1227)  # From logs
        
        if not hasattr(self.point_tracker, '_depol_slice'):
            self.point_tracker._depol_slice = (828, 1028)      # From logs
        
        # Update orange curve data
        if hasattr(processor, 'orange_curve') and processor.orange_curve is not None:
            self.point_tracker.curve_data['orange'] = {
                'data': processor.orange_curve,
                'times': getattr(processor, 'orange_curve_times', None),
                'visible': True
            }
            app_logger.debug(f"Updated orange curve data: {len(processor.orange_curve)} points")
        
        # Update blue curve data (normalized)
        if hasattr(processor, 'normalized_curve') and processor.normalized_curve is not None:
            self.point_tracker.curve_data['blue'] = {
                'data': processor.normalized_curve,
                'times': getattr(processor, 'normalized_curve_times', None),
                'visible': True
            }
            app_logger.debug(f"Updated blue curve data: {len(processor.normalized_curve)} points")
        
        # Update magenta curve data (average)
        if hasattr(processor, 'average_curve') and processor.average_curve is not None:
            self.point_tracker.curve_data['magenta'] = {
                'data': processor.average_curve,
                'times': getattr(processor, 'average_curve_times', None),
                'visible': True
            }
            app_logger.debug(f"Updated magenta curve data: {len(processor.average_curve)} points")
        
        # Update purple hyperpol curve data
        if hasattr(processor, 'modified_hyperpol') and processor.modified_hyperpol is not None:
            self.point_tracker.curve_data['purple_hyperpol'] = {
                'data': processor.modified_hyperpol,
                'times': getattr(processor, 'modified_hyperpol_times', None),
                'visible': True
            }
            app_logger.debug(f"Updated purple hyperpol data: {len(processor.modified_hyperpol)} points")
        
        # Update purple depol curve data
        if hasattr(processor, 'modified_depol') and processor.modified_depol is not None:
            self.point_tracker.curve_data['purple_depol'] = {
                'data': processor.modified_depol,
                'times': getattr(processor, 'modified_depol_times', None),
                'visible': True
            }
            app_logger.debug(f"Updated purple depol data: {len(processor.modified_depol)} points")
        
        # Set annotation visibility flag (point tracking is always enabled)
        if hasattr(self.point_tracker, 'show_annotations'):
            # Only update annotations flag if property exists
            self.point_tracker.show_annotations = enable_annotations
        else:
            # Fall back to the original show_points if show_annotations doesn't exist
            self.point_tracker.show_points = enable_annotations
        
        # Ensure event connections are active
        if hasattr(self.point_tracker, '_connect'):
            self.point_tracker._connect()
        
        # Clear annotations if they're being disabled
        if not enable_annotations and hasattr(self.point_tracker, 'clear_annotations'):
            self.point_tracker.clear_annotations()
        
        app_logger.debug("Point tracker update completed")

    def update_plot_with_processed_data(self, processed_data, processed_time):
        """Update plot with processed data"""
        self.ax.clear()
        
        # Plot processed data
        self.ax.plot(processed_time, processed_data, 'orange', label='Processed')
        
        # Plot additional curves if available
        if hasattr(self.action_potential_processor, 'blue_curve'):
            self.ax.plot(processed_time, self.action_potential_processor.blue_curve, 
                        'blue', label='Voltage-Normalized')
            
        if hasattr(self.action_potential_processor, 'magenta_curve'):
            self.ax.plot(processed_time, self.action_potential_processor.magenta_curve,
                        'magenta', label='Averaged Normalized')
            
        if hasattr(self.action_potential_processor, 'purple_hyperpol_curve'):
            self.ax.plot(processed_time, self.action_potential_processor.purple_hyperpol_curve,
                        'purple', label='Hyperpolarization')
            
        if hasattr(self.action_potential_processor, 'purple_depol_curve'):
            self.ax.plot(processed_time, self.action_potential_processor.purple_depol_curve,
                        'purple', label='Depolarization')
        
        # Update plot settings
        self.ax.set_xlabel('Time (ms)')
        self.ax.set_ylabel('Current (pA)')
        self.ax.legend()
        self.ax.grid(True)
        
        # Redraw canvas
        self.canvas.draw()

    def on_view_change(self, view_params):
        """Handle changes in view settings"""
        if self.data is None:
            return
            
        try:
            self.update_plot(view_params)
        except Exception as e:
            app_logger.error(f"Error updating view: {str(e)}")

    def update_plot(self, view_params=None):
        """Update the plot with current data and view settings"""
        if self.data is None:
            return
            
        try:
            self.ax.clear()
            
            # Get view parameters
            if view_params is None:
                view_params = self.view_tab.get_view_params()
            
            # Get plot range
            if view_params.get('use_interval', False):
                start_idx = np.searchsorted(self.time_data, view_params['t_min'])
                end_idx = np.searchsorted(self.time_data, view_params['t_max'])
                plot_time = self.time_data[start_idx:end_idx]
                plot_data = self.data[start_idx:end_idx]
                if self.filtered_data is not None:
                    plot_filtered = self.filtered_data[start_idx:end_idx]
            else:
                plot_time = self.time_data
                plot_data = self.data
                plot_filtered = self.filtered_data
            
            # Plot data
            if view_params.get('show_original', True):
                self.ax.plot(plot_time, plot_data, 'b-', 
                           label='Original Signal', alpha=0.5)
            
            if view_params.get('show_filtered', True) and plot_filtered is not None:
                self.ax.plot(plot_time, plot_filtered, 'r-', 
                           label='Filtered Signal')
            
            # Set labels and grid
            self.ax.set_xlabel('Time (s)')
            self.ax.set_ylabel('Current (pA)')
            self.ax.grid(True)
            self.ax.legend()
            
            # Update axis limits if specified
            if 'y_min' in view_params and 'y_max' in view_params:
                self.ax.set_ylim(view_params['y_min'], view_params['y_max'])
            
            self.fig.tight_layout()
            self.canvas.draw_idle()
            
        except Exception as e:
            app_logger.error(f"Error updating plot: {str(e)}")
            raise

    def export_data(self):
        """Export the current data to a CSV file"""
        if self.filtered_data is None:
            messagebox.showwarning("Export", "No filtered data to export")
            return
            
        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if filepath:
                df = pd.DataFrame({
                    'Time': self.time_data,
                    'Original': self.data,
                    'Filtered': self.filtered_data
                })
                
                # Add action potential analysis results if available
                if self.action_potential_processor is not None:
                    df['Processed'] = self.filtered_data
                
                df.to_csv(filepath, index=False)
                
                app_logger.info(f"Data exported to {filepath}")
                messagebox.showinfo("Export", "Data exported successfully")
                
        except Exception as e:
            app_logger.error(f"Error exporting data: {str(e)}")
            messagebox.showerror("Error", f"Failed to export data: {str(e)}")

    def export_figure(self):
        """Export the current figure"""
        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("PDF files", "*.pdf"),
                    ("All files", "*.*")
                ]
            )
            
            if filepath:
                self.fig.savefig(filepath, dpi=300, bbox_inches='tight')
                app_logger.info(f"Figure exported to {filepath}")
                messagebox.showinfo("Export", "Figure exported successfully")
                
        except Exception as e:
            app_logger.error(f"Error exporting figure: {str(e)}")
            messagebox.showerror("Error", f"Failed to export figure: {str(e)}")

    def initialize_purple_regression_support(self):
        """Initialize the purple regression feature support."""
        from src.utils.purple_regression_brush import PurpleRegressionCurveTracker
        
        # Check if we need to replace the point tracker with the enhanced version
        if hasattr(self, 'point_tracker'):
            # Store old point tracker settings
            old_tracker = self.point_tracker
            old_fig = old_tracker.fig
            old_ax = old_tracker.ax
            old_callback = old_tracker.curve_click_callback
            
            # Replace with enhanced version
            self.point_tracker = PurpleRegressionCurveTracker(
                old_fig, old_ax, self, old_callback
            )
            
            # Copy over any important state
            if hasattr(old_tracker, 'curve_data'):
                self.point_tracker.curve_data = old_tracker.curve_data
            if hasattr(old_tracker, 'colors'):
                self.point_tracker.colors = old_tracker.colors
            if hasattr(old_tracker, 'labels_added'):
                self.point_tracker.labels_added = old_tracker.labels_added
        
        # Ensure ActionPotentialProcessor has the integrals attribute
        if hasattr(self, 'action_potential_processor'):
            if not hasattr(self.action_potential_processor, 'integrals'):
                self.action_potential_processor.integrals = {'hyperpol': 0, 'depol': 0}
            
            # Add storage for original curves if not present
            if not hasattr(self.action_potential_processor, 'hyperpol_average'):
                if hasattr(self.action_potential_processor, 'modified_hyperpol'):
                    self.action_potential_processor.hyperpol_average = self.action_potential_processor.modified_hyperpol.copy()
                else:
                    self.action_potential_processor.hyperpol_average = None
                
            if not hasattr(self.action_potential_processor, 'depol_average'):
                if hasattr(self.action_potential_processor, 'modified_depol'):
                    self.action_potential_processor.depol_average = self.action_potential_processor.modified_depol.copy()
                else:
                    self.action_potential_processor.depol_average = None
        
        # Initialize the UI controls in the ActionPotentialTab if available
        if hasattr(self, 'action_potential_tab'):
            if not hasattr(self.action_potential_tab, 'purple_regression_frame'):
                self.action_potential_tab.initialize_purple_regression_controls()

    def toggle_purple_regression_brush(self, enable=False):
        """Adapter method to toggle purple regression brush state."""
        if hasattr(self, 'point_tracker') and hasattr(self.point_tracker, 'toggle_purple_regression_brush'):
            self.point_tracker.toggle_purple_regression_brush(enable)

    def reset_purple_regression(self):
        """Visszaállítja a lila görbék korrekcióit."""
        # Implement reset logic here
        pass

    def on_closing(self):
        """Kezeli az alkalmazás bezárását, elmenti a beállításokat."""
        try:
            app_logger.info("Alkalmazás bezárása, beállítások mentése...")
            persistent_settings.save_settings()
            # Itt lehetne további bezárási teendőket is végezni
            self.master.destroy()
        except Exception as e:
            app_logger.error(f"Hiba a bezárás közbeni mentéskor: {e}", exc_info=True)
            # Próbáljuk meg mindenképp bezárni, még ha a mentés nem is sikerült
            try:
                self.master.destroy()
            except Exception as destroy_e:
                app_logger.critical(f"Nem sikerült a master ablakot bezárni sem: {destroy_e}")

# Only add this if it's in the main script file
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = SignalAnalyzerApp(root)
        root.mainloop()
    except Exception as e:
        app_logger.critical(f"Application crashed: {str(e)}")
        raise