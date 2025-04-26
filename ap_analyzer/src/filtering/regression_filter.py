# src/filtering/regression_filter.py

import numpy as np
from sklearn.linear_model import LinearRegression
from src.utils.logger import app_logger

class LinearRegressionFilter:
    def __init__(self, window_size=100):
        """
        Initialize linear regression filter
        
        Args:
            window_size: Number of initial points to use for regression
        """
        self.window_size = window_size
        self.reg = LinearRegression()
        self.fitted_curve = None
        
    def fit_initial_points(self, data, time_data):
        """
        Fit linear regression to initial points of the signal
        
        Args:
            data: Signal data array
            time_data: Time points array
            
        Returns:
            numpy.ndarray: Smoothed initial segment of the signal
        """
        try:
            app_logger.info("Fitting linear regression to initial points")
            
            # Use specified number of initial points
            n_points = min(self.window_size, len(data))
            X = time_data[:n_points].reshape(-1, 1)
            y = data[:n_points]
            
            # Fit regression
            self.reg.fit(X, y)
            
            # Generate smoothed curve
            self.fitted_curve = self.reg.predict(X)
            
            # Calculate fit quality
            r2_score = self.reg.score(X, y)
            app_logger.info(f"Linear regression fit R² score: {r2_score:.4f}")
            
            return self.fitted_curve
            
        except Exception as e:
            app_logger.error(f"Error in linear regression fitting: {str(e)}")
            raise
            
    def apply_regression_filter(self, data, time_data, blend=True, blend_window=20):
        """
        Apply linear regression filtering to signal
        
        Args:
            data: Signal data array
            time_data: Time points array
            blend: Whether to blend transition between regression and original signal
            blend_window: Size of blending window
            
        Returns:
            numpy.ndarray: Filtered signal data
        """
        try:
            # Fit regression to initial points
            smoothed_start = self.fit_initial_points(data, time_data)
            filtered_data = data.copy()
            
            # Replace initial segment with smoothed data
            if blend:
                # Create smooth transition
                blend_end = min(len(smoothed_start), blend_window)
                weights = np.linspace(1, 0, blend_end)
                filtered_data[:blend_end] = (
                    weights * smoothed_start[:blend_end] + 
                    (1 - weights) * data[:blend_end]
                )
            else:
                filtered_data[:len(smoothed_start)] = smoothed_start
                
            return filtered_data
            
        except Exception as e:
            app_logger.error(f"Error applying regression filter: {str(e)}")
            raise
            
    def get_regression_stats(self):
        """Get regression statistics"""
        if self.reg is None or self.fitted_curve is None:
            return None
            
        return {
            'slope': self.reg.coef_[0],
            'intercept': self.reg.intercept_,
            'initial_trend': 'increasing' if self.reg.coef_[0] > 0 else 'decreasing'
        }