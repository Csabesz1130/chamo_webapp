import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import re
from src.utils.logger import app_logger

class LogViewerTab(ttk.Frame):
    """
    A tab for viewing application logs in real-time.
    Provides filtering capabilities and automatic updates.
    """
    
    def __init__(self, parent, log_file_path=None, *args, **kwargs):
        """
        Initialize the log viewer tab.
        
        Args:
            parent: The parent widget
            log_file_path: Path to the log file to monitor (optional)
            *args, **kwargs: Additional arguments to pass to the Frame constructor
        """
        super().__init__(parent, *args, **kwargs)
        
        self.log_file_path = log_file_path
        self.log_buffer = []
        self.filter_pattern = None
        self.update_interval = 1000  # milliseconds
        self.auto_scroll = True
        self.running = True
        
        # Set up the UI components
        self._setup_ui()
        
        # Start the log update thread if a log file is provided
        if self.log_file_path:
            self._start_log_monitoring()
        else:
            # Set up a callback handler for direct log messages
            self._setup_log_callback()
        
        app_logger.info("Log viewer tab initialized")
    
    def _setup_ui(self):
        """Set up the user interface components."""
        # Create main container
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create control frame for buttons and filters
        self.control_frame = ttk.Frame(self.main_container)
        self.control_frame.pack(fill=tk.X, side=tk.TOP, padx=5, pady=5)
        
        # Add clear button
        self.clear_button = ttk.Button(
            self.control_frame, 
            text="Clear Logs", 
            command=self.clear_logs
        )
        self.clear_button.pack(side=tk.LEFT, padx=2)
        
        # Add filter controls
        ttk.Label(self.control_frame, text="Filter:").pack(side=tk.LEFT, padx=(10, 2))
        self.filter_var = tk.StringVar()
        self.filter_entry = ttk.Entry(self.control_frame, textvariable=self.filter_var)
        self.filter_entry.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # Add filter button
        self.filter_button = ttk.Button(
            self.control_frame, 
            text="Apply Filter", 
            command=self.apply_filter
        )
        self.filter_button.pack(side=tk.LEFT, padx=2)
        
        # Add log level filter
        ttk.Label(self.control_frame, text="Log Level:").pack(side=tk.LEFT, padx=(10, 2))
        self.log_level_var = tk.StringVar(value="ALL")
        self.log_level_combo = ttk.Combobox(
            self.control_frame,
            textvariable=self.log_level_var,
            values=["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            state="readonly",
            width=10
        )
        self.log_level_combo.pack(side=tk.LEFT, padx=2)
        self.log_level_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filter())
        
        # Add auto-scroll checkbox
        self.auto_scroll_var = tk.BooleanVar(value=True)
        self.auto_scroll_check = ttk.Checkbutton(
            self.control_frame,
            text="Auto-scroll",
            variable=self.auto_scroll_var,
            command=self.toggle_auto_scroll
        )
        self.auto_scroll_check.pack(side=tk.LEFT, padx=(10, 2))
        
        # Create log text area with scrollbar
        self.log_text = scrolledtext.ScrolledText(
            self.main_container,
            wrap=tk.WORD,
            width=80,
            height=20,
            font=("Consolas", 10)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure text tags for different log levels
        self.log_text.tag_configure("DEBUG", foreground="gray")
        self.log_text.tag_configure("INFO", foreground="black")
        self.log_text.tag_configure("WARNING", foreground="orange")
        self.log_text.tag_configure("ERROR", foreground="red")
        self.log_text.tag_configure("CRITICAL", foreground="red", background="yellow")
        
        # Make the text widget read-only
        self.log_text.config(state=tk.DISABLED)
    
    def _start_log_monitoring(self):
        """Start a thread to monitor the log file for changes."""
        self.log_thread = threading.Thread(target=self._monitor_log_file, daemon=True)
        self.log_thread.start()
        
        # Schedule the first UI update
        self.after(self.update_interval, self.update_log_view)
    
    def _setup_log_callback(self):
        """Set up a callback to receive log messages directly."""
        # This would be connected to the application's logging system
        # For now, we'll just schedule periodic updates
        self.after(self.update_interval, self.update_log_view)
    
    def _monitor_log_file(self):
        """Monitor the log file for changes in a separate thread."""
        if not self.log_file_path:
            return
            
        try:
            with open(self.log_file_path, 'r') as file:
                # Move to the end of the file
                file.seek(0, 2)
                
                while self.running:
                    line = file.readline()
                    if line:
                        self.log_buffer.append(line)
                    else:
                        # No new lines, sleep briefly
                        time.sleep(0.1)
        except Exception as e:
            app_logger.error(f"Error monitoring log file: {str(e)}")
    
    def update_log_view(self):
        """Update the log view with new log entries."""
        if not self.running:
            return
            
        try:
            # Process any new log entries in the buffer
            if self.log_buffer:
                self.log_text.config(state=tk.NORMAL)
                
                for log_entry in self.log_buffer:
                    # Apply filtering if needed
                    if self._should_display_log(log_entry):
                        # Determine log level for coloring
                        tag = self._get_log_level_tag(log_entry)
                        
                        # Add the log entry to the text widget
                        self.log_text.insert(tk.END, log_entry, tag)
                        
                        # Auto-scroll to the bottom if enabled
                        if self.auto_scroll_var.get():
                            self.log_text.see(tk.END)
                
                # Clear the buffer
                self.log_buffer = []
                
                self.log_text.config(state=tk.DISABLED)
        except Exception as e:
            app_logger.error(f"Error updating log view: {str(e)}")
        
        # Schedule the next update
        self.after(self.update_interval, self.update_log_view)
    
    def _should_display_log(self, log_entry):
        """
        Determine if a log entry should be displayed based on current filters.
        
        Args:
            log_entry: The log entry to check
            
        Returns:
            bool: True if the entry should be displayed, False otherwise
        """
        # Check log level filter
        selected_level = self.log_level_var.get()
        if selected_level != "ALL":
            if selected_level not in log_entry:
                return False
        
        # Check text filter
        filter_text = self.filter_var.get()
        if filter_text and filter_text not in log_entry:
            return False
            
        return True
    
    def _get_log_level_tag(self, log_entry):
        """
        Determine the appropriate tag for a log entry based on its level.
        
        Args:
            log_entry: The log entry to check
            
        Returns:
            str: The tag name to use for this entry
        """
        if "CRITICAL" in log_entry:
            return "CRITICAL"
        elif "ERROR" in log_entry:
            return "ERROR"
        elif "WARNING" in log_entry:
            return "WARNING"
        elif "INFO" in log_entry:
            return "INFO"
        elif "DEBUG" in log_entry:
            return "DEBUG"
        else:
            return "INFO"  # Default
    
    def apply_filter(self):
        """Apply the current filter settings to the log display."""
        # Clear and redisplay all logs with the new filter
        current_text = self.log_text.get(1.0, tk.END)
        self.clear_logs()
        
        # Split the text into lines and re-add them with filtering
        lines = current_text.split('\n')
        self.log_buffer.extend([line + '\n' for line in lines if line])
        self.update_log_view()
    
    def clear_logs(self):
        """Clear all logs from the display."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def toggle_auto_scroll(self):
        """Toggle the auto-scroll feature."""
        self.auto_scroll = self.auto_scroll_var.get()
    
    def add_log_message(self, message, level="INFO"):
        """
        Add a log message directly to the viewer.
        
        Args:
            message: The log message to add
            level: The log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        self.log_buffer.append(log_entry)
    
    def on_closing(self):
        """Clean up resources when the tab is closed."""
        self.running = False
        # Wait for the monitoring thread to finish if it exists
        if hasattr(self, 'log_thread') and self.log_thread.is_alive():
            self.log_thread.join(timeout=1.0)