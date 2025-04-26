import tkinter as tk
from tkinter import ttk, messagebox
from src.utils.logger import app_logger

class ActionPotentialTab:
    def __init__(self, parent, callback):
        """
        Initialize the action potential analysis tab.
        
        Args:
            parent: Parent widget
            callback: Function to call when analysis settings change
        """
        self.parent = parent
        self.update_callback = callback
        
        # Create main frame
        self.frame = ttk.LabelFrame(parent, text="Action Potential Analysis")
        self.frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Initialize variables
        self.init_variables()
        
        # Create controls
        self.setup_parameter_controls()
        self.setup_analysis_controls()
        self.setup_point_tracking_controls()
        self.initialize_purple_regression_controls()
        self.initialize_integration_point_controls()
        
        app_logger.debug("Action potential analysis tab initialized")

    def init_variables(self):
        """Initialize control variables with validation"""
        try:
            # Analysis parameters with validation
            self.n_cycles = tk.IntVar(value=2)
            self.t1 = tk.DoubleVar(value=100.0)
            self.t2 = tk.DoubleVar(value=100.0)
            self.V0 = tk.DoubleVar(value=-80.0)
            self.V1 = tk.DoubleVar(value=100.0)
            self.V2 = tk.DoubleVar(value=10.0)
            
            # Point tracking controls
            self.show_points = tk.BooleanVar(value=False)
            self.show_integration = tk.BooleanVar(value=False)
            self.show_regression = tk.BooleanVar(value=False)
            
            # Results display
            self.integral_value = tk.StringVar(value="No analysis performed")
            self.status_text = tk.StringVar(value="Ready")
            
            # Add validation traces
            self.n_cycles.trace_add("write", self.validate_n_cycles)
            self.t1.trace_add("write", self.validate_time_constant)
            self.t2.trace_add("write", self.validate_time_constant)
            
            app_logger.debug("Variables initialized successfully")
            
        except Exception as e:
            app_logger.error(f"Error initializing variables: {str(e)}")
            raise

    def validate_n_cycles(self, *args):
        """Validate number of cycles"""
        try:
            value = self.n_cycles.get()
            if value < 1:
                self.n_cycles.set(1)
                messagebox.showwarning("Validation", "Number of cycles must be at least 1")
            elif value > 10:
                self.n_cycles.set(10)
                messagebox.showwarning("Validation", "Maximum number of cycles is 10")
        except tk.TclError:
            # Invalid integer - reset to default
            self.n_cycles.set(2)

    def validate_time_constant(self, *args):
        """Validate time constants"""
        try:
            t1 = self.t1.get()
            t2 = self.t2.get()
            if t1 <= 0:
                self.t1.set(1.0)
                messagebox.showwarning("Validation", "Time constants must be positive")
            if t2 <= 0:
                self.t2.set(1.0)
                messagebox.showwarning("Validation", "Time constants must be positive")
        except tk.TclError:
            # Invalid float - reset to defaults
            self.t1.set(100.0)
            self.t2.set(100.0)

    def setup_parameter_controls(self):
        """Setup parameter input controls"""
        try:
            param_frame = ttk.LabelFrame(self.frame, text="Parameters")
            param_frame.pack(fill='x', padx=5, pady=5)
            
            # Number of cycles
            cycle_frame = ttk.Frame(param_frame)
            cycle_frame.pack(fill='x', padx=5, pady=2)
            ttk.Label(cycle_frame, text="Number of Cycles:").pack(side='left')
            ttk.Entry(cycle_frame, textvariable=self.n_cycles,
                     width=10).pack(side='right')
            
            # Time constants
            time_frame = ttk.Frame(param_frame)
            time_frame.pack(fill='x', padx=5, pady=2)
            ttk.Label(time_frame, text="t1 (ms):").pack(side='left')
            ttk.Entry(time_frame, textvariable=self.t1,
                     width=10).pack(side='left', padx=5)
            ttk.Label(time_frame, text="t2 (ms):").pack(side='left')
            ttk.Entry(time_frame, textvariable=self.t2,
                     width=10).pack(side='right')
            
            # Voltage levels
            volt_frame = ttk.Frame(param_frame)
            volt_frame.pack(fill='x', padx=5, pady=2)
            ttk.Label(volt_frame, text="V0 (mV):").pack(side='left')
            ttk.Entry(volt_frame, textvariable=self.V0,
                     width=10).pack(side='left', padx=5)
            ttk.Label(volt_frame, text="V1 (mV):").pack(side='left')
            ttk.Entry(volt_frame, textvariable=self.V1,
                     width=10).pack(side='left', padx=5)
            ttk.Label(volt_frame, text="V2 (mV):").pack(side='left')
            ttk.Entry(volt_frame, textvariable=self.V2,
                     width=10).pack(side='right')
            
            # Add tooltips
            self.create_tooltip(cycle_frame, "Number of action potential cycles to analyze")
            self.create_tooltip(time_frame, "Time constants for repolarization (t1) and depolarization (t2)")
            self.create_tooltip(volt_frame, "Voltage levels for baseline (V0), repolarization (V1), and depolarization (V2)")
            
        except Exception as e:
            app_logger.error(f"Error setting up parameter controls: {str(e)}")
            raise

    def setup_analysis_controls(self):
        """Setup analysis controls and results display"""
        try:
            analysis_frame = ttk.LabelFrame(self.frame, text="Analysis")
            analysis_frame.pack(fill='x', padx=5, pady=5)
            
            # Analysis button with progress indication
            self.analyze_button = ttk.Button(analysis_frame, 
                                           text="Analyze Signal",
                                           command=self.analyze_signal)
            self.analyze_button.pack(pady=5)
            
            # Progress bar
            self.progress_var = tk.DoubleVar()
            self.progress = ttk.Progressbar(analysis_frame, 
                                          variable=self.progress_var,
                                          mode='determinate')
            self.progress.pack(fill='x', padx=5, pady=5)
            
            # Results display
            results_frame = ttk.LabelFrame(analysis_frame, text="Results")
            results_frame.pack(fill='x', padx=5, pady=5)
            
            # Integral value display
            ttk.Label(results_frame, text="Integral Value:").pack(side='left')
            ttk.Label(results_frame, textvariable=self.integral_value,
                     width=20).pack(side='left', padx=5)
            
            # Status display
            status_frame = ttk.Frame(self.frame)
            status_frame.pack(fill='x', padx=5, pady=5)
            ttk.Label(status_frame, textvariable=self.status_text).pack(side='left')
            
        except Exception as e:
            app_logger.error(f"Error setting up analysis controls: {str(e)}")
            raise

    def setup_point_tracking_controls(self):
        """Setup controls for point tracking features"""
        try:
            # Create frame for point tracking controls
            tracking_frame = ttk.LabelFrame(self.frame, text="Point Tracking")
            tracking_frame.pack(fill='x', padx=5, pady=5)
            
            # Show points checkbox
            points_check = ttk.Checkbutton(tracking_frame, 
                                         text="Enable Points & Regression",
                                         variable=self.show_points,
                                         command=self.on_show_points_change)
            points_check.pack(fill='x', padx=5, pady=2)
            
            # Integration range checkbox
            integration_check = ttk.Checkbutton(tracking_frame,
                                              text="Show Integration Range",
                                              variable=self.show_integration,
                                              command=self.on_integration_change)
            integration_check.pack(fill='x', padx=5, pady=2)
            
            # Regression line checkbox
            regression_check = ttk.Checkbutton(tracking_frame,
                                             text="Show Regression Line",
                                             variable=self.show_regression,
                                             command=self.on_regression_change)
            regression_check.pack(fill='x', padx=5, pady=2)
            
            app_logger.debug("Point tracking controls setup completed")
            
        except Exception as e:
            app_logger.error(f"Error setting up point tracking controls: {str(e)}")
            raise

    def initialize_purple_regression_controls(self):
        """Initialize the purple regression controls."""
        # Create a frame for purple regression controls
        self.purple_regression_frame = ttk.LabelFrame(self, text="Purple curve regression")
        self.purple_regression_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        # Add controls
        self.purple_regression_enable = tk.BooleanVar(value=False)
        self.purple_regression_check = ttk.Checkbutton(
            self.purple_regression_frame,
            text="Allow purple curve regression",
            variable=self.purple_regression_enable,
            command=self.on_purple_regression_toggle
        )
        self.purple_regression_check.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.purple_regression_reset = ttk.Button(
            self.purple_regression_frame,
            text="Reset regression",
            command=self.on_purple_regression_reset
        )
        self.purple_regression_reset.grid(row=0, column=1, padx=5, pady=5, sticky="e")

    def initialize_integration_point_controls(self):
        """Inicializálja az integrálási pont vezérlőket."""
        app_logger.info("Integrálási pont vezérlők inicializálása kezdődik")
        try:
            # Importáljuk a vezérlőt a helyes útvonalról
            from src.analysis.purple_integration_control import PurpleIntegrationController
            app_logger.debug("PurpleIntegrationController modul sikeresen importálva")
            
            # Ellenőrizzük, hogy van-e főablak és ábra
            if not hasattr(self.master, 'fig') or not hasattr(self.master, 'ax'):
                app_logger.error("Nincs elérhető ábra az integrálási pont vezérlők inicializálásához")
                return
            
            app_logger.debug("Ábra és tengely elérhető, inicializálás folytatása")
            
            # Ellenőrizzük, hogy van-e jobb oldali keret
            if not hasattr(self, 'right_frame'):
                app_logger.debug("Jobb oldali keret létrehozása")
                self.right_frame = ttk.Frame(self.frame)
                self.right_frame.pack(side='right', fill='y', padx=5)
            
            # Hozzáadjuk a vezérlőket a jobb oldali kerethez
            self.integration_frame = ttk.LabelFrame(self.right_frame, text="Integrálási pontok")
            self.integration_frame.pack(fill=tk.X, padx=5, pady=5)
            app_logger.debug("Integrálási pont keret létrehozva")
            
            # Vezérlő gombok
            self.toggle_integration_button = ttk.Button(
                self.integration_frame,
                text="Integrálási pontok",
                command=self.toggle_integration_point_controls
            )
            self.toggle_integration_button.pack(fill=tk.X, padx=5, pady=2)
            
            self.reset_integration_button = ttk.Button(
                self.integration_frame,
                text="Visszaállítás",
                command=self.reset_integration_points
            )
            self.reset_integration_button.pack(fill=tk.X, padx=5, pady=2)
            app_logger.debug("Vezérlő gombok létrehozva")
            
            # Létrehozzuk az integrálási pont vezérlőt
            self.integration_controller = PurpleIntegrationController(
                self.master.fig,
                self.master.ax,
                self.master.processor
            )
            app_logger.debug("PurpleIntegrationController példány létrehozva")
            
            app_logger.info("Integrálási pont vezérlők sikeresen inicializálva")
            
        except ImportError as e:
            app_logger.error(f"Modul importálási hiba: {str(e)}")
            raise
        except Exception as e:
            app_logger.error(f"Hiba az integrálási pont vezérlők inicializálásakor: {str(e)}")
            raise

    def toggle_integration_point_controls(self):
        """Váltja az integrálási pont vezérlők láthatóságát."""
        app_logger.debug("Integrálási pont vezérlők váltása kezdődik")
        try:
            if hasattr(self, 'integration_controller'):
                current_state = self.integration_controller.is_active
                self.integration_controller.is_active = not current_state
                self.toggle_integration_button.config(
                    text="Integrálási pontok" if current_state else "Kikapcsolás"
                )
                app_logger.info(f"Integrálási pont vezérlők {'bekapcsolva' if not current_state else 'kikapcsolva'}")
                self.master.canvas.draw_idle()
            else:
                app_logger.warning("Nincs inicializált integrálási pont vezérlő")
        except Exception as e:
            app_logger.error(f"Hiba az integrálási pont vezérlők váltásakor: {str(e)}")

    def reset_integration_points(self):
        """Visszaállítja az integrálási pontokat az alapértelmezett értékekre."""
        app_logger.debug("Integrálási pontok visszaállítása kezdődik")
        try:
            if hasattr(self, 'integration_controller'):
                self.integration_controller.reset()
                app_logger.info("Integrálási pontok visszaállítva")
                self.master.canvas.draw_idle()
            else:
                app_logger.warning("Nincs inicializált integrálási pont vezérlő")
        except Exception as e:
            app_logger.error(f"Hiba az integrálási pontok visszaállításakor: {str(e)}")

    def on_show_points_change(self):
        """
        Handle changes to show_points checkbox - only affects annotations
        and visual elements, not basic point tracking.
        """
        import os, time
        func_version = "1.0.1"  # Increment when modifying
        app_logger.debug(f"Running on_show_points_change version {func_version}")
        
        # Get current state
        show_points = self.show_points.get()
        app_logger.info(f"Show points toggled: {show_points}")
        
        # Get main app reference
        app = self.parent.master
        
        # Send update with integration ranges
        ranges = {}
        if hasattr(self, 'range_manager'):
            ranges = self.range_manager.get_integration_ranges()
            # Enable/disable range sliders
            self.range_manager.enable_controls(show_points)
        
        # Build params for update
        params = {
            'integration_ranges': ranges,
            'show_points': show_points,  # This now only controls visual elements
            'visibility_update': True
        }
        
        # Call update callback
        if self.update_callback:
            self.update_callback(params)
        
        # Set display mode to points when enabled
        if show_points:
            if hasattr(self, 'modified_display_mode'):
                self.modified_display_mode.set("all_points")
            if hasattr(self, 'average_display_mode'):
                self.average_display_mode.set("all_points")
        
        # Toggle annotation display only (point tracking remains active)
        if hasattr(app, 'point_tracker'):
            # Use new property if available
            if hasattr(app.point_tracker, 'show_annotations'):
                app.point_tracker.show_annotations = show_points
                app_logger.debug(f"Set point_tracker.show_annotations to {show_points}")
            else:
                # Fall back to original property
                app.point_tracker.show_points = show_points
                app_logger.debug(f"Set point_tracker.show_points to {show_points}")
            
            # Clear annotations if disabled
            if not show_points:
                app.point_tracker.clear_annotations()
        
        # Update point tracking settings
        if hasattr(app, 'update_point_tracking'):
            # Only controls annotation visibility now
            app.update_point_tracking(show_points)
            app_logger.debug(f"Called app.update_point_tracking({show_points})")
        
        # Toggle span selectors
        if hasattr(app, 'toggle_span_selectors'):
            app.toggle_span_selectors(show_points)
            app_logger.debug(f"Toggled span selectors: {show_points}")

    def on_integration_change(self):
        """Handle changes to integration range visibility"""
        try:
            # Update integration range visibility
            self.update_callback({
                'show_integration': self.show_integration.get()
            })
            
            app_logger.debug(f"Integration range visibility set to {self.show_integration.get()}")
            
        except Exception as e:
            app_logger.error(f"Error updating integration range visibility: {str(e)}")
            raise

    def on_regression_change(self):
        """Handle changes to regression line visibility"""
        try:
            # Update regression line visibility
            self.update_callback({
                'show_regression': self.show_regression.get()
            })
            
            app_logger.debug(f"Regression line visibility set to {self.show_regression.get()}")
            
        except Exception as e:
            app_logger.error(f"Error updating regression line visibility: {str(e)}")
            raise

    def on_purple_regression_toggle(self):
        """Handle purple regression toggle."""
        if hasattr(self.master, 'toggle_purple_regression_brush'):
            self.master.toggle_purple_regression_brush(self.purple_regression_enable.get())
            app_logger.info(f"Lila regressziós ecset {'engedélyezve' if self.purple_regression_enable.get() else 'letiltva'}")

    def on_purple_regression_reset(self):
        """Handle purple regression reset."""
        if hasattr(self.master, 'reset_purple_regression'):
            self.master.reset_purple_regression()
            app_logger.info("Lila regresszió visszaállítva")

    def create_tooltip(self, widget, text):
        """Create tooltip for a widget"""
        def enter(event):
            self.tooltip = tk.Toplevel()
            self.tooltip.wm_overrideredirect(True)
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 20
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = ttk.Label(self.tooltip, text=text, 
                            justify='left', background="#ffffe0", 
                            relief='solid', borderwidth=1)
            label.pack()
            
        def leave(event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()
                
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

    def get_parameters(self):
        """Get current analysis parameters with validation"""
        try:
            params = {
                'n_cycles': self.n_cycles.get(),
                't1': self.t1.get(),
                't2': self.t2.get(),
                'V0': self.V0.get(),
                'V1': self.V1.get(),
                'V2': self.V2.get()
            }
            
            # Validate parameters
            if params['n_cycles'] < 1:
                raise ValueError("Number of cycles must be positive")
            if params['t1'] <= 0 or params['t2'] <= 0:
                raise ValueError("Time constants must be positive")
            
            app_logger.debug(f"Parameters validated: {params}")
            return params
            
        except Exception as e:
            app_logger.error(f"Error getting parameters: {str(e)}")
            raise

    def analyze_signal(self):
        """Perform signal analysis with current parameters"""
        try:
            # Disable button during analysis
            self.analyze_button.state(['disabled'])
            self.status_text.set("Analyzing...")
            self.progress_var.set(0)
            
            # Get parameters
            params = self.get_parameters()
            
            # Update progress
            self.progress_var.set(50)
            
            # Call callback with parameters
            self.update_callback(params)
            
            # Reset UI
            self.progress_var.set(100)
            self.status_text.set("Analysis complete")
            self.analyze_button.state(['!disabled'])
            
        except Exception as e:
            app_logger.error(f"Error in signal analysis: {str(e)}")
            self.status_text.set(f"Error: {str(e)}")
            self.integral_value.set("Error")
            self.analyze_button.state(['!disabled'])
            messagebox.showerror("Analysis Error", str(e))

    def update_results(self, results):
        """Update displayed results with compact formatting."""
        try:
            if not results:
                self.integral_value.set("No analysis results")
                self.status_text.set("Analysis produced no results")
                return

            # Format with shorter labels and reduced precision
            display_text = [
                "Analysis Results",
                "---------------",
                f"{'Integral:':<10} {float(results['integral_value'].split()[0]):.1e} C",
                f"{'Capacitance:':<10} {float(results['capacitance_uF_cm2'].split()[0]):.4f} µF",
                "",
                "Raw Values",
                "---------------"
            ]
            
            # Format raw values with minimal precision
            if 'raw_values' in results:
                raw = results['raw_values']
                display_text.extend([
                    f"{'Charge:':<10} {raw['charge_C']:.1e} C",
                    f"{'Cap.:':<10} {raw['capacitance_F']:.1e} F",
                    f"{'Area:':<10} {raw['area_cm2']:.1e} cm²"
                ])
            
            # Join and display
            self.integral_value.set('\n'.join(display_text))
            self.status_text.set("Analysis complete")
            
        except Exception as e:
            app_logger.error(f"Error updating results: {str(e)}")
            self.integral_value.set("Error displaying results")
            self.status_text.set("Error in display")
            raise

    def reset(self):
        """Reset the tab to initial state"""
        try:
            self.n_cycles.set(2)
            self.t1.set(100.0)
            self.t2.set(100.0)
            self.V0.set(-80.0)
            self.V1.set(100.0)
            self.V2.set(10.0)
            self.integral_value.set("No analysis performed")
            self.status_text.set("Ready")
            self.progress_var.set(0)
            self.analyze_button.state(['!disabled'])
            
        except Exception as e:
            app_logger.error(f"Error resetting tab: {str(e)}")
            raise