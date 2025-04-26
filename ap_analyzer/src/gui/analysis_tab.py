import tkinter as tk
from tkinter import ttk
import numpy as np
from scipy.signal import find_peaks
from src.utils.logger import app_logger

class AnalysisTab:
    def __init__(self, parent, callback):
        """
        Initialize the analysis control tab.
        
        Args:
            parent: Parent widget
            callback: Function to call when analysis settings change
        """
        self.parent = parent
        self.update_callback = callback
        
        # Initialize data holders
        self.data = None
        self.time_data = None
        self.filtered_data = None
        
        # Create main frame
        self.frame = ttk.LabelFrame(parent, text="Analysis Controls")
        self.frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Initialize variables
        self.init_variables()
        
        # Create controls
        self.setup_statistics_display()
        self.setup_peak_detection()
        self.setup_event_analysis()
        
        app_logger.debug("Analysis tab initialized")

    def init_variables(self):
        """Initialize control variables"""
        # Peak detection parameters
        self.detect_peaks = tk.BooleanVar(value=False)
        self.peak_prominence = tk.DoubleVar(value=200)
        self.peak_distance = tk.IntVar(value=50)
        self.peak_width = tk.DoubleVar(value=10)
        self.peak_height = tk.DoubleVar(value=100)
        
        # Event analysis parameters
        self.analyze_events = tk.BooleanVar(value=False)
        self.event_threshold = tk.DoubleVar(value=100)
        self.min_event_duration = tk.DoubleVar(value=0.1)
        
        # Statistics display
        self.stats_text = tk.StringVar(value="No data loaded")
        self.peak_stats_text = tk.StringVar(value="No peaks detected")
        self.event_stats_text = tk.StringVar(value="No events detected")

    def setup_statistics_display(self):
        """Setup the statistics display section"""
        stats_frame = ttk.LabelFrame(self.frame, text="Signal Statistics")
        stats_frame.pack(fill='x', padx=5, pady=5)
        
        # Basic statistics display
        basic_stats = ttk.Label(stats_frame, textvariable=self.stats_text,
                              wraplength=300, justify='left')
        basic_stats.pack(fill='x', padx=5, pady=5)
        
        # Add refresh button
        ttk.Button(stats_frame, text="Refresh Statistics",
                  command=self.update_statistics).pack(pady=5)

    def setup_peak_detection(self):
        """Setup peak detection controls"""
        peak_frame = ttk.LabelFrame(self.frame, text="Peak Detection")
        peak_frame.pack(fill='x', padx=5, pady=5)
        
        # Enable peak detection
        ttk.Checkbutton(peak_frame, text="Enable Peak Detection",
                       variable=self.detect_peaks,
                       command=self.on_peak_settings_change).pack(pady=2)
        
        # Peak prominence control
        prom_frame = ttk.Frame(peak_frame)
        prom_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(prom_frame, text="Prominence:").pack(side='left')
        ttk.Scale(prom_frame, from_=0, to=1000, variable=self.peak_prominence,
                 orient='horizontal', command=self.on_peak_settings_change
                 ).pack(side='left', fill='x', expand=True)
        ttk.Label(prom_frame, textvariable=self.peak_prominence).pack(side='right')
        
        # Peak distance control
        dist_frame = ttk.Frame(peak_frame)
        dist_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(dist_frame, text="Min Distance:").pack(side='left')
        ttk.Scale(dist_frame, from_=1, to=200, variable=self.peak_distance,
                 orient='horizontal', command=self.on_peak_settings_change
                 ).pack(side='left', fill='x', expand=True)
        ttk.Label(dist_frame, textvariable=self.peak_distance).pack(side='right')
        
        # Peak width control
        width_frame = ttk.Frame(peak_frame)
        width_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(width_frame, text="Min Width:").pack(side='left')
        ttk.Scale(width_frame, from_=1, to=50, variable=self.peak_width,
                 orient='horizontal', command=self.on_peak_settings_change
                 ).pack(side='left', fill='x', expand=True)
        ttk.Label(width_frame, textvariable=self.peak_width).pack(side='right')
        
        # Peak height control
        height_frame = ttk.Frame(peak_frame)
        height_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(height_frame, text="Min Height:").pack(side='left')
        ttk.Scale(height_frame, from_=0, to=1000, variable=self.peak_height,
                 orient='horizontal', command=self.on_peak_settings_change
                 ).pack(side='left', fill='x', expand=True)
        ttk.Label(height_frame, textvariable=self.peak_height).pack(side='right')
        
        # Peak statistics display
        ttk.Label(peak_frame, textvariable=self.peak_stats_text,
                 wraplength=300, justify='left').pack(fill='x', padx=5, pady=5)

    def setup_event_analysis(self):
        """Setup event analysis controls"""
        event_frame = ttk.LabelFrame(self.frame, text="Event Analysis")
        event_frame.pack(fill='x', padx=5, pady=5)
        
        # Enable event analysis
        ttk.Checkbutton(event_frame, text="Enable Event Analysis",
                       variable=self.analyze_events,
                       command=self.on_event_settings_change).pack(pady=2)
        
        # Event threshold control
        thresh_frame = ttk.Frame(event_frame)
        thresh_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(thresh_frame, text="Threshold:").pack(side='left')
        ttk.Scale(thresh_frame, from_=0, to=1000, variable=self.event_threshold,
                 orient='horizontal', command=self.on_event_settings_change
                 ).pack(side='left', fill='x', expand=True)
        ttk.Label(thresh_frame, textvariable=self.event_threshold).pack(side='right')
        
        # Minimum event duration control
        dur_frame = ttk.Frame(event_frame)
        dur_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(dur_frame, text="Min Duration (s):").pack(side='left')
        ttk.Scale(dur_frame, from_=0.01, to=1.0, variable=self.min_event_duration,
                 orient='horizontal', command=self.on_event_settings_change
                 ).pack(side='left', fill='x', expand=True)
        ttk.Label(dur_frame, textvariable=self.min_event_duration).pack(side='right')
        
        # Event statistics display
        ttk.Label(event_frame, textvariable=self.event_stats_text,
                 wraplength=300, justify='left').pack(fill='x', padx=5, pady=5)

    def update_data(self, data, time_data):
        """Update the data for analysis"""
        self.data = data
        self.time_data = time_data
        self.filtered_data = data.copy()
        self.update_statistics()
        self.update_peak_detection()
        self.update_event_analysis()

    def update_filtered_data(self, filtered_data):
        """Update the filtered data for analysis"""
        self.filtered_data = filtered_data
        self.update_statistics()
        self.update_peak_detection()
        self.update_event_analysis()

    def update_statistics(self):
        """Update basic signal statistics"""
        if self.filtered_data is None:
            return
            
        try:
            # Calculate basic statistics
            stats = {
                'mean': np.mean(self.filtered_data),
                'std': np.std(self.filtered_data),
                'min': np.min(self.filtered_data),
                'max': np.max(self.filtered_data),
                'peak_to_peak': np.ptp(self.filtered_data),
                'rms': np.sqrt(np.mean(np.square(self.filtered_data)))
            }
            
            # Update display
            stats_text = (
                f"Signal Statistics:\n"
                f"Mean: {stats['mean']:.2f} pA\n"
                f"Std Dev: {stats['std']:.2f} pA\n"
                f"Min: {stats['min']:.2f} pA\n"
                f"Max: {stats['max']:.2f} pA\n"
                f"Peak-to-Peak: {stats['peak_to_peak']:.2f} pA\n"
                f"RMS: {stats['rms']:.2f} pA"
            )
            self.stats_text.set(stats_text)
            
        except Exception as e:
            app_logger.error(f"Error updating statistics: {str(e)}")

    def update_peak_detection(self):
        """Update peak detection analysis"""
        if not self.detect_peaks.get() or self.filtered_data is None:
            return
            
        try:
            # Find peaks with current settings
            peaks, properties = find_peaks(
                self.filtered_data,
                height=self.peak_height.get(),
                prominence=self.peak_prominence.get(),
                distance=self.peak_distance.get(),
                width=self.peak_width.get()
            )
            
            if len(peaks) > 0:
                # Calculate peak statistics
                peak_heights = self.filtered_data[peaks]
                peak_stats = {
                    'count': len(peaks),
                    'mean_height': np.mean(peak_heights),
                    'std_height': np.std(peak_heights),
                    'mean_prominence': np.mean(properties['prominences']),
                    'mean_width': np.mean(properties['widths'])
                }
                
                # Update display
                stats_text = (
                    f"Peak Analysis:\n"
                    f"Number of Peaks: {peak_stats['count']}\n"
                    f"Mean Height: {peak_stats['mean_height']:.2f} pA\n"
                    f"Height Std: {peak_stats['std_height']:.2f} pA\n"
                    f"Mean Prominence: {peak_stats['mean_prominence']:.2f}\n"
                    f"Mean Width: {peak_stats['mean_width']:.2f} points"
                )
                self.peak_stats_text.set(stats_text)
            else:
                self.peak_stats_text.set("No peaks detected")
            
            # Update callback with peak information
            self.update_callback({
                'peaks': peaks,
                'peak_properties': properties
            })
            
        except Exception as e:
            app_logger.error(f"Error in peak detection: {str(e)}")

    def update_event_analysis(self):
        """Update event analysis"""
        if not self.analyze_events.get() or self.filtered_data is None:
            return
            
        try:
            # Find events based on threshold
            threshold = self.event_threshold.get()
            min_duration = self.min_event_duration.get()
            sampling_rate = len(self.time_data) / (self.time_data[-1] - self.time_data[0])
            min_samples = int(min_duration * sampling_rate)
            
            # Detect threshold crossings
            above_threshold = self.filtered_data > threshold
            crossings = np.diff(above_threshold.astype(int))
            starts = np.where(crossings == 1)[0]
            ends = np.where(crossings == -1)[0]
            
            # Ensure equal number of starts and ends
            if len(ends) > 0 and len(starts) > 0:
                if starts[0] > ends[0]:
                    ends = ends[1:]
                if len(starts) > len(ends):
                    starts = starts[:len(ends)]
                
                # Filter by duration
                durations = ends - starts
                valid_events = durations >= min_samples
                starts = starts[valid_events]
                ends = ends[valid_events]
                
                if len(starts) > 0:
                    # Calculate event statistics
                    event_stats = {
                        'count': len(starts),
                        'mean_duration': np.mean(ends - starts) / sampling_rate,
                        'mean_amplitude': np.mean([
                            np.max(self.filtered_data[s:e])
                            for s, e in zip(starts, ends)
                        ])
                    }
                    
                    # Update display
                    stats_text = (
                        f"Event Analysis:\n"
                        f"Number of Events: {event_stats['count']}\n"
                        f"Mean Duration: {event_stats['mean_duration']:.3f} s\n"
                        f"Mean Amplitude: {event_stats['mean_amplitude']:.2f} pA"
                    )
                    self.event_stats_text.set(stats_text)
                    
                    # Update callback with event information
                    self.update_callback({
                        'event_starts': starts,
                        'event_ends': ends,
                        'event_stats': event_stats
                    })
                else:
                    self.event_stats_text.set("No events detected")
            else:
                self.event_stats_text.set("No events detected")
            
        except Exception as e:
            app_logger.error(f"Error in event analysis: {str(e)}")

    def on_peak_settings_change(self, *args):
        """Handle changes to peak detection settings"""
        if self.detect_peaks.get():
            self.update_peak_detection()

    def on_event_settings_change(self, *args):
        """Handle changes to event analysis settings"""
        if self.analyze_events.get():
            self.update_event_analysis()

    def get_analysis_params(self):
        """Get current analysis parameters"""
        return {
            'detect_peaks': self.detect_peaks.get(),
            'peak_params': {
                'height': self.peak_height.get(),
                'prominence': self.peak_prominence.get(),
                'distance': self.peak_distance.get(),
                'width': self.peak_width.get()
            },
            'analyze_events': self.analyze_events.get(),
            'event_params': {
                'threshold': self.event_threshold.get(),
                'min_duration': self.min_event_duration.get()
            }
        }