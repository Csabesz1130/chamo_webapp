# src/io_utils/io_utils.py
import numpy as np
from ..utils.logger import app_logger  # Changed from src.utils.logger

class ATFHandler:
    def __init__(self, filepath):
        self.filepath = filepath
        self.headers = []
        self.data = None
        self.metadata = {}
        app_logger.info(f"Initializing ATF Handler for file: {filepath}")

    def load_atf(self):
        """Load and parse the ATF file, storing headers and data."""
        app_logger.info("Starting ATF file load")
        try:
            with open(self.filepath, 'r') as file:
                lines = file.readlines()

            # Verify ATF format and version
            version_info = lines[0].strip().split()
            if version_info[0] != 'ATF':
                app_logger.error("Invalid file format - not an ATF file")
                raise ValueError("File format is not ATF.")
            self.metadata['version'] = version_info[1]
            app_logger.debug(f"ATF version: {version_info[1]}")

            # Parse header info from second line
            header_info = lines[1].strip().split()
            self.metadata['header_lines'] = int(header_info[0])
            
            # Extract headers and clean quotes
            header_lines = []
            for line in lines[2:self.metadata['header_lines']+2]:
                if line.strip():
                    # Remove quotes and clean the line
                    cleaned_line = line.strip().replace('"', '').replace('=', '')
                    header_lines.append(cleaned_line)
            
            # Parse headers
            self.headers = header_lines[-1].split()
            app_logger.debug(f"Detected headers: {self.headers}")

            # Parse data lines
            data_lines = []
            for line in lines[self.metadata['header_lines']+2:]:
                if line.strip():
                    try:
                        values = [float(val) for val in line.strip().split()]
                        data_lines.append(values)
                    except ValueError:
                        continue

            self.data = np.array(data_lines)
            app_logger.info(f"Successfully loaded data with shape: {self.data.shape}")

            # Create a mapping of signal types and their columns
            self.signal_map = self._create_signal_map()
            app_logger.debug(f"Signal map: {self.signal_map}")

        except Exception as e:
            app_logger.error(f"Error loading ATF file: {str(e)}")
            raise

    def _create_signal_map(self):
        """Create a mapping of signal types to their column indices"""
        signal_map = {}
        
        # Map column indices directly
        current_trace = 1
        for i, header in enumerate(self.headers):
            if header == 'Im' or 'I_MTest' in header:
                signal_map[f"Trace_{current_trace}"] = i
                current_trace += 1
                
        app_logger.debug(f"Created signal map: {signal_map}")
        return signal_map

    def get_column(self, column_name):
        """Get data from a specific column by header name or trace number."""
        app_logger.debug(f"Attempting to get column: {column_name}")
        
        if self.data is None:
            app_logger.error("No data loaded. Call load_atf() first.")
            raise ValueError("No data loaded. Call load_atf() first.")

        # Print actual data shape and headers for debugging
        app_logger.debug(f"Data shape: {self.data.shape}")
        app_logger.debug(f"Available headers: {self.headers}")
        app_logger.debug(f"Current signal map: {self.signal_map}")

        # Handle trace columns
        if column_name.startswith('#'):
            trace_num = column_name[1:]
            trace_key = f"Trace_{trace_num}"
            
            if trace_key in self.signal_map:
                column_idx = self.signal_map[trace_key]
                app_logger.debug(f"Found trace {trace_num} at index {column_idx}")
                return self.data[:, column_idx]
            else:
                # If not found in signal map, try to find in raw data
                for i, header in enumerate(self.headers):
                    if 'Im' in header or 'I_MTest' in header:
                        app_logger.debug(f"Found alternative trace data at index {i}")
                        return self.data[:, i]
                        
                app_logger.error(f"Trace {trace_num} not found in signal map or raw data")
                raise ValueError(f"Trace {trace_num} not found in signal map or raw data")

        # Handle time column
        if column_name.lower() == 'time':
            app_logger.debug("Generating time data")
            # Use the first column as time or generate time data
            time_data = np.arange(len(self.data)) * 0.0001  # Assuming 0.1ms sampling rate
            return time_data

        # Handle other named columns
        try:
            # Clean up column name for comparison
            clean_name = column_name.replace('"', '')
            for i, header in enumerate(self.headers):
                if clean_name in header.replace('"', ''):
                    if i < self.data.shape[1]:
                        app_logger.debug(f"Found column {clean_name} at index {i}")
                        return self.data[:, i]
                
            app_logger.error(f"Column '{column_name}' not found")
            raise ValueError(f"Column '{column_name}' not found")
                
        except ValueError as e:
            app_logger.error(f"Error accessing column: {str(e)}")
            raise

    def get_sampling_rate(self):
        """Get the sampling rate from the file or use default"""
        return 0.0001  # 0.1ms in seconds