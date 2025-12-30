#!/usr/bin/env python3
"""
Main entry point for IM-Insight WeChat monitoring.
"""

import logging
import sys
import time
from datetime import UTC, datetime, timedelta
from src.config.loader import get_settings, load_settings

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
        from src.action.storage import SqliteStore
        from src.action.report import ReportGenerator
        
        # Initialize WeChat client with settings
        logger.info("Initializing WeChat client...")
        client = WeChatClient()
        
        # Initialize Processor and Recorder
        logger.info("Initializing Signal Processor and SQLite store...")
        processor = SignalProcessor()
        store = SqliteStore(
            db_path=settings.storage.db_path,
            raw_retention_days=settings.storage.raw_retention_days
        )
        
        # Main monitoring loop with configurable interval
        logger.info("Starting WeChat monitoring loop...")
        last_report_time = None
        auto_reports_enabled = settings.report.auto_enabled
        if auto_reports_enabled:
            if sys.stdin.isatty():
                choice = input("是否自动生成长期报表（y/n）: ").strip().lower()
                auto_reports_enabled = choice == "y"
            else:
                logger.info("非交互终端，使用配置中的长期报表开关")
        try:
            while True:
                try:
                    messages = client.get_recent_messages()
                    generated_temp_report = False
                    for msg in messages:
                        logger.info(f"New message - Sender: {msg.sender}, Room: {msg.room}, Content: {msg.content[:50]}...")
                        
                        is_trade = processor.is_trade_related(msg)
                        store.save_raw_message(msg, is_trade)
                        if not is_trade:
                            continue

                        # Process message to extract signals
                        signals = processor.process(msg)

                        # Save signals to SQLite
                        if signals:
                            store.save_signals(signals)
                            logger.info(f"{len(signals)} signal(s) recorded to SQLite.")
                    
                    # Cleanup raw messages beyond retention window
                    store.cleanup_raw_messages()

                    # Generate temporary report after new messages arrive
                    if messages and settings.report.temp_goods_whitelist:
                        current_settings = load_settings()
                        generator = ReportGenerator(
                            current_settings.storage.db_path,
                            current_settings.report.output_dir,
                            temp_valid_days=current_settings.report.temp_valid_days,
                        )
                        generator.generate_temporary_goods_report(
                            current_settings.report.temp_goods_whitelist
                        )
                        generated_temp_report = True

                    # Auto-generate long-term reports if enabled
                    if auto_reports_enabled:
                        now = datetime.now(UTC)
                        if (
                            last_report_time is None
                            or now - last_report_time
                            >= timedelta(minutes=settings.report.auto_interval_min)
                        ):
                            current_settings = load_settings()
                            generator = ReportGenerator(
                                current_settings.storage.db_path,
                                current_settings.report.output_dir,
                                temp_valid_days=current_settings.report.temp_valid_days,
                            )
                            generator.generate_aggregate_report()
                            generator.generate_group_reports()
                            last_report_time = now

                    # Use configurable polling interval
                    scan_interval = settings.ingestion.scan_interval_min
                    time.sleep(scan_interval)
                    
                except KeyboardInterrupt:
                    logger.info("Monitoring stopped by user")
                    break
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    time.sleep(5)  # Wait longer on error
        finally:
            # Close recorder file handles
            store.close()
                
    except ImportError as e:
        logger.error(f"Import error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
