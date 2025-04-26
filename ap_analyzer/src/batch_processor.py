"""
Batch processing module for analyzing multiple ATF files.

This module provides functionality to process multiple ATF files in a directory,
apply standard filtering and analysis, and aggregate the results.
"""

import os
import csv
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime

# Import project modules
from src.utils.logger import app_logger
from src.data.atf_handler import ATFHandler  # Assuming this exists
from src.ai.signal_analyzer import SignalAnalyzer
from src.processing.filters import apply_filters  # Assuming this exists
from src.processing.action_potential import analyze_action_potential  # Assuming this exists


class BatchProcessor:
    """
    Class for batch processing of ATF files.
    
    This class provides methods to process multiple ATF files in a directory,
    apply standard filtering and analysis, and aggregate the results.
    """
    
    def __init__(self):
        """Initialize the batch processor."""
        self.signal_analyzer = SignalAnalyzer()
        self.results = []
        self.summary = {}
        app_logger.info("BatchProcessor initialized")
    
    def process_folder(self, folder_path: Union[str, Path], 
                      recursive: bool = False,
                      export_path: Optional[Union[str, Path]] = None,
                      export_format: str = "csv") -> Dict:
        """
        Process all ATF files in the specified folder.
        
        Args:
            folder_path: Path to the folder containing ATF files
            recursive: Whether to search for files recursively in subfolders
            export_path: Path where to export the results (if None, results are not exported)
            export_format: Format to export results ('csv', 'json', or 'excel')
            
        Returns:
            Dictionary containing processing summary
        """
        folder_path = Path(folder_path)
        if not folder_path.exists() or not folder_path.is_dir():
            error_msg = f"Invalid folder path: {folder_path}"
            app_logger.error(error_msg)
            return {"success": False, "message": error_msg}
        
        app_logger.info(f"Starting batch processing in folder: {folder_path}")
        
        # Reset results
        self.results = []
        
        # Find all ATF files
        pattern = "**/*.atf" if recursive else "*.atf"
        atf_files = list(folder_path.glob(pattern))
        
        if not atf_files:
            message = f"No ATF files found in {folder_path}"
            app_logger.warning(message)
            return {"success": False, "message": message}
        
        app_logger.info(f"Found {len(atf_files)} ATF files to process")
        
        # Process each file
        for file_path in atf_files:
            try:
                app_logger.info(f"Processing file: {file_path}")
                data = self.load_atf(file_path)
                if data:
                    result = self.process_data(data, file_path.name)
                    self.aggregate_results(result, file_path.name)
            except Exception as e:
                app_logger.error(f"Error processing file {file_path}: {str(e)}")
        
        # Generate summary
        self.generate_summary()
        
        # Export results if requested
        if export_path:
            self.export_results(export_path, export_format)
        
        return {
            "success": True,
            "message": f"Processed {len(atf_files)} files",
            "files_processed": len(atf_files),
            "results_count": len(self.results),
            "summary": self.summary
        }
    
    def load_atf(self, file_path: Union[str, Path]) -> Optional[Dict]:
        """
        Load an ATF file using the ATFHandler.
        
        Args:
            file_path: Path to the ATF file
            
        Returns:
            Dictionary containing the loaded data or None if loading failed
        """
        try:
            handler = ATFHandler()
            data = handler.load(file_path)
            return data
        except Exception as e:
            app_logger.error(f"Failed to load ATF file {file_path}: {str(e)}")
            return None
    
    def process_data(self, data: Dict, filename: str) -> Dict:
        """
        Process the data from an ATF file.
        
        Args:
            data: Dictionary containing the data from an ATF file
            filename: Name of the file being processed
            
        Returns:
            Dictionary containing the processing results
        """
        app_logger.info(f"Processing data from {filename}")
        
        # Extract time and signal data
        times = data.get('time', np.array([]))
        signal = data.get('signal', np.array([]))
        
        if len(times) == 0 or len(signal) == 0:
            return {
                "filename": filename,
                "success": False,
                "message": "Missing time or signal data"
            }
        
        # Apply filters
        filtered_signal = apply_filters(signal)
        
        # Analyze action potentials
        ap_results = analyze_action_potential(times, filtered_signal)
        
        # AI analysis
        ai_results = self.signal_analyzer.analyze_signal(times, filtered_signal)
        
        # Combine results
        result = {
            "filename": filename,
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "data_points": len(signal),
            "duration": times[-1] - times[0] if len(times) > 0 else 0,
            "action_potential": ap_results,
            "ai_analysis": ai_results
        }
        
        return result
    
    def aggregate_results(self, result: Dict, filename: str) -> None:
        """
        Aggregate the results from processing a file.
        
        Args:
            result: Dictionary containing the processing results
            filename: Name of the file that was processed
        """
        if result.get("success", False):
            self.results.append(result)
            app_logger.info(f"Added results for {filename} to aggregate")
        else:
            app_logger.warning(f"Skipping failed results for {filename}")
    
    def generate_summary(self) -> Dict:
        """
        Generate a summary of the batch processing results.
        
        Returns:
            Dictionary containing the summary
        """
        if not self.results:
            self.summary = {"message": "No results to summarize"}
            return self.summary
        
        # Calculate basic statistics
        successful_files = len(self.results)
        
        # Extract key metrics for summary
        ap_counts = [len(r.get("action_potential", {}).get("peaks", [])) for r in self.results]
        durations = [r.get("duration", 0) for r in self.results]
        
        self.summary = {
            "files_processed": successful_files,
            "average_ap_count": np.mean(ap_counts) if ap_counts else 0,
            "max_ap_count": np.max(ap_counts) if ap_counts else 0,
            "min_ap_count": np.min(ap_counts) if ap_counts else 0,
            "average_duration": np.mean(durations) if durations else 0,
            "timestamp": datetime.now().isoformat()
        }
        
        app_logger.info(f"Generated summary for {successful_files} files")
        return self.summary
    
    def export_results(self, export_path: Union[str, Path], 
                      format: str = "csv") -> bool:
        """
        Export the aggregated results to a file.
        
        Args:
            export_path: Path where to export the results
            format: Format to export results ('csv', 'json', or 'excel')
            
        Returns:
            True if export was successful, False otherwise
        """
        if not self.results:
            app_logger.warning("No results to export")
            return False
        
        export_path = Path(export_path)
        
        # Create directory if it doesn't exist
        export_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if format.lower() == "csv":
                return self._export_to_csv(export_path)
            elif format.lower() == "json":
                return self._export_to_json(export_path)
            elif format.lower() == "excel":
                return self._export_to_excel(export_path)
            else:
                app_logger.error(f"Unsupported export format: {format}")
                return False
        except Exception as e:
            app_logger.error(f"Error exporting results: {str(e)}")
            return False
    
    def _export_to_csv(self, export_path: Path) -> bool:
        """Export results to CSV format."""
        # Flatten the results for CSV export
        flattened_results = []
        
        for result in self.results:
            flat_result = {
                "filename": result.get("filename", ""),
                "timestamp": result.get("timestamp", ""),
                "data_points": result.get("data_points", 0),
                "duration": result.get("duration", 0)
            }
            
            # Add action potential data
            ap_data = result.get("action_potential", {})
            flat_result.update({
                "ap_count": len(ap_data.get("peaks", [])),
                "ap_amplitude_avg": np.mean(ap_data.get("amplitudes", [0])),
                "ap_duration_avg": np.mean(ap_data.get("durations", [0]))
            })
            
            # Add AI analysis data
            ai_data = result.get("ai_analysis", {}).get("data", {})
            flat_result.update({
                "ai_prediction": ai_data.get("prediction", ""),
                "ai_confidence": ai_data.get("confidence", 0)
            })
            
            flattened_results.append(flat_result)
        
        # Write to CSV
        with open(export_path, 'w', newline='') as csvfile:
            if flattened_results:
                fieldnames = flattened_results[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(flattened_results)
        
        # Export summary to a separate file
        summary_path = export_path.with_name(f"{export_path.stem}_summary.csv")
        with open(summary_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for key, value in self.summary.items():
                writer.writerow([key, value])
        
        app_logger.info(f"Exported results to CSV: {export_path}")
        return True
    
    def _export_to_json(self, export_path: Path) -> bool:
        """Export results to JSON format."""
        export_data = {
            "results": self.results,
            "summary": self.summary
        }
        
        with open(export_path, 'w') as jsonfile:
            json.dump(export_data, jsonfile, indent=2)
        
        app_logger.info(f"Exported results to JSON: {export_path}")
        return True
    
    def _export_to_excel(self, export_path: Path) -> bool:
        """Export results to Excel format."""
        # Create a pandas DataFrame from the flattened results
        flattened_results = []
        
        for result in self.results:
            flat_result = {
                "filename": result.get("filename", ""),
                "timestamp": result.get("timestamp", ""),
                "data_points": result.get("data_points", 0),
                "duration": result.get("duration", 0)
            }
            
            # Add action potential data
            ap_data = result.get("action_potential", {})
            flat_result.update({
                "ap_count": len(ap_data.get("peaks", [])),
                "ap_amplitude_avg": np.mean(ap_data.get("amplitudes", [0])),
                "ap_duration_avg": np.mean(ap_data.get("durations", [0]))
            })
            
            # Add AI analysis data
            ai_data = result.get("ai_analysis", {}).get("data", {})
            flat_result.update({
                "ai_prediction": ai_data.get("prediction", ""),
                "ai_confidence": ai_data.get("confidence", 0)
            })
            
            flattened_results.append(flat_result)
        
        # Create DataFrames
        results_df = pd.DataFrame(flattened_results)
        summary_df = pd.DataFrame([self.summary])
        
        # Write to Excel with multiple sheets
        with pd.ExcelWriter(export_path) as writer:
            results_df.to_excel(writer, sheet_name='Results', index=False)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        app_logger.info(f"Exported results to Excel: {export_path}")
        return True


def process_folder(folder_path: Union[str, Path], 
                  export_path: Optional[Union[str, Path]] = None,
                  export_format: str = "csv",
                  recursive: bool = False) -> Dict:
    """
    Process all ATF files in the specified folder.
    
    This is a convenience function that creates a BatchProcessor instance
    and calls its process_folder method.
    
    Args:
        folder_path: Path to the folder containing ATF files
        export_path: Path where to export the results (if None, results are not exported)
        export_format: Format to export results ('csv', 'json', or 'excel')
        recursive: Whether to search for files recursively in subfolders
        
    Returns:
        Dictionary containing processing summary
    """
    processor = BatchProcessor()
    return processor.process_folder(
        folder_path=folder_path,
        export_path=export_path,
        export_format=export_format,
        recursive=recursive
    )


if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch process ATF files')
    parser.add_argument('folder', type=str, help='Folder containing ATF files')
    parser.add_argument('--output', '-o', type=str, help='Output file path')
    parser.add_argument('--format', '-f', type=str, default='csv', 
                        choices=['csv', 'json', 'excel'], help='Output format')
    parser.add_argument('--recursive', '-r', action='store_true', 
                        help='Search recursively in subfolders')
    
    args = parser.parse_args()
    
    result = process_folder(
        folder_path=args.folder,
        export_path=args.output,
        export_format=args.format,
        recursive=args.recursive
    )
    
    print(f"Processing complete: {result['message']}")
    if result['success'] and 'summary' in result:
        print("\nSummary:")
        for key, value in result['summary'].items():
            print(f"  {key}: {value}")