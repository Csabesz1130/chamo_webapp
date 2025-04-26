import numpy as np
from utils.logger import app_logger

class SignalStatistics:
    def __init__(self):
        self.stats = {}
        
    def calculate_basic_stats(self, data):
        """
        Calculate basic signal statistics.
        
        Args:
            data (np.array): Input signal data
            
        Returns:
            dict: Dictionary containing basic statistics
        """
        app_logger.debug("Calculating basic signal statistics")
        try:
            self.stats.update({
                'mean': np.mean(data),
                'std': np.std(data),
                'min': np.min(data),
                'max': np.max(data),
                'peak_to_peak': np.ptp(data),
                'rms': np.sqrt(np.mean(np.square(data))),
                'variance': np.var(data)
            })
            
            app_logger.debug("Basic statistics calculated successfully")
            return self.stats
            
        except Exception as e:
            app_logger.error(f"Error calculating basic statistics: {str(e)}")
            raise
            
    def calculate_advanced_stats(self, data):
        """
        Calculate advanced signal statistics.
        
        Args:
            data (np.array): Input signal data
            
        Returns:
            dict: Dictionary containing advanced statistics
        """
        app_logger.debug("Calculating advanced signal statistics")
        try:
            # Calculate skewness
            skewness = np.mean(((data - np.mean(data)) / np.std(data)) ** 3)
            
            # Calculate kurtosis
            kurtosis = np.mean(((data - np.mean(data)) / np.std(data)) ** 4) - 3
            
            # Calculate signal energy
            energy = np.sum(np.square(data))
            
            # Update stats dictionary
            self.stats.update({
                'skewness': skewness,
                'kurtosis': kurtosis,
                'energy': energy
            })
            
            app_logger.debug("Advanced statistics calculated successfully")
            return self.stats
            
        except Exception as e:
            app_logger.error(f"Error calculating advanced statistics: {str(e)}")
            raise
            
    def calculate_interval_stats(self, data, start_idx, end_idx):
        """
        Calculate statistics for a specific interval of the signal.
        
        Args:
            data (np.array): Input signal data
            start_idx (int): Start index of interval
            end_idx (int): End index of interval
            
        Returns:
            dict: Dictionary containing interval statistics
        """
        app_logger.debug(f"Calculating statistics for interval [{start_idx}, {end_idx}]")
        try:
            interval_data = data[start_idx:end_idx]
            interval_stats = {
                'interval_mean': np.mean(interval_data),
                'interval_std': np.std(interval_data),
                'interval_min': np.min(interval_data),
                'interval_max': np.max(interval_data),
                'interval_peak_to_peak': np.ptp(interval_data)
            }
            
            self.stats.update({'interval': interval_stats})
            
            app_logger.debug("Interval statistics calculated successfully")
            return interval_stats
            
        except Exception as e:
            app_logger.error(f"Error calculating interval statistics: {str(e)}")
            raise
            
    def get_statistics_summary(self, include_advanced=True):
        """
        Get a formatted summary of all calculated statistics.
        
        Args:
            include_advanced (bool): Whether to include advanced statistics
            
        Returns:
            str: Formatted statistics summary
        """
        try:
            summary = []
            
            # Basic statistics
            if 'mean' in self.stats:
                summary.extend([
                    "Basic Statistics:",
                    f"Mean: {self.stats['mean']:.2f}",
                    f"Std Dev: {self.stats['std']:.2f}",
                    f"Min: {self.stats['min']:.2f}",
                    f"Max: {self.stats['max']:.2f}",
                    f"Peak-to-Peak: {self.stats['peak_to_peak']:.2f}",
                    f"RMS: {self.stats['rms']:.2f}"
                ])
            
            # Advanced statistics
            if include_advanced and 'skewness' in self.stats:
                summary.extend([
                    "\nAdvanced Statistics:",
                    f"Skewness: {self.stats['skewness']:.2f}",
                    f"Kurtosis: {self.stats['kurtosis']:.2f}",
                    f"Signal Energy: {self.stats['energy']:.2f}"
                ])
            
            # Interval statistics
            if 'interval' in self.stats:
                interval = self.stats['interval']
                summary.extend([
                    "\nInterval Statistics:",
                    f"Mean: {interval['interval_mean']:.2f}",
                    f"Std Dev: {interval['interval_std']:.2f}",
                    f"Min: {interval['interval_min']:.2f}",
                    f"Max: {interval['interval_max']:.2f}",
                    f"Peak-to-Peak: {interval['interval_peak_to_peak']:.2f}"
                ])
            
            return '\n'.join(summary)
            
        except Exception as e:
            app_logger.error(f"Error generating statistics summary: {str(e)}")
            raise