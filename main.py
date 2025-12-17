#!/usr/bin/env python3
"""
Main entry point for IM-Insight WeChat monitoring.
"""

import logging
import sys
import time

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
    # Check if wxauto is installed
    if not check_wxauto_installed():
        raise ImportError("wxauto library is required but not installed")
    
    try:
        # Import our modules
        from src.core.monitor import WeChatClient
        
        # Initialize WeChat client
        logger.info("Initializing WeChat client...")
        client = WeChatClient()
        
        # Main monitoring loop
        logger.info("Starting WeChat monitoring loop...")
        while True:
            try:
                messages = client.get_recent_messages()
                for msg in messages:
                    logger.info(f"New message - Sender: {msg.sender}, Room: {msg.room}, Content: {msg.content[:50]}...")
                
                # Poll every 1 second
                time.sleep(1)
                
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