#!/usr/bin/env python3
"""
Main entry point for IM-Insight WeChat monitoring.
"""

import logging
import sys
import time
from src.config.loader import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_wxauto_installed():
    """Verify that wxauto is installed."""
    try:
        import wxauto
        logger.info("wxauto library is installed")
        return True
    except ImportError:
        logger.error("wxauto library is not installed. Please install it with: pip install wxauto")
        return False


def main():
    """Main function to run the WeChat monitoring loop."""
    # Load application settings
    try:
        settings = get_settings()
        logger.info(f"Loaded settings for {settings.app.name} v{settings.app.version if hasattr(settings.app, 'version') else '1.0'}")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        sys.exit(1)
    
    # Check if wxauto is installed
    if not check_wxauto_installed():
        raise ImportError("wxauto library is required but not installed")
    
    try:
        # Import our modules
        from src.core.monitor import WeChatClient
        from src.engine.processor import SignalProcessor
        from src.action.exporter import CsvExporter
        
        # Initialize WeChat client with settings
        logger.info("Initializing WeChat client...")
        client = WeChatClient()
        
        # Initialize Processor and Exporter
        logger.info("Initializing Signal Processor and Exporter...")
        processor = SignalProcessor()
        exporter = CsvExporter()
        
        # Main monitoring loop with configurable interval
        logger.info("Starting WeChat monitoring loop...")
        while True:
            try:
                messages = client.get_recent_messages()
                for msg in messages:
                    logger.info(f"New message - Sender: {msg.sender}, Room: {msg.room}, Content: {msg.content[:50]}...")
                    
                    # Process message to extract signal
                    signal = processor.process(msg)
                    
                    # Save signal to CSV
                    exporter.save(signal)
                    
                    # Log confirmation
                    item_display = signal.item if signal.item else "Unknown Item"
                    price_display = signal.price if signal.price is not None else "N/A"
                    group_display = signal.group if signal.group else "Direct Message"
                    logger.info(f"Saved signal from {group_display}: {item_display} @ {price_display}")
                
                # Use configurable polling interval
                scan_interval = settings.ingestion.scan_interval_min
                time.sleep(scan_interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Wait longer on error
                
    except ImportError as e:
        logger.error(f"Import error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()