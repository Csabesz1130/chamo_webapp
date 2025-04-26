"""
AI Dashboard module for visualizing model performance metrics, 
prediction confidence, and explanation summaries.
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
from typing import Dict, List, Optional, Tuple, Any, Callable

from src.utils.logger import app_logger


class AIDashboardTab:
    """
    A tkinter-based dashboard for displaying AI model metrics, 
    predictions, and explanations.
    """
    
    def __init__(self, notebook, update_callback=None):
        """
        Initialize the AI Dashboard tab.
        
        Args:
            notebook: The parent notebook widget
            update_callback: Optional callback for updates
        """
        self.frame = ttk.Frame(notebook)
        self.update_callback = update_callback
        self.signal_analyzer = None
        self.continuous_learner = None
        self.refresh_interval = 5000  # ms
        self.is_updating = False
        self.last_predictions = []
        self.confidence_history = []
        self.performance_metrics = {}
        
        # Setup the UI components
        self._setup_ui()
        
        # Start periodic updates
        self._schedule_update()
        
        app_logger.info("AI Dashboard initialized")
    
    def _setup_ui(self):
        """Set up the user interface components."""
        # Create main container with sections
        main_container = ttk.PanedWindow(self.frame, orient='vertical')
        main_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Top section - Performance metrics
        self.metrics_frame = ttk.LabelFrame(main_container, text="Model Performance Metrics")
        
        # Middle section - Predictions and confidence
        self.predictions_frame = ttk.LabelFrame(main_container, text="Latest Predictions")
        
        # Bottom section - Explanations
        self.explanations_frame = ttk.LabelFrame(main_container, text="Model Explanations")
        
        # Add frames to PanedWindow
        main_container.add(self.metrics_frame, weight=1)
        main_container.add(self.predictions_frame, weight=2)
        main_container.add(self.explanations_frame, weight=2)
        
        # Setup each section's content
        self._setup_metrics_section()
        self._setup_predictions_section()
        self._setup_explanations_section()
        
        # Add refresh controls
        self._setup_refresh_controls()
    
    def _setup_metrics_section(self):
        """Set up the performance metrics section."""
        # Create a frame for metrics display
        metrics_display = ttk.Frame(self.metrics_frame)
        metrics_display.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create labels for metrics
        self.accuracy_var = tk.StringVar(value="Accuracy: N/A")
        self.precision_var = tk.StringVar(value="Precision: N/A")
        self.recall_var = tk.StringVar(value="Recall: N/A")
        self.f1_var = tk.StringVar(value="F1 Score: N/A")
        
        # Add labels to the frame
        ttk.Label(metrics_display, textvariable=self.accuracy_var).pack(anchor='w', pady=2)
        ttk.Label(metrics_display, textvariable=self.precision_var).pack(anchor='w', pady=2)
        ttk.Label(metrics_display, textvariable=self.recall_var).pack(anchor='w', pady=2)
        ttk.Label(metrics_display, textvariable=self.f1_var).pack(anchor='w', pady=2)
        
        # Create figure for metrics chart
        self.metrics_fig = Figure(figsize=(5, 2), dpi=100)
        self.metrics_ax = self.metrics_fig.add_subplot(111)
        self.metrics_canvas = FigureCanvasTkAgg(self.metrics_fig, master=metrics_display)
        self.metrics_canvas.draw()
        self.metrics_canvas.get_tk_widget().pack(fill='both', expand=True, pady=5)
        
        # Initialize the metrics chart
        self._update_metrics_chart()
    
    def _setup_predictions_section(self):
        """Set up the predictions and confidence section."""
        # Create a frame for predictions display
        predictions_display = ttk.Frame(self.predictions_frame)
        predictions_display.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Left side - Latest predictions list
        predictions_list_frame = ttk.Frame(predictions_display)
        predictions_list_frame.pack(side='left', fill='both', expand=True)
        
        ttk.Label(predictions_list_frame, text="Recent Predictions:").pack(anchor='w')
        
        # Create a listbox for predictions
        self.predictions_listbox = tk.Listbox(predictions_list_frame, height=8)
        self.predictions_listbox.pack(fill='both', expand=True, pady=5)
        
        # Right side - Confidence chart
        confidence_chart_frame = ttk.Frame(predictions_display)
        confidence_chart_frame.pack(side='right', fill='both', expand=True)
        
        # Create figure for confidence chart
        self.confidence_fig = Figure(figsize=(5, 3), dpi=100)
        self.confidence_ax = self.confidence_fig.add_subplot(111)
        self.confidence_canvas = FigureCanvasTkAgg(self.confidence_fig, master=confidence_chart_frame)
        self.confidence_canvas.draw()
        self.confidence_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Initialize the confidence chart
        self._update_confidence_chart()
    
    def _setup_explanations_section(self):
        """Set up the model explanations section."""
        # Create a frame for explanations display
        explanations_display = ttk.Frame(self.explanations_frame)
        explanations_display.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create a text widget for explanation summaries
        ttk.Label(explanations_display, text="Explanation Summary:").pack(anchor='w')
        
        self.explanation_text = tk.Text(explanations_display, height=6, wrap='word')
        self.explanation_text.pack(fill='both', expand=True, pady=5)
        self.explanation_text.insert('1.0', "No explanations available yet.")
        self.explanation_text.config(state='disabled')
        
        # Create figure for SHAP values visualization
        ttk.Label(explanations_display, text="Feature Importance (SHAP Values):").pack(anchor='w')
        
        self.shap_fig = Figure(figsize=(5, 3), dpi=100)
        self.shap_ax = self.shap_fig.add_subplot(111)
        self.shap_canvas = FigureCanvasTkAgg(self.shap_fig, master=explanations_display)
        self.shap_canvas.draw()
        self.shap_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Initialize the SHAP chart
        self._update_shap_chart()
    
    def _setup_refresh_controls(self):
        """Set up refresh controls."""
        refresh_frame = ttk.Frame(self.frame)
        refresh_frame.pack(fill='x', padx=5, pady=5)
        
        # Refresh interval control
        ttk.Label(refresh_frame, text="Refresh Interval (s):").pack(side='left', padx=5)
        
        self.refresh_var = tk.StringVar(value=str(self.refresh_interval // 1000))
        refresh_entry = ttk.Entry(refresh_frame, textvariable=self.refresh_var, width=5)
        refresh_entry.pack(side='left', padx=5)
        
        # Apply button
        ttk.Button(refresh_frame, text="Apply", 
                  command=self._update_refresh_interval).pack(side='left', padx=5)
        
        # Manual refresh button
        ttk.Button(refresh_frame, text="Refresh Now", 
                  command=self.refresh_dashboard).pack(side='right', padx=5)
    
    def _update_refresh_interval(self):
        """Update the refresh interval based on user input."""
        try:
            interval_seconds = float(self.refresh_var.get())
            self.refresh_interval = int(interval_seconds * 1000)  # Convert to milliseconds
            app_logger.info(f"Dashboard refresh interval updated to {interval_seconds} seconds")
            
            # Reschedule updates with new interval
            self._schedule_update()
        except ValueError:
            app_logger.error("Invalid refresh interval value")
    
    def _schedule_update(self):
        """Schedule the next dashboard update."""
        # Cancel any existing scheduled update
        if hasattr(self, '_update_job') and self._update_job:
            self.frame.after_cancel(self._update_job)
        
        # Schedule new update
        self._update_job = self.frame.after(self.refresh_interval, self._periodic_update)
    
    def _periodic_update(self):
        """Perform periodic dashboard updates."""
        if not self.is_updating:
            self.is_updating = True
            try:
                self.refresh_dashboard()
            finally:
                self.is_updating = False
            
            # Schedule next update
            self._schedule_update()
    
    def refresh_dashboard(self):
        """Refresh all dashboard components with latest data."""
        app_logger.debug("Refreshing AI dashboard")
        
        # Fetch latest data from AI modules
        self._fetch_latest_data()
        
        # Update UI components
        self._update_metrics_display()
        self._update_predictions_display()
        self._update_explanations_display()
        
        # Redraw charts
        self._update_metrics_chart()
        self._update_confidence_chart()
        self._update_shap_chart()
        
        app_logger.debug("AI dashboard refresh complete")
    
    def _fetch_latest_data(self):
        """Fetch the latest data from AI modules."""
        # This would normally connect to the SignalAnalyzer and continuous_learning modules
        # For now, we'll use placeholder data
        
        # Example of how to fetch data from SignalAnalyzer if available
        if self.signal_analyzer:
            try:
                # This is pseudocode - actual implementation would depend on SignalAnalyzer API
                latest_analysis = self.signal_analyzer.get_latest_analysis()
                if latest_analysis:
                    self._process_analysis_results(latest_analysis)
            except Exception as e:
                app_logger.error(f"Error fetching data from SignalAnalyzer: {e}")
        
        # Example of how to fetch data from continuous_learning module if available
        if self.continuous_learner:
            try:
                # This is pseudocode - actual implementation would depend on continuous_learning API
                performance_metrics = self.continuous_learner.get_performance_metrics()
                if performance_metrics:
                    self.performance_metrics = performance_metrics
            except Exception as e:
                app_logger.error(f"Error fetching data from continuous learning module: {e}")
        
        # For demonstration, generate some placeholder data
        self._generate_placeholder_data()
    
    def _process_analysis_results(self, analysis_results):
        """Process analysis results from SignalAnalyzer."""
        # This would extract relevant information from analysis results
        # and update the dashboard data structures
        pass
    
    def _generate_placeholder_data(self):
        """Generate placeholder data for demonstration."""
        # Update performance metrics
        self.performance_metrics = {
            'accuracy': np.random.uniform(0.75, 0.95),
            'precision': np.random.uniform(0.70, 0.90),
            'recall': np.random.uniform(0.65, 0.85),
            'f1': np.random.uniform(0.70, 0.90)
        }
        
        # Generate a new prediction
        prediction_types = ['Normal Signal', 'Anomaly Detected', 'Noise Pattern', 'Action Potential']
        confidence = np.random.uniform(0.6, 0.99)
        prediction = {
            'type': np.random.choice(prediction_types),
            'confidence': confidence,
            'timestamp': time.strftime('%H:%M:%S')
        }
        
        # Add to history (limit to last 10)
        self.last_predictions.insert(0, prediction)
        if len(self.last_predictions) > 10:
            self.last_predictions = self.last_predictions[:10]
        
        # Update confidence history
        self.confidence_history.append(confidence)
        if len(self.confidence_history) > 20:
            self.confidence_history = self.confidence_history[-20:]
    
    def _update_metrics_display(self):
        """Update the metrics display with latest values."""
        # Update metrics text variables
        if self.performance_metrics:
            self.accuracy_var.set(f"Accuracy: {self.performance_metrics.get('accuracy', 'N/A'):.2f}")
            self.precision_var.set(f"Precision: {self.performance_metrics.get('precision', 'N/A'):.2f}")
            self.recall_var.set(f"Recall: {self.performance_metrics.get('recall', 'N/A'):.2f}")
            self.f1_var.set(f"F1 Score: {self.performance_metrics.get('f1', 'N/A'):.2f}")
    
    def _update_predictions_display(self):
        """Update the predictions display with latest values."""
        # Clear and update predictions listbox
        self.predictions_listbox.delete(0, tk.END)
        
        for pred in self.last_predictions:
            pred_text = f"{pred['timestamp']} - {pred['type']} ({pred['confidence']:.2f})"
            self.predictions_listbox.insert(tk.END, pred_text)
    
    def _update_explanations_display(self):
        """Update the explanations display with latest values."""
        # Generate a simple explanation summary
        if self.last_predictions:
            latest_pred = self.last_predictions[0]
            explanation = self._generate_explanation_text(latest_pred)
            
            # Update explanation text
            self.explanation_text.config(state='normal')
            self.explanation_text.delete('1.0', tk.END)
            self.explanation_text.insert('1.0', explanation)
            self.explanation_text.config(state='disabled')
    
    def _generate_explanation_text(self, prediction):
        """Generate explanation text for a prediction."""
        pred_type = prediction['type']
        confidence = prediction['confidence']
        
        explanations = {
            'Normal Signal': (
                f"The model identified this as a Normal Signal with {confidence:.2f} confidence. "
                "Key factors were the regular waveform pattern and absence of significant anomalies. "
                "The signal shows expected amplitude and frequency characteristics."
            ),
            'Anomaly Detected': (
                f"Anomaly detected with {confidence:.2f} confidence. "
                "The model identified unusual patterns in signal amplitude and frequency. "
                "This may indicate interference or biological activity of interest."
            ),
            'Noise Pattern': (
                f"Noise pattern identified with {confidence:.2f} confidence. "
                "The signal shows characteristics of environmental or equipment noise. "
                "Consider applying additional filtering before analysis."
            ),
            'Action Potential': (
                f"Action potential detected with {confidence:.2f} confidence. "
                "The signal displays the characteristic rapid depolarization and repolarization pattern. "
                "Key features include the spike amplitude and recovery phase timing."
            )
        }
        
        return explanations.get(pred_type, "No explanation available for this prediction type.")
    
    def _update_metrics_chart(self):
        """Update the metrics chart with latest values."""
        # Clear previous plot
        self.metrics_ax.clear()
        
        if self.performance_metrics:
            # Extract metrics
            metrics = ['Accuracy', 'Precision', 'Recall', 'F1']
            values = [
                self.performance_metrics.get('accuracy', 0),
                self.performance_metrics.get('precision', 0),
                self.performance_metrics.get('recall', 0),
                self.performance_metrics.get('f1', 0)
            ]
            
            # Create bar chart
            bars = self.metrics_ax.bar(metrics, values, color='skyblue')
            
            # Add value labels on top of bars
            for bar in bars:
                height = bar.get_height()
                self.metrics_ax.text(
                    bar.get_x() + bar.get_width()/2.,
                    height + 0.01,
                    f'{height:.2f}',
                    ha='center', va='bottom', fontsize=8
                )
            
            # Set y-axis limits
            self.metrics_ax.set_ylim(0, 1.1)
            
            # Remove spines
            for spine in ['top', 'right']:
                self.metrics_ax.spines[spine].set_visible(False)
        
        # Update the canvas
        self.metrics_fig.tight_layout()
        self.metrics_canvas.draw()
    
    def _update_confidence_chart(self):
        """Update the confidence chart with latest values."""
        # Clear previous plot
        self.confidence_ax.clear()
        
        if self.confidence_history:
            # Plot confidence history
            x = range(len(self.confidence_history))
            self.confidence_ax.plot(x, self.confidence_history, 'o-', color='green')
            
            # Set labels and limits
            self.confidence_ax.set_xlabel('Prediction')
            self.confidence_ax.set_ylabel('Confidence')
            self.confidence_ax.set_ylim(0, 1.1)
            
            # Remove spines
            for spine in ['top', 'right']:
                self.confidence_ax.spines[spine].set_visible(False)
        
        # Update the canvas
        self.confidence_fig.tight_layout()
        self.confidence_canvas.draw()
    
    def _update_shap_chart(self):
        """Update the SHAP values chart with latest values."""
        # Clear previous plot
        self.shap_ax.clear()
        
        # Generate placeholder SHAP values for demonstration
        features = ['Feature 1', 'Feature 2', 'Feature 3', 'Feature 4', 'Feature 5']
        importance = np.random.uniform(0, 1, size=len(features))
        importance = importance / importance.sum()  # Normalize
        
        # Sort by importance
        sorted_idx = np.argsort(importance)
        sorted_features = [features[i] for i in sorted_idx]
        sorted_importance = importance[sorted_idx]
        
        # Create horizontal bar chart
        bars = self.shap_ax.barh(sorted_features, sorted_importance, color='coral')
        
        # Add value labels
        for bar in bars:
            width = bar.get_width()
            self.shap_ax.text(
                width + 0.01,
                bar.get_y() + bar.get_height()/2.,
                f'{width:.2f}',
                ha='left', va='center', fontsize=8
            )
        
        # Set labels and title
        self.shap_ax.set_xlabel('Relative Importance')
        
        # Remove spines
        for spine in ['top', 'right']:
            self.shap_ax.spines[spine].set_visible(False)
        
        # Update the canvas
        self.shap_fig.tight_layout()
        self.shap_canvas.draw()
    
    def set_signal_analyzer(self, analyzer):
        """Set the SignalAnalyzer instance for data retrieval."""
        self.signal_analyzer = analyzer
        app_logger.info("SignalAnalyzer connected to dashboard")
    
    def set_continuous_learner(self, learner):
        """Set the continuous learning module instance for data retrieval."""
        self.continuous_learner = learner
        app_logger.info("Continuous learning module connected to dashboard")
    
    def update_with_analysis(self, analysis_results):
        """
        Update the dashboard with new analysis results.
        
        Args:
            analysis_results: Results from SignalAnalyzer
        """
        if not analysis_results:
            return
        
        app_logger.debug("Updating dashboard with new analysis results")
        
        # Process the analysis results
        self._process_analysis_results(analysis_results)
        
        # Refresh the dashboard
        self.refresh_dashboard()