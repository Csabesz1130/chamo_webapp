# src/gui/filter_tab.py

import tkinter as tk
from tkinter import ttk
from src.utils.logger import app_logger

class FilterTab:
    def __init__(self, parent, callback):
        """
        Initialize the filter tab with dynamic filter controls.
        
        Args:
            parent: Parent tkinter widget
            callback: Function to call when filters change
        """
        self.parent = parent
        self.update_callback = callback
        
        # Create main frame
        self.frame = ttk.LabelFrame(parent, text="Filter Controls", padding="5 5 5 5")
        self.frame.pack(fill='x', padx=5, pady=5)
        
        # Initialize filter variables
        self.init_filter_vars()
        
        # Create filter controls
        self.setup_savgol_controls()
        self.setup_wavelet_controls()
        self.setup_butterworth_controls()
        self.setup_extract_add_controls()

    def init_filter_vars(self):
        """Initialize all filter-related variables"""
        # Savitzky-Golay filter variables
        self.use_savgol = tk.BooleanVar(value=False)
        self.savgol_window = tk.IntVar(value=51)
        self.savgol_order = tk.IntVar(value=3)
        
        
        # Butterworth filter variables
        self.use_butterworth = tk.BooleanVar(value=False)
        self.butter_cutoff = tk.DoubleVar(value=0.1)
        self.butter_order = tk.IntVar(value=5)

        # Wavelet filter variables
        self.use_wavelet = tk.BooleanVar(value=False)
        self.wavelet_level = tk.IntVar(value=4)
        
        # Extract-Add filter variables
        self.use_extract_add = tk.BooleanVar(value=False)
        self.extract_prominence = tk.DoubleVar(value=200)
        self.extract_width_min = tk.IntVar(value=1)
        self.extract_width_max = tk.IntVar(value=50)

    def setup_savgol_controls(self):
        """Setup Savitzky-Golay filter controls"""
        savgol_frame = ttk.LabelFrame(self.frame, text="Savitzky-Golay Filter")
        savgol_frame.pack(fill='x', padx=5, pady=5)
        
        # Enable checkbox
        ttk.Checkbutton(savgol_frame, text="Enable", 
                       variable=self.use_savgol,
                       command=self.on_filter_change).pack(pady=2)
        
        # Window length control
        window_frame = ttk.Frame(savgol_frame)
        window_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(window_frame, text="Window Length:").pack(side='left')
        ttk.Scale(window_frame, from_=5, to=101, variable=self.savgol_window,
                 orient='horizontal', command=lambda _: self.on_filter_change()
                 ).pack(side='left', fill='x', expand=True)
        ttk.Label(window_frame, textvariable=self.savgol_window).pack(side='right')
        
        # Polynomial order control
        order_frame = ttk.Frame(savgol_frame)
        order_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(order_frame, text="Polynomial Order:").pack(side='left')
        ttk.Scale(order_frame, from_=2, to=5, variable=self.savgol_order,
                 orient='horizontal', command=lambda _: self.on_filter_change()
                 ).pack(side='left', fill='x', expand=True)
        ttk.Label(order_frame, textvariable=self.savgol_order).pack(side='right')

    def setup_fft_controls(self):
        """Setup FFT filter controls"""
        fft_frame = ttk.LabelFrame(self.frame, text="FFT Filter")
        fft_frame.pack(fill='x', padx=5, pady=5)
        
        # Enable checkbox
        ttk.Checkbutton(fft_frame, text="Enable",
                       variable=self.use_fft,
                       command=self.on_filter_change).pack(pady=2)
        
        # Threshold control
        threshold_frame = ttk.Frame(fft_frame)
        threshold_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(threshold_frame, text="Threshold:").pack(side='left')
        ttk.Scale(threshold_frame, from_=0.01, to=1.0, variable=self.fft_threshold,
                 orient='horizontal', command=lambda _: self.on_filter_change()
                 ).pack(side='left', fill='x', expand=True)
        ttk.Label(threshold_frame, textvariable=self.fft_threshold).pack(side='right')
        
        # Frequency band controls
        band_frame = ttk.Frame(fft_frame)
        band_frame.pack(fill='x', padx=5, pady=2)
        ttk.Checkbutton(band_frame, text="Use Frequency Band",
                       variable=self.use_freq_band,
                       command=self.on_filter_change).pack(side='left')
        
        # Min/Max frequency controls
        freq_frame = ttk.Frame(fft_frame)
        freq_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(freq_frame, text="Freq Range (Hz):").pack(side='left')
        ttk.Entry(freq_frame, textvariable=self.min_freq, width=8).pack(side='left')
        ttk.Label(freq_frame, text=" - ").pack(side='left')
        ttk.Entry(freq_frame, textvariable=self.max_freq, width=8).pack(side='left')

    def setup_butterworth_controls(self):
        """Setup Butterworth filter controls"""
        butter_frame = ttk.LabelFrame(self.frame, text="Butterworth Filter")
        butter_frame.pack(fill='x', padx=5, pady=5)
        
        # Enable checkbox
        ttk.Checkbutton(butter_frame, text="Enable",
                       variable=self.use_butterworth,
                       command=self.on_filter_change).pack(pady=2)
        
        # Cutoff frequency control
        cutoff_frame = ttk.Frame(butter_frame)
        cutoff_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(cutoff_frame, text="Cutoff Frequency:").pack(side='left')
        ttk.Scale(cutoff_frame, from_=0.01, to=1.0, variable=self.butter_cutoff,
                 orient='horizontal', command=lambda _: self.on_filter_change()
                 ).pack(side='left', fill='x', expand=True)
        ttk.Label(cutoff_frame, textvariable=self.butter_cutoff).pack(side='right')
        
        # Order control
        order_frame = ttk.Frame(butter_frame)
        order_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(order_frame, text="Order:").pack(side='left')
        ttk.Scale(order_frame, from_=1, to=10, variable=self.butter_order,
                 orient='horizontal', command=lambda _: self.on_filter_change()
                 ).pack(side='left', fill='x', expand=True)
        ttk.Label(order_frame, textvariable=self.butter_order).pack(side='right')

    def setup_extract_add_controls(self):
        """Setup Extract-Add filter controls"""
        extract_frame = ttk.LabelFrame(self.frame, text="Extract-Add Filter")
        extract_frame.pack(fill='x', padx=5, pady=5)
        
        # Enable checkbox
        ttk.Checkbutton(extract_frame, text="Enable",
                       variable=self.use_extract_add,
                       command=self.on_filter_change).pack(pady=2)
        
        # Prominence threshold
        prom_frame = ttk.Frame(extract_frame)
        prom_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(prom_frame, text="Prominence:").pack(side='left')
        ttk.Scale(prom_frame, from_=50, to=500, variable=self.extract_prominence,
                 orient='horizontal', command=lambda _: self.on_filter_change()
                 ).pack(side='left', fill='x', expand=True)
        ttk.Label(prom_frame, textvariable=self.extract_prominence).pack(side='right')
        
        # Width range controls
        width_frame = ttk.Frame(extract_frame)
        width_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(width_frame, text="Width Range:").pack(side='left')
        ttk.Scale(width_frame, from_=1, to=20, variable=self.extract_width_min,
                 orient='horizontal', command=lambda _: self.on_filter_change()
                 ).pack(side='left', fill='x', expand=True)
        ttk.Label(width_frame, text="to").pack(side='left')
        ttk.Scale(width_frame, from_=21, to=100, variable=self.extract_width_max,
                 orient='horizontal', command=lambda _: self.on_filter_change()
                 ).pack(side='left', fill='x', expand=True)

    def get_active_filters(self):
        """Get the currently active filters and their parameters"""
        filters = {}
        
        # Savitzky-Golay filter parameters
        if self.use_savgol.get():
            filters['savgol_params'] = {
                'window_length': self.savgol_window.get(),
                'polyorder': self.savgol_order.get()
            }
        
        # Wavelet filter parameters
        if self.use_wavelet.get():
            filters['wavelet_params'] = {
                'wavelet': self.wavelet_type.get(),
                'level': self.wavelet_level.get(),
                'threshold_mode': self.threshold_mode.get()
            }
        
        # Butterworth filter parameters
        if self.use_butterworth.get():
            filters['butter_params'] = {
                'cutoff': float(self.butter_cutoff.get()),
                'fs': 1000.0,  # Default sampling frequency
                'order': int(self.butter_order.get())
            }
        
        # Extract-Add filter parameters
        if self.use_extract_add.get():
            filters['extract_add_params'] = {
                'prominence_threshold': float(self.extract_prominence.get()),
                'width_range': (
                    int(self.extract_width_min.get()),
                    int(self.extract_width_max.get())
                )
            }
        
        app_logger.debug(f"Active filters configuration: {filters}")
        return filters

    def setup_wavelet_controls(self):
        """Setup wavelet filter controls"""
        wavelet_frame = ttk.LabelFrame(self.frame, text="Wavelet Filter")
        wavelet_frame.pack(fill='x', padx=5, pady=5)
        
        # Enable checkbox
        ttk.Checkbutton(wavelet_frame, text="Enable",
                    variable=self.use_wavelet,
                    command=self.on_filter_change).pack(pady=2)
        
        # Wavelet type selection
        type_frame = ttk.Frame(wavelet_frame)
        type_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(type_frame, text="Wavelet Type:").pack(side='left')
        wavelet_types = ['db4', 'sym4', 'coif3']
        self.wavelet_type = ttk.Combobox(type_frame, values=wavelet_types, width=10)
        self.wavelet_type.set('db4')
        self.wavelet_type.pack(side='right')
        
        # Decomposition level
        level_frame = ttk.Frame(wavelet_frame)
        level_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(level_frame, text="Level:").pack(side='left')
        ttk.Scale(level_frame, from_=1, to=10, variable=self.wavelet_level,
                orient='horizontal', command=lambda _: self.on_filter_change()
                ).pack(side='left', fill='x', expand=True)
        ttk.Label(level_frame, textvariable=self.wavelet_level).pack(side='right')
        
        # Threshold mode
        mode_frame = ttk.Frame(wavelet_frame)
        mode_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(mode_frame, text="Threshold:").pack(side='left')
        modes = ['soft', 'hard']
        self.threshold_mode = ttk.Combobox(mode_frame, values=modes, width=10)
        self.threshold_mode.set('soft')
        self.threshold_mode.pack(side='right')

    def on_filter_change(self, *args):
        """Called when any filter parameter changes"""
        app_logger.debug("Filter parameters changed")
        try:
            # Get current filter settings and update plot
            self.update_callback(self.get_active_filters())
        except Exception as e:
            app_logger.error(f"Error updating filters: {str(e)}")

    def reset_filters(self):
        """Reset all filters to default values"""
        self.use_savgol.set(False)
        self.use_fft.set(False)
        self.use_butterworth.set(False)
        self.use_extract_add.set(False)
        
        # Reset parameters to defaults
        self.savgol_window.set(51)
        self.savgol_order.set(3)
        self.fft_threshold.set(0.2)
        self.min_freq.set("0")
        self.max_freq.set("500")
        self.butter_cutoff.set(0.1)
        self.butter_order.set(5)
        self.extract_prominence.set(200)
        self.extract_width_min.set(1)
        self.extract_width_max.set(50)
        
        # Update plot
        self.on_filter_change()