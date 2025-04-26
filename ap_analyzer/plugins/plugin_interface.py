"""
Plugin Interface for DataChaEnhanced

This module defines the interface that all plugins must implement to be compatible
with the DataChaEnhanced application. The application will scan the 'plugins' directory
at startup and load any modules that conform to this interface.

Plugin developers should create a new Python module in the 'plugins' directory
that implements the Plugin class defined here.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class Plugin(ABC):
    """
    Base class for all DataChaEnhanced plugins.
    
    All plugins must inherit from this class and implement its abstract methods.
    The main application will discover and load plugins that properly implement
    this interface at startup.
    
    Example implementation:
    ```python
    from plugin_interface import Plugin
    
    class MyCustomPlugin(Plugin):
        def initialize(self):
            self.name = "My Custom Plugin"
            self.description = "This plugin does something useful"
            self.version = "1.0.0"
            self.results = None
            
        def process(self, data):
            # Process the data
            processed_data = self._my_processing_algorithm(data)
            self.results = processed_data
            return True
            
        def get_results(self):
            return self.results
            
        def _my_processing_algorithm(self, data):
            # Custom processing logic
            return transformed_data
    ```
    """
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the plugin.
        
        This method is called when the plugin is first loaded by the application.
        Use this method to set up any resources, configurations, or state that
        the plugin needs.
        
        Returns:
            None
        """
        pass
    
    @abstractmethod
    def process(self, data: Any) -> bool:
        """
        Process the input data.
        
        This is the main method where the plugin performs its data processing.
        The application will call this method with the data that needs to be processed.
        
        Args:
            data: The input data to process. The type depends on the specific
                 plugin and what kind of data it's designed to handle.
        
        Returns:
            bool: True if processing was successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def get_results(self) -> Any:
        """
        Retrieve the results of the processing.
        
        This method should return the results after the 'process' method has been called.
        
        Returns:
            The processed results. The type depends on the specific plugin.
        """
        pass
    
    def get_metadata(self) -> Dict[str, str]:
        """
        Get plugin metadata.
        
        This method should return metadata about the plugin, such as its name,
        description, version, and author.
        
        Returns:
            Dict[str, str]: A dictionary containing plugin metadata.
        """
        return {
            "name": getattr(self, "name", "Unnamed Plugin"),
            "description": getattr(self, "description", "No description provided"),
            "version": getattr(self, "version", "0.0.0"),
            "author": getattr(self, "author", "Unknown")
        }
    
    def cleanup(self) -> None:
        """
        Clean up any resources used by the plugin.
        
        This method is called when the application is shutting down or when
        the plugin is being unloaded. Use this method to release any resources
        that the plugin has acquired.
        
        Returns:
            None
        """
        pass


# Plugin Loading Information
"""
Plugin Loading Process:

1. The main application scans the 'plugins' directory at startup.
2. For each Python module found, the application attempts to load it.
3. The application looks for classes that inherit from the Plugin base class.
4. For each valid plugin class found, the application:
   - Instantiates the class
   - Calls the 'initialize' method
   - Registers the plugin for later use

Plugin Requirements:
- Must be in a .py file in the 'plugins' directory
- Must contain at least one class that inherits from Plugin
- Must implement all abstract methods: initialize, process, and get_results
- Should not have any code at the module level that performs actions
  (importing modules is fine)

Plugin Best Practices:
- Include comprehensive docstrings
- Handle exceptions gracefully
- Provide meaningful error messages
- Use the cleanup method to release resources
- Set meaningful metadata (name, description, version, author)
"""