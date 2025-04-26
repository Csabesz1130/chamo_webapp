import numpy as np
from scipy import signal
from scipy.integrate import simps
from scipy.stats import linregress
from src.utils.logger import app_logger

class ActionPotentialProcessor:
    def __init__(self):
        """Initialize the action potential processor"""
        self.data = None
        self.time_data = None
        self.params = {
            'n_cycles': 2,
            't1': 100,  # ms
            't2': 100,  # ms
            'V0': -80,  # mV
            'V1': 100,  # mV
            'V2': 10,   # mV
            'cell_area_cm2': 1.0  # Default membrane area in cm²
        }
        
        # Processed data
        self.processed_data = None
        self.baseline = None
        self.cycles = []
        self.cycle_times = []
        self.cycle_indices = []
        
        # Derived curves
        self.blue_curve = None
        self.magenta_curve = None
        self.purple_hyperpol_curve = None
        self.purple_depol_curve = None
        
        # Status bar
        self.status_callback = None
        
        # Initialize attributes for curves and slices
        self.orange_curve = None
        self._hyperpol_slice = None  # Initialize slice attribute
        self._depol_slice = None    # Initialize slice attribute
        
        self.time = None
        self.filtered_data = None
        self.integrals = {
            'hyperpol': 0,
            'depol': 0
        }
        self.averages = {
            'hyperpol': 0,
            'depol': 0
        }
        self.custom_integration_points = {
            'hyperpol': None,
            'depol': None
        }
        self.use_custom_points = False
        
        app_logger.debug("Action potential processor initialized")

    def set_data(self, data, time_data):
        """Set input data"""
        self.data = np.array(data)
        self.time_data = np.array(time_data)
        app_logger.debug("Input data set")

    def set_status_callback(self, callback):
        """Set status bar update callback"""
        self.status_callback = callback

    def update_status(self, text):
        """Update status bar text"""
        if self.status_callback:
            self.status_callback(text)

    def analyze(self, **params):
        """Perform action potential analysis"""
        app_logger.info("Starting Action Potential Analysis...")
        try:
            # Update parameters
            self.params.update(params)
            app_logger.debug(f"Analysis using parameters: {self.params}")
            
            # --- Signal Processing Steps ---
            app_logger.debug("Step 1: Baseline Correction")
            self.baseline_correction()
            
            app_logger.debug("Step 2: Finding Cycles (if applicable)")
            self.find_cycles() # Note: This might be deprecated by the new method
            
            app_logger.debug("Step 3: Normalizing Signal (if cycles found)")
            self.normalize_signal() # Note: Depends on cycles
            
            # Check if processed_data exists after initial steps
            if self.processed_data is None:
                app_logger.error("processed_data is None after baseline correction. Cannot proceed.")
                raise ValueError("Baseline correction failed to produce data.")
                
            # --- Alternative Method Logic (if applicable) ---
            # Assuming the orange/blue/magenta/purple logic replaces or supplements find_cycles/normalize_signal
            # Let's ensure the main derived curves are calculated regardless
            app_logger.debug("Step 4: Calculating Derived Curves")
            self.calculate_orange_curve_logic() # Assuming this handles orange curve creation
            self.calculate_blue_curve()         # Ensure these use self.processed_data
            self.calculate_magenta_curve()
            self.calculate_purple_curves()    # This should now correctly store slices if data is sufficient
            
            # --- Results Calculation ---
            app_logger.debug("Step 5: Calculating Integral (if cycles found)")
            results = self.calculate_integral() # Depends on cycles found earlier
            
            # --- Final Logging and Return ---
            app_logger.debug("Step 6: Logging Curve Details")
            self.log_curve_details() # *** Ensure this call exists ***
            
            app_logger.info("Analysis completed successfully")
            # Return a dictionary containing all relevant data for plotting/tracking
            # It's better to return the curves explicitly than just processed_data
            return {
                'orange': self.orange_curve,
                'blue': self.blue_curve,
                'magenta': self.magenta_curve,
                'purple_hyperpol': self.purple_hyperpol_curve,
                'purple_depol': self.purple_depol_curve,
                'time': self.time_data,
                'processed': self.processed_data, 
                'integral_info': results 
            }
            
        except Exception as e:
            app_logger.error(f"Error during analysis: {str(e)}", exc_info=True)
            # Optionally return None or empty data structure on error
            return None 

    def baseline_correction(self):
        """Apply baseline correction"""
        baseline_window = self.data[:1000]
        self.baseline = np.median(baseline_window)
        self.processed_data = self.data - self.baseline
        app_logger.info(f"Baseline correction applied: {self.baseline:.2f}")

    def find_cycles(self):
        """Find action potential cycles"""
        sampling_rate = 1.0 / np.mean(np.diff(self.time_data))
        t1_samples = int(self.params['t1'] * sampling_rate / 1000)
        
        # Find peaks with proper threshold
        peaks, _ = signal.find_peaks(-self.processed_data,
                                   prominence=np.std(self.processed_data),
                                   distance=t1_samples)
        
        for i, peak in enumerate(peaks[:self.params['n_cycles']]):
            start = max(0, peak - t1_samples//2)
            end = min(len(self.processed_data), peak + t1_samples*2)
            
            cycle = self.processed_data[start:end]
            cycle_time = self.time_data[start:end] - self.time_data[start]
            
            self.cycles.append(cycle)
            self.cycle_times.append(cycle_time)
            self.cycle_indices.append((start, end))
            app_logger.debug(f"Valid cycle found at index {peak}")

    def normalize_signal(self):
        """Normalize signal to voltage range"""
        if not self.cycles:
            return
            
        baselines = [np.median(cycle[:100]) for cycle in self.cycles]
        baseline = np.mean(baselines)
        min_val = min(np.min(cycle) for cycle in self.cycles)
        
        # Scale to V0-V1 range in mV
        scale_factor = abs(self.params['V1'] - self.params['V0']) / abs(min_val - baseline)
        self.processed_data = (self.processed_data - baseline) * scale_factor + self.params['V0']
        
        # Update cycles with normalized data
        for i, (start, end) in enumerate(self.cycle_indices):
            self.cycles[i] = self.processed_data[start:end]
        
        app_logger.info(f"Signal normalized with scale factor: {scale_factor:.4f}")

    def calculate_blue_curve(self):
        """Calculate voltage-normalized curve"""
        if not self.processed_data is None:
            # Take points 28-827 (800 points)
            self.blue_curve = self.processed_data[28:828]
            app_logger.debug("Blue curve calculated")

    def calculate_magenta_curve(self):
        """Calculate averaged normalized curve"""
        if not self.blue_curve is None:
            # Take points 28-228 (200 points) and average
            self.magenta_curve = np.mean(self.blue_curve[:200])
            app_logger.debug("Magenta curve calculated")

    def calculate_purple_curves(self):
        """Calculate modified peak curves and store slices"""
        app_logger.debug(f"Attempting to calculate purple curves...")
        if self.processed_data is not None:
            data_len = len(self.processed_data)
            app_logger.debug(f"Length of processed_data: {data_len}")
            # Check if data is long enough for the standard slices
            if data_len > 1227: 
                # Define and store slices based on fixed indices
                self._depol_slice = (828, 1028) 
                self._hyperpol_slice = (1028, 1227)
                app_logger.info(f"Sufficient data length ({data_len}). Setting fixed slices: Depol={self._depol_slice}, Hyperpol={self._hyperpol_slice}")
                
                # Hyperpolarization curve
                self.purple_hyperpol_curve = self.processed_data[self._hyperpol_slice[0]:self._hyperpol_slice[1]]
                
                # Depolarization curve
                self.purple_depol_curve = self.processed_data[self._depol_slice[0]:self._depol_slice[1]]
                
                app_logger.info(f"Purple curves calculated from fixed slices.")
            else:
                # Data too short for fixed slices, set everything to None
                app_logger.warning(f"Processed data length ({data_len}) is too short for fixed purple curve slices (needs > 1227). Setting purple curves and slices to None.")
                self.purple_hyperpol_curve = None
                self.purple_depol_curve = None
                self._hyperpol_slice = None
                self._depol_slice = None
        else:
            # Processed data is None
            app_logger.warning("Cannot calculate purple curves because processed_data is None.")
            self.purple_hyperpol_curve = None
            self.purple_depol_curve = None
            self._hyperpol_slice = None
            self._depol_slice = None

    def calculate_integral(self):
        """Calculate integral and capacitance"""
        try:
            if not self.cycles:
                return {
                    'integral_value': 'No cycles found',
                    'capacitance_uF_cm2': 'No cycles found',
                    'cycle_indices': []
                }
                
            # Calculate integral for each cycle
            integrals = []
            for cycle, cycle_time in zip(self.cycles, self.cycle_times):
                integral = simps(cycle, cycle_time)
                integrals.append(integral)
                
            # Calculate average integral
            avg_integral = np.mean(integrals)
            
            # Calculate capacitance
            capacitance = avg_integral / (self.params['V1'] - self.params['V0'])
            capacitance_per_area = capacitance / self.params['cell_area_cm2']
            
            return {
                'integral_value': f"{avg_integral:.2f} pA·ms",
                'capacitance_uF_cm2': f"{capacitance_per_area:.2f} μF/cm²",
                'cycle_indices': self.cycle_indices
            }
            
        except Exception as e:
            app_logger.error(f"Error calculating integral: {str(e)}")
            return {
                'integral_value': f'Error: {str(e)}',
                'capacitance_uF_cm2': 'Error',
                'cycle_indices': []
            }

    def get_regression_line(self, start_idx, end_idx):
        """Calculate regression line for given range"""
        try:
            x = self.time_data[start_idx:end_idx]
            y = self.processed_data[start_idx:end_idx]
            
            slope, intercept, r_value, p_value, std_err = linregress(x, y)
            
            return {
                'slope': slope,
                'intercept': intercept,
                'r_squared': r_value**2,
                'x': x,
                'y': slope * x + intercept
            }
            
        except Exception as e:
            app_logger.error(f"Error calculating regression: {str(e)}")
            return None

    def log_curve_details(self):
        """Log details about calculated curves and slices."""
        app_logger.info("--- Curve Calculation Summary ---")
        app_logger.info(f"Orange curve points: {len(self.orange_curve) if self.orange_curve is not None else 'N/A'}")
        app_logger.info(f"Blue curve points: {len(self.blue_curve) if self.blue_curve is not None else 'N/A'}")
        app_logger.info(f"Magenta curve points: {len(self.magenta_curve) if self.magenta_curve is not None else 'N/A'}")
        app_logger.info(f"Purple Hyperpol points: {len(self.purple_hyperpol_curve) if self.purple_hyperpol_curve is not None else 'N/A'}")
        app_logger.info(f"Purple Depol points: {len(self.purple_depol_curve) if self.purple_depol_curve is not None else 'N/A'}")
        if hasattr(self, '_hyperpol_slice') and self._hyperpol_slice:
            app_logger.info(f"Stored Hyperpol Slice: {self._hyperpol_slice}")
        else:
            app_logger.info("Hyperpol Slice: Not stored or unavailable.")
        if hasattr(self, '_depol_slice') and self._depol_slice:
             app_logger.info(f"Stored Depol Slice: {self._depol_slice}")
        else:
             app_logger.info("Depol Slice: Not stored or unavailable.")
        app_logger.info("-------------------------------")

    def set_custom_integration_points(self, points):
        """Beállítja az egyéni integrálási pontokat."""
        if points is None:
            self.custom_integration_points = {
                'hyperpol': None,
                'depol': None
            }
            self.use_custom_points = False
            return
        
        self.custom_integration_points.update(points)
        self.use_custom_points = True

    def calculate_integrals(self, time, data, ranges):
        """Kiszámítja az integrálokat az adott tartományokon."""
        if self.use_custom_points and self.custom_integration_points:
            # Egyéni pontok használata
            hyperpol_start = self.custom_integration_points['hyperpol']
            depol_start = self.custom_integration_points['depol']
            
            if hyperpol_start is not None:
                ranges['hyperpol'] = (hyperpol_start, ranges['hyperpol'][1])
            if depol_start is not None:
                ranges['depol'] = (depol_start, ranges['depol'][1])
        
        # Integrálok számítása a tartományokon
        self.integrals['hyperpol'] = np.trapz(
            data[ranges['hyperpol'][0]:ranges['hyperpol'][1]],
            time[ranges['hyperpol'][0]:ranges['hyperpol'][1]]
        )
        
        self.integrals['depol'] = np.trapz(
            data[ranges['depol'][0]:ranges['depol'][1]],
            time[ranges['depol'][0]:ranges['depol'][1]]
        )
        
        # Átlagok számítása
        self.averages['hyperpol'] = np.mean(
            data[ranges['hyperpol'][0]:ranges['hyperpol'][1]]
        )
        self.averages['depol'] = np.mean(
            data[ranges['depol'][0]:ranges['depol'][1]]
        )