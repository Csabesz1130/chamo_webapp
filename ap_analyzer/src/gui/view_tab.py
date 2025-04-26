import tkinter as tk
from tkinter import ttk
from src.utils.logger import app_logger

class ViewTab:
    def __init__(self, parent, callback):
        """
        Initialize the view control tab.
        
        Args:
            parent: Parent widget
            callback: Function to call when view settings change
        """
        self.parent = parent
        self.update_callback = callback
        
        # Create main frame
        self.frame = ttk.LabelFrame(parent, text="View Controls")
        self.frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Initialize variables
        self.init_variables()
        
        # Create controls
        self.setup_display_controls()
        self.setup_interval_controls()
        self.setup_axis_controls()
        
        app_logger.debug("View tab initialized")

    def init_variables(self):
        """Initialize control variables"""
        # Display options
        self.show_original = tk.BooleanVar(value=True)
        self.show_filtered = tk.BooleanVar(value=True)
        self.show_grid = tk.BooleanVar(value=True)
        
        # Interval selection
        self.use_interval = tk.BooleanVar(value=False)
        self.t_min = tk.DoubleVar(value=0)
        self.t_max = tk.DoubleVar(value=1)
        self.t_min_str = tk.StringVar(value="0.00")
        self.t_max_str = tk.StringVar(value="1.00")
        
        # Axis limits
        self.use_custom_ylim = tk.BooleanVar(value=False)
        self.y_min = tk.DoubleVar(value=0)
        self.y_max = tk.DoubleVar(value=1)
        self.y_min_str = tk.StringVar(value="0.00")
        self.y_max_str = tk.StringVar(value="1.00")

    def setup_display_controls(self):
        """Setup display control options"""
        display_frame = ttk.LabelFrame(self.frame, text="Display Options")
        display_frame.pack(fill='x', padx=5, pady=5)
        
        # Signal visibility controls
        ttk.Checkbutton(display_frame, text="Show Original Signal",
                       variable=self.show_original,
                       command=self.on_view_change).pack(pady=2)
        
        ttk.Checkbutton(display_frame, text="Show Filtered Signal",
                       variable=self.show_filtered,
                       command=self.on_view_change).pack(pady=2)
        
        ttk.Checkbutton(display_frame, text="Show Grid",
                       variable=self.show_grid,
                       command=self.on_view_change).pack(pady=2)

    def setup_interval_controls(self):
        """Setup time interval controls"""
        interval_frame = ttk.LabelFrame(self.frame, text="Time Interval")
        interval_frame.pack(fill='x', padx=5, pady=5)
        
        # Enable/disable interval selection
        ttk.Checkbutton(interval_frame, text="Use Custom Interval",
                       variable=self.use_interval,
                       command=self.on_interval_toggle).pack(pady=2)
        
        # Min time control
        min_frame = ttk.Frame(interval_frame)
        min_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(min_frame, text="Start Time:").pack(side='left')
        self.t_min_scale = ttk.Scale(min_frame, from_=0, to=1,
                                   variable=self.t_min,
                                   orient='horizontal',
                                   command=self.update_time_labels)
        self.t_min_scale.pack(side='left', fill='x', expand=True)
        ttk.Label(min_frame, textvariable=self.t_min_str,
                 width=8).pack(side='right')
        
        # Max time control
        max_frame = ttk.Frame(interval_frame)
        max_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(max_frame, text="End Time:").pack(side='left')
        self.t_max_scale = ttk.Scale(max_frame, from_=0, to=1,
                                   variable=self.t_max,
                                   orient='horizontal',
                                   command=self.update_time_labels)
        self.t_max_scale.pack(side='left', fill='x', expand=True)
        ttk.Label(max_frame, textvariable=self.t_max_str,
                 width=8).pack(side='right')

    def setup_axis_controls(self):
        """Setup axis limit controls"""
        axis_frame = ttk.LabelFrame(self.frame, text="Axis Limits")
        axis_frame.pack(fill='x', padx=5, pady=5)
        
        # Enable/disable custom Y limits
        ttk.Checkbutton(axis_frame, text="Use Custom Y-axis Limits",
                       variable=self.use_custom_ylim,
                       command=self.on_ylim_toggle).pack(pady=2)
        
        # Y-axis minimum control
        y_min_frame = ttk.Frame(axis_frame)
        y_min_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(y_min_frame, text="Y Minimum:").pack(side='left')
        self.y_min_scale = ttk.Scale(y_min_frame, from_=-10000, to=10000,
                                   variable=self.y_min,
                                   orient='horizontal',
                                   command=self.update_ylim_labels)
        self.y_min_scale.pack(side='left', fill='x', expand=True)
        ttk.Label(y_min_frame, textvariable=self.y_min_str,
                 width=8).pack(side='right')
        
        # Y-axis maximum control
        y_max_frame = ttk.Frame(axis_frame)
        y_max_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(y_max_frame, text="Y Maximum:").pack(side='left')
        self.y_max_scale = ttk.Scale(y_max_frame, from_=-10000, to=10000,
                                   variable=self.y_max,
                                   orient='horizontal',
                                   command=self.update_ylim_labels)
        self.y_max_scale.pack(side='left', fill='x', expand=True)
        ttk.Label(y_max_frame, textvariable=self.y_max_str,
                 width=8).pack(side='right')
        
        # Add reset button
        ttk.Button(axis_frame, text="Reset View",
                  command=self.reset_view).pack(pady=5)

    def update_limits(self, t_min=None, t_max=None, v_min=None, v_max=None):
        """Update the range of sliders based on data"""
        try:
            if t_min is not None and t_max is not None:
                # Update time sliders
                self.t_min_scale.configure(from_=t_min, to=t_max)
                self.t_max_scale.configure(from_=t_min, to=t_max)
                self.t_min.set(t_min)
                self.t_max.set(t_max)
                self.update_time_labels()
            
            if v_min is not None and v_max is not None:
                # Update y-axis sliders
                padding = (v_max - v_min) * 0.1
                self.y_min_scale.configure(from_=v_min-padding, to=v_max+padding)
                self.y_max_scale.configure(from_=v_min-padding, to=v_max+padding)
                self.y_min.set(v_min)
                self.y_max.set(v_max)
                self.update_ylim_labels()
            
            app_logger.debug("View limits updated successfully")
            
        except Exception as e:
            app_logger.error(f"Error updating view limits: {str(e)}")

    def update_time_labels(self, *args):
        """Update time interval display labels"""
        try:
            self.t_min_str.set(f"{self.t_min.get():.2f}")
            self.t_max_str.set(f"{self.t_max.get():.2f}")
            self.on_view_change()
        except Exception as e:
            app_logger.error(f"Error updating time labels: {str(e)}")

    def update_ylim_labels(self, *args):
        """Update y-axis limit display labels"""
        try:
            self.y_min_str.set(f"{self.y_min.get():.2f}")
            self.y_max_str.set(f"{self.y_max.get():.2f}")
            self.on_view_change()
        except Exception as e:
            app_logger.error(f"Error updating y-axis labels: {str(e)}")

    def on_interval_toggle(self):
        """Handle interval selection toggle"""
        enabled = self.use_interval.get()
        
        # Update control states
        state = 'normal' if enabled else 'disabled'
        self.t_min_scale.configure(state=state)
        self.t_max_scale.configure(state=state)
        
        self.on_view_change()

    def on_ylim_toggle(self):
        """Handle y-axis limits toggle"""
        enabled = self.use_custom_ylim.get()
        
        # Update control states
        state = 'normal' if enabled else 'disabled'
        self.y_min_scale.configure(state=state)
        self.y_max_scale.configure(state=state)
        
        self.on_view_change()

    def reset_view(self):
        """Reset view to default settings"""
        self.use_interval.set(False)
        self.use_custom_ylim.set(False)
        self.show_original.set(True)
        self.show_filtered.set(True)
        self.show_grid.set(True)
        
        # Reset scales to their configured limits
        self.t_min.set(self.t_min_scale.cget('from'))
        self.t_max.set(self.t_max_scale.cget('to'))
        self.y_min.set(self.y_min_scale.cget('from'))
        self.y_max.set(self.y_max_scale.cget('to'))
        
        # Update labels and view
        self.update_time_labels()
        self.update_ylim_labels()
        self.on_view_change()

    def get_view_params(self):
        """Get current view parameters"""
        params = {
            'show_original': self.show_original.get(),
            'show_filtered': self.show_filtered.get(),
            'show_grid': self.show_grid.get()
        }
        
        if self.use_interval.get():
            params.update({
                'use_interval': True,
                't_min': self.t_min.get(),
                't_max': self.t_max.get()
            })
        
        if self.use_custom_ylim.get():
            params.update({
                'use_custom_ylim': True,
                'y_min': self.y_min.get(),
                'y_max': self.y_max.get()
            })
            
        return params

    def on_view_change(self, *args):
        """Callback for view parameter changes"""
        try:
            app_logger.debug("View parameters changed")
            self.update_callback(self.get_view_params())
        except Exception as e:
            app_logger.error(f"Error in view change callback: {str(e)}")