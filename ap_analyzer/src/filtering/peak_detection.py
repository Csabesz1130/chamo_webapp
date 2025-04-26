import numpy as np
from scipy.signal import find_peaks
from utils.logger import app_logger

class PeakDetector:
    def __init__(self):
        self.peak_indices = None
        self.peak_properties = None

    def detect_peaks(self, data, height=None, distance=None, prominence=None, width=None):
        """
        Detect peaks in the signal data.
        
        Args:
            data (np.array): Input signal data
            height (float): Minimum peak height
            distance (int): Minimum distance between peaks
            prominence (float): Minimum peak prominence
            width (float): Minimum peak width
            
        Returns:
            tuple: (peak_indices, peak_properties)
        """
        app_logger.debug("Starting peak detection")
        try:
            # Normalize data for consistent peak detection
            normalized_data = self._normalize_data(data)
            
            # Find peaks
            self.peak_indices, properties = find_peaks(
                normalized_data,
                height=height,
                distance=distance,
                prominence=prominence,
                width=width
            )
            
            # Store properties and calculate peak metrics
            self.peak_properties = self._calculate_peak_metrics(
                data, self.peak_indices, properties
            )
            
            app_logger.info(f"Detected {len(self.peak_indices)} peaks")
            return self.peak_indices, self.peak_properties
        
        except Exception as e:
            app_logger.error(f"Error in peak detection: {str(e)}")
            raise

    def _normalize_data(self, data):
        """Normalize data to 0-1 range"""
        try:
            normalized = (data - np.min(data)) / (np.max(data) - np.min(data))
            return normalized
        except Exception as e:
            app_logger.error(f"Error normalizing data: {str(e)}")
            raise

    def _calculate_peak_metrics(self, data, indices, properties):
        """Calculate additional peak metrics"""
        try:
            metrics = {
                'heights': data[indices],
                'peak_indices': indices
            }
            
            # Add additional properties if available
            if 'prominences' in properties:
                metrics['prominences'] = properties['prominences']
            if 'widths' in properties:
                metrics['widths'] = properties['widths']
            
            # Calculate intervals between peaks
            if len(indices) > 1:
                metrics['intervals'] = np.diff(indices)
            
            return metrics
        
        except Exception as e:
            app_logger.error(f"Error calculating peak metrics: {str(e)}")
            raise

    def get_peak_statistics(self):
        """Get statistical summary of peak properties"""
        if self.peak_indices is None or len(self.peak_indices) == 0:
            return None
            
        try:
            stats = {
                'num_peaks': len(self.peak_indices),
                'mean_height': np.mean(self.peak_properties['heights']),
                'std_height': np.std(self.peak_properties['heights'])
            }
            
            if 'intervals' in self.peak_properties:
                stats.update({
                    'mean_interval': np.mean(self.peak_properties['intervals']),
                    'std_interval': np.std(self.peak_properties['intervals'])
                })
            
            if 'widths' in self.peak_properties:
                stats.update({
                    'mean_width': np.mean(self.peak_properties['widths']),
                    'std_width': np.std(self.peak_properties['widths'])
                })
            
            return stats
            
        except Exception as e:
            app_logger.error(f"Error calculating peak statistics: {str(e)}")
            raise