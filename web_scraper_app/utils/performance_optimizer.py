"""
Performance optimization utilities for the application
"""

import gc
import sys
import psutil
import threading
import time
from typing import Dict, Any, Optional
from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
import logging


class PerformanceMonitor(QObject):
    """
    Monitor application performance and resource usage
    """
    
    memory_warning = pyqtSignal(float)  # Memory usage percentage
    cpu_warning = pyqtSignal(float)     # CPU usage percentage
    
    def __init__(self):
        super().__init__()
        self.process = psutil.Process()
        self.monitoring_enabled = False
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.check_performance)
        
        # Thresholds for warnings
        self.memory_threshold = 80.0  # 80% of available memory
        self.cpu_threshold = 90.0     # 90% CPU usage
        
        # Performance history
        self.performance_history = {
            'memory': [],
            'cpu': [],
            'timestamps': []
        }
        self.max_history_size = 100
    
    def start_monitoring(self, interval_ms: int = 5000):
        """
        Start performance monitoring
        
        Args:
            interval_ms: Monitoring interval in milliseconds
        """
        self.monitoring_enabled = True
        self.monitor_timer.start(interval_ms)
        logging.info(f"Performance monitoring started (interval: {interval_ms}ms)")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_enabled = False
        self.monitor_timer.stop()
        logging.info("Performance monitoring stopped")
    
    def check_performance(self):
        """Check current performance metrics"""
        if not self.monitoring_enabled:
            return
        
        try:
            # Get memory usage
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            
            # Get CPU usage
            cpu_percent = self.process.cpu_percent()
            
            # Store in history
            current_time = time.time()
            self.performance_history['memory'].append(memory_percent)
            self.performance_history['cpu'].append(cpu_percent)
            self.performance_history['timestamps'].append(current_time)
            
            # Limit history size
            if len(self.performance_history['memory']) > self.max_history_size:
                for key in self.performance_history:
                    self.performance_history[key] = self.performance_history[key][-self.max_history_size:]
            
            # Check thresholds and emit warnings
            if memory_percent > self.memory_threshold:
                self.memory_warning.emit(memory_percent)
            
            if cpu_percent > self.cpu_threshold:
                self.cpu_warning.emit(cpu_percent)
            
            # Log performance data (debug level)
            logging.debug(f"Performance: Memory {memory_percent:.1f}%, CPU {cpu_percent:.1f}%")
            
        except Exception as e:
            logging.error(f"Performance monitoring error: {e}")
    
    def get_current_stats(self) -> Dict[str, Any]:
        """
        Get current performance statistics
        
        Returns:
            Dictionary with current performance data
        """
        try:
            memory_info = self.process.memory_info()
            
            return {
                'memory_percent': self.process.memory_percent(),
                'memory_rss': memory_info.rss / 1024 / 1024,  # MB
                'memory_vms': memory_info.vms / 1024 / 1024,  # MB
                'cpu_percent': self.process.cpu_percent(),
                'num_threads': self.process.num_threads(),
                'open_files': len(self.process.open_files()),
                'connections': len(self.process.connections()),
            }
        except Exception as e:
            logging.error(f"Error getting performance stats: {e}")
            return {}
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary from history
        
        Returns:
            Dictionary with performance summary
        """
        if not self.performance_history['memory']:
            return {}
        
        memory_data = self.performance_history['memory']
        cpu_data = self.performance_history['cpu']
        
        return {
            'memory_avg': sum(memory_data) / len(memory_data),
            'memory_max': max(memory_data),
            'memory_min': min(memory_data),
            'cpu_avg': sum(cpu_data) / len(cpu_data),
            'cpu_max': max(cpu_data),
            'cpu_min': min(cpu_data),
            'samples': len(memory_data)
        }


class MemoryOptimizer:
    """
    Memory optimization utilities
    """
    
    @staticmethod
    def optimize_garbage_collection():
        """Optimize garbage collection settings"""
        # Set more aggressive garbage collection thresholds
        gc.set_threshold(700, 10, 10)
        
        # Force garbage collection
        collected = gc.collect()
        logging.debug(f"Garbage collection freed {collected} objects")
        
        return collected
    
    @staticmethod
    def clear_qt_caches():
        """Clear Qt-specific caches"""
        try:
            app = QApplication.instance()
            if app:
                # Clear Qt's internal caches
                app.processEvents()  # Process pending events
                
                # Force style refresh (clears style caches)
                app.setStyleSheet(app.styleSheet())
                
        except Exception as e:
            logging.error(f"Error clearing Qt caches: {e}")
    
    @staticmethod
    def optimize_memory_usage():
        """Perform comprehensive memory optimization"""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Clear Qt caches
        MemoryOptimizer.clear_qt_caches()
        
        # Run garbage collection
        collected = MemoryOptimizer.optimize_garbage_collection()
        
        # Get final memory usage
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_saved = initial_memory - final_memory
        
        logging.info(f"Memory optimization: {memory_saved:.1f}MB saved, {collected} objects collected")
        
        return {
            'initial_memory_mb': initial_memory,
            'final_memory_mb': final_memory,
            'memory_saved_mb': memory_saved,
            'objects_collected': collected
        }


class StartupOptimizer:
    """
    Startup performance optimization utilities
    """
    
    @staticmethod
    def optimize_qt_application(app: QApplication):
        """
        Apply Qt-specific optimizations
        
        Args:
            app: QApplication instance
        """
        # Performance attributes (PyQt6 compatible)
        try:
            app.setAttribute(app.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings, True)
            app.setAttribute(app.ApplicationAttribute.AA_CompressHighFrequencyEvents, True)
            app.setAttribute(app.ApplicationAttribute.AA_DisableWindowContextHelpButton, True)
            app.setAttribute(app.ApplicationAttribute.AA_ShareOpenGLContexts, True)
        except AttributeError:
            # Some attributes may not be available in all PyQt6 versions
            pass
        
        # Skip UI effects as they may not be available in PyQt6
        try:
            # These may not be available in PyQt6
            pass
        except AttributeError:
            pass
        
        logging.info("Qt application optimizations applied")
    
    @staticmethod
    def preload_modules():
        """Preload commonly used modules to improve startup time"""
        modules_to_preload = [
            'json',
            'csv',
            'sqlite3',
            'urllib.parse',
            'datetime',
            'pathlib',
            'asyncio',
            'concurrent.futures'
        ]
        
        preloaded = 0
        for module_name in modules_to_preload:
            try:
                __import__(module_name)
                preloaded += 1
            except ImportError:
                pass
        
        logging.debug(f"Preloaded {preloaded} modules for faster startup")
        return preloaded
    
    @staticmethod
    def optimize_python_settings():
        """Optimize Python interpreter settings"""
        # Optimize string interning
        sys.intern("") 
        
        # Set recursion limit (if needed)
        current_limit = sys.getrecursionlimit()
        if current_limit < 2000:
            sys.setrecursionlimit(2000)
        
        logging.debug(f"Python optimization: recursion limit set to {sys.getrecursionlimit()}")


class ResourceManager:
    """
    Manage application resources and cleanup
    """
    
    def __init__(self):
        self.cleanup_callbacks = []
        self.resource_timers = {}
    
    def register_cleanup_callback(self, callback, description: str = ""):
        """
        Register a cleanup callback
        
        Args:
            callback: Function to call during cleanup
            description: Description of what the callback does
        """
        self.cleanup_callbacks.append((callback, description))
        logging.debug(f"Registered cleanup callback: {description}")
    
    def schedule_periodic_cleanup(self, interval_minutes: int = 30):
        """
        Schedule periodic resource cleanup
        
        Args:
            interval_minutes: Cleanup interval in minutes
        """
        timer = QTimer()
        timer.timeout.connect(self.perform_periodic_cleanup)
        timer.start(interval_minutes * 60 * 1000)  # Convert to milliseconds
        
        self.resource_timers['periodic_cleanup'] = timer
        logging.info(f"Scheduled periodic cleanup every {interval_minutes} minutes")
    
    def perform_periodic_cleanup(self):
        """Perform periodic resource cleanup"""
        logging.debug("Performing periodic resource cleanup")
        
        # Memory optimization
        result = MemoryOptimizer.optimize_memory_usage()
        
        # Log results
        if result.get('memory_saved_mb', 0) > 1:
            logging.info(f"Periodic cleanup saved {result['memory_saved_mb']:.1f}MB")
    
    def cleanup_all_resources(self):
        """Cleanup all registered resources"""
        logging.info("Starting application resource cleanup")
        
        # Stop all timers
        for timer_name, timer in self.resource_timers.items():
            timer.stop()
            logging.debug(f"Stopped timer: {timer_name}")
        
        # Execute cleanup callbacks
        for callback, description in self.cleanup_callbacks:
            try:
                callback()
                logging.debug(f"Executed cleanup: {description}")
            except Exception as e:
                logging.error(f"Cleanup callback failed ({description}): {e}")
        
        # Final memory cleanup
        MemoryOptimizer.optimize_memory_usage()
        
        logging.info("Application resource cleanup completed")


# Global instances
_performance_monitor = None
_resource_manager = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def get_resource_manager() -> ResourceManager:
    """Get the global resource manager instance"""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager


def setup_performance_optimizations(app: QApplication):
    """
    Setup all performance optimizations
    
    Args:
        app: QApplication instance
    """
    # Apply Qt optimizations
    StartupOptimizer.optimize_qt_application(app)
    
    # Optimize Python settings
    StartupOptimizer.optimize_python_settings()
    
    # Preload modules
    StartupOptimizer.preload_modules()
    
    # Setup memory optimization
    MemoryOptimizer.optimize_garbage_collection()
    
    # Setup resource management
    resource_manager = get_resource_manager()
    resource_manager.schedule_periodic_cleanup(30)  # Every 30 minutes
    
    # Setup performance monitoring (optional)
    performance_monitor = get_performance_monitor()
    performance_monitor.start_monitoring(10000)  # Every 10 seconds
    
    logging.info("Performance optimizations setup completed")