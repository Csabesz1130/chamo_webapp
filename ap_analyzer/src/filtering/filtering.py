import numpy as np
from scipy.signal import (
    savgol_filter, 
    butter, 
    filtfilt, 
    find_peaks, 
    sosfilt, 
    butter as butter_design
)
from scipy.fft import fft, ifft, fftfreq
from pywt import wavedec, waverec, threshold  
from src.utils.logger import app_logger


def apply_savgol_filter(data, window_length=51, polyorder=3):
    """
    Apply Savitzky-Golay filter to the data.
    
    Args:
        data (np.array): Input signal data
        window_length (int): Length of the filter window (must be odd)
        polyorder (int): Order of the polynomial
        
    Returns:
        np.array: Filtered data
    """
    app_logger.debug(f"Applying Savitzky-Golay filter: window={window_length}, order={polyorder}")
    try:
        # Ensure window length is odd
        if window_length % 2 == 0:
            window_length += 1
        
        filtered_data = savgol_filter(data, window_length, polyorder)
        app_logger.info("Savitzky-Golay filter applied successfully")
        return filtered_data
    
    except Exception as e:
        app_logger.error(f"Error applying Savitzky-Golay filter: {str(e)}")
        raise


def apply_fft_filter(data, threshold=0.2, min_freq=None, max_freq=None, sampling_rate=1000.0):
    """
    Absolutely minimal FFT filter implementation.
    
    Args:
        data (np.array): Input signal data
        threshold (float): Threshold for frequency components (0 to 1)
        min_freq (float, optional): Minimum frequency to keep (Hz)
        max_freq (float, optional): Maximum frequency to keep (Hz)
        sampling_rate (float): Sampling rate of the signal in Hz
    
    Returns:
        np.array: Filtered data
    """
    try:
        # Convert to numpy array
        signal = np.asarray(data)
        n = len(signal)
        
        # Compute FFT
        spectrum = fft(signal)
        
        # Get frequencies
        frequencies = fftfreq(n, d=1/sampling_rate)
        
        # Create mask without any indexing or broadcasting
        mask = np.ones(n, dtype=bool)
        
        # Apply threshold to each component individually
        for i in range(n):
            if i == 0:  # DC component
                continue
                
            # Check magnitude against threshold
            if np.abs(spectrum[i]) < threshold * np.max(np.abs(spectrum)):
                mask[i] = False
            
            # Apply frequency band if specified
            if min_freq is not None and max_freq is not None:
                if abs(frequencies[i]) < min_freq or abs(frequencies[i]) > max_freq:
                    mask[i] = False
        
        # Apply filter directly
        filtered_spectrum = np.zeros(n, dtype=complex)
        for i in range(n):
            if mask[i]:
                filtered_spectrum[i] = spectrum[i]
        
        # Inverse FFT
        filtered_signal = np.real(ifft(filtered_spectrum))
        
        # Log statistics
        retained = np.sum(mask) / len(mask) * 100
        app_logger.info(f"FFT filter retained {retained:.1f}% of components")
        
        return filtered_signal
        
    except Exception as e:
        app_logger.error(f"Error in FFT filter: {str(e)}")
        app_logger.error(f"Signal shape: {signal.shape if 'signal' in locals() else 'N/A'}")
        raise

def butter_lowpass_filter(data, cutoff, fs=1000.0, order=5):
    """
    Apply improved Butterworth low-pass filter with better stability.
    
    Args:
        data (np.array): Input signal data
        cutoff (float): Cutoff frequency in Hz
        fs (float): Sampling frequency in Hz
        order (int): Filter order
        
    Returns:
        np.array: Filtered data
    """
    app_logger.debug(f"Applying Butterworth filter: cutoff={cutoff}Hz, order={order}")
    try:
        # Convert cutoff to Hz if it's normalized
        if cutoff <= 1:
            cutoff = cutoff * (fs/2)
            
        # Ensure cutoff is valid
        nyquist = fs / 2
        if cutoff >= nyquist:
            cutoff = 0.99 * nyquist
            app_logger.warning(f"Cutoff too high, adjusted to {cutoff:.1f} Hz")
            
        # Design filter using second-order sections for better numerical stability
        sos = butter_design(order, cutoff, btype='low', fs=fs, output='sos')
        
        # Apply zero-phase filtering
        filtered_data = sosfilt(sos, data)
        
        # Apply forward-backward filtering to ensure zero phase
        filtered_data = sosfilt(sos, filtered_data[::-1])[::-1]
        
        return filtered_data
        
    except Exception as e:
        app_logger.error(f"Error in Butterworth filter: {str(e)}")
        raise

def combined_filter(data, savgol_params=None, wavelet_params=None, butter_params=None, 
                   extract_add_params=None):
    """
    Apply multiple filters in sequence.
    
    Args:
        data (np.array): Input signal data
        savgol_params (dict): Parameters for Savitzky-Golay filter
        wavelet_params (dict): Parameters for Wavelet filter
        butter_params (dict): Parameters for Butterworth filter
        extract_add_params (dict): Parameters for extract-add filter
        
    Returns:
        np.array: Filtered data
    """
    app_logger.info("Starting combined filtering process")
    filtered_data = np.array(data, copy=True)
    
    try:
        # Apply Savitzky-Golay filter
        if savgol_params:
            filtered_data = apply_savgol_filter(
                filtered_data,
                window_length=savgol_params['window_length'],
                polyorder=savgol_params['polyorder']
            )
        
        # Apply Wavelet filter
        if wavelet_params:
            filtered_data = apply_wavelet_filter(
                filtered_data,
                wavelet=wavelet_params['wavelet'],
                level=wavelet_params['level'],
                threshold_mode=wavelet_params['threshold_mode']
            )
        
        # Apply Butterworth filter
        if butter_params:
            filtered_data = butter_lowpass_filter(
                filtered_data,
                cutoff=butter_params['cutoff'],
                fs=butter_params.get('fs', 1000.0),
                order=butter_params['order']
            )
        
        # Apply Extract-Add filter
        if extract_add_params:
            filtered_data = extract_add_filter(
                filtered_data,
                **extract_add_params
            )
        
        return filtered_data
        
    except Exception as e:
        app_logger.error(f"Error in combined filtering: {str(e)}")
        raise


def calculate_filter_metrics(original_data, filtered_data):
    """
    Calculate metrics to evaluate filter performance.
    
    Args:
        original_data (np.array): Original signal data
        filtered_data (np.array): Filtered signal data
        
    Returns:
        dict: Dictionary containing filter performance metrics
    """
    try:
        # Calculate various metrics
        residuals = original_data - filtered_data
        mse = np.mean(np.square(residuals))
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(residuals))
        
        # Calculate signal-to-noise ratio
        signal_power = np.mean(np.square(filtered_data))
        noise_power = np.mean(np.square(residuals))
        snr = 10 * np.log10(signal_power / noise_power) if noise_power > 0 else float('inf')
        
        metrics = {
            'mse': mse,
            'rmse': rmse,
            'mae': mae,
            'snr_db': snr,
            'max_deviation': np.max(np.abs(residuals)),
            'mean_deviation': np.mean(residuals)
        }
        
        app_logger.debug("Filter metrics calculated successfully")
        return metrics
        
    except Exception as e:
        app_logger.error(f"Error calculating filter metrics: {str(e)}")
        raise

def apply_wavelet_filter(data, wavelet='db4', level=None, threshold_mode='soft'):
    """
    Apply wavelet-based denoising filter.
    
    Args:
        data (np.array): Input signal data
        wavelet (str): Wavelet type ('db4', 'sym4', or 'coif3' recommended for biological signals)
        level (int): Decomposition level (None for automatic)
        threshold_mode (str): 'soft' or 'hard' thresholding
        
    Returns:
        np.array: Filtered data
    """
    try:
        # Convert to numpy array
        data = np.asarray(data, dtype=np.float64)
        
        # Automatically determine level if not specified
        if level is None:
            level = min(int(np.log2(len(data))), 10)
        
        # Decompose signal into wavelet coefficients
        coeffs = wavedec(data, wavelet, level=level)
        
        # Calculate noise estimate from finest level
        noise_sigma = mad(coeffs[-1]) / 0.6745
        
        # Calculate threshold
        threshold_value = noise_sigma * np.sqrt(2 * np.log(len(data)))
        
        # Process each coefficient level
        for i in range(1, len(coeffs)):  # Skip approximation coefficients
            coeffs[i] = threshold(coeffs[i], threshold_value, mode=threshold_mode)
        
        # Reconstruct signal
        filtered_data = waverec(coeffs, wavelet)
        
        # Ensure output length matches input
        if len(filtered_data) > len(data):
            filtered_data = filtered_data[:len(data)]
        elif len(filtered_data) < len(data):
            filtered_data = np.pad(filtered_data, (0, len(data) - len(filtered_data)))
        
        app_logger.info(f"Wavelet filter applied: level={level}, wavelet={wavelet}")
        return filtered_data
        
    except Exception as e:
        app_logger.error(f"Error in wavelet filter: {str(e)}")
        raise

def mad(data):
    """Calculate Median Absolute Deviation"""
    median = np.median(data)
    return np.median(np.abs(data - median))


def adaptive_threshold_filter(data, window_size=50):
    """
    Apply adaptive thresholding based on local signal statistics.
    
    Args:
        data (np.array): Input signal data
        window_size (int): Size of the sliding window
        
    Returns:
        np.array: Filtered data
    """
    app_logger.debug(f"Applying adaptive threshold filter with window_size={window_size}")
    try:
        filtered_data = data.copy()
        padding = window_size // 2
        
        # Pad the data for edge handling
        padded_data = np.pad(data, (padding, padding), mode='edge')
        
        for i in range(len(data)):
            # Get local window
            window = padded_data[i:i + window_size]
            
            # Calculate local statistics
            local_mean = np.mean(window)
            local_std = np.std(window)
            
            # Apply adaptive threshold
            if abs(data[i] - local_mean) > 2 * local_std:
                filtered_data[i] = local_mean
        
        app_logger.info("Adaptive threshold filter applied successfully")
        return filtered_data
        
    except Exception as e:
        app_logger.error(f"Error applying adaptive threshold filter: {str(e)}")
        raise

def extract_add_filter(data, window_length=51, polyorder=3, prominence_threshold=200, width_range=(1, 50)):
    """
    Implementation of the extract-filter-add method for preserving important signal features.
    1. Extracts significant peaks/events from the signal
    2. Filters the remaining baseline
    3. Adds the extracted features back to the filtered baseline
    
    Args:
        data (np.array): Input signal data
        window_length (int): Length of the filter window for baseline filtering
        polyorder (int): Order of the polynomial for baseline filtering
        prominence_threshold (float): Minimum prominence for peak detection
        width_range (tuple): Expected width range of peaks (min, max)
    
    Returns:
        np.array: Filtered data with preserved peaks/events
    """
    app_logger.debug("Starting extract-add filtering process")
    try:
        # 1. Peak Detection and Extraction
        # Find peaks with significant prominence
        peaks, properties = find_peaks(data, 
                                     prominence=prominence_threshold,
                                     width=width_range)
        
        # Find valleys (negative peaks) by inverting the signal
        valleys, valley_properties = find_peaks(-data, 
                                              prominence=prominence_threshold,
                                              width=width_range)
        
        # Create masks for peaks and their surrounding regions
        event_mask = np.zeros_like(data, dtype=bool)
        
        # Function to add peak/valley regions to mask
        def add_region_to_mask(indices, widths):
            for idx, width in zip(indices, widths):
                left_idx = max(0, int(idx - width))
                right_idx = min(len(data), int(idx + width + 1))
                event_mask[left_idx:right_idx] = True
        
        # Add peak regions to mask
        add_region_to_mask(peaks, properties['widths'])
        # Add valley regions to mask
        add_region_to_mask(valleys, valley_properties['widths'])
        
        # 2. Separate Signal Components
        # Extract events
        events = np.zeros_like(data)
        events[event_mask] = data[event_mask]
        
        # Create baseline by removing events
        baseline = data.copy()
        baseline[event_mask] = np.interp(
            np.where(event_mask)[0],
            np.where(~event_mask)[0],
            baseline[~event_mask]
        )
        
        # 3. Filter Baseline
        filtered_baseline = savgol_filter(baseline, window_length, polyorder)
        
        # 4. Reconstruct Signal
        # Add events back to filtered baseline
        filtered_data = filtered_baseline + events - baseline[event_mask].mean()
        
        # 5. Optional: Smooth Transitions
        # Find edges of event regions
        edges = np.where(np.diff(event_mask.astype(int)) != 0)[0]
        
        # Smooth transitions at edges
        for edge in edges:
            if edge > 1 and edge < len(data) - 2:  # Avoid array bounds
                # Create small overlap for smooth transition
                left_idx = max(0, edge - 2)
                right_idx = min(len(data), edge + 3)
                
                # Apply local smoothing at transition points
                transition = np.mean([
                    filtered_data[left_idx:right_idx],
                    savgol_filter(filtered_data[left_idx:right_idx], 5, 2)
                ], axis=0)
                
                filtered_data[left_idx:right_idx] = transition
        
        app_logger.info("Extract-add filter completed successfully")
        return filtered_data
        
    except Exception as e:
        app_logger.error(f"Error in extract-add filtering: {str(e)}")
        raise


def get_filter_info(filter_name):
    """
    Get information about a specific filter.
    
    Args:
        filter_name (str): Name of the filter
        
    Returns:
        dict: Dictionary containing filter information
    """
    filter_info = {
        'savitzky_golay': {
            'description': 'Smooths data using local polynomial regression',
            'parameters': {
                'window_length': 'Length of the filter window (must be odd)',
                'polyorder': 'Order of the polynomial used for fitting'
            },
            'suitable_for': [
                'Smoothing without shifting peaks',
                'Preserving higher moments of the signal',
                'Data with uniform sampling'
            ]
        },
        'fft': {
            'description': 'Filters noise in frequency domain',
            'parameters': {
                'threshold': 'Threshold for frequency components (0 to 1)'
            },
            'suitable_for': [
                'Removing high-frequency noise',
                'Periodic signals',
                'Frequency-based analysis'
            ]
        },
        'butterworth': {
            'description': 'Low-pass filter with maximally flat response',
            'parameters': {
                'cutoff': 'Cutoff frequency',
                'fs': 'Sampling frequency',
                'order': 'Filter order'
            },
            'suitable_for': [
                'Removing high-frequency noise',
                'Smooth frequency response',
                'Real-time applications'
            ]
        }
    }
    
    return filter_info.get(filter_name, {
        'description': 'Filter information not available',
        'parameters': {},
        'suitable_for': []
    })