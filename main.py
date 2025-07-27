"""
CPG Compliance AI Agents - Main Application
Entry point for the autonomous compliance monitoring system.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from config.settings import Settings
from config.logging_config import setup_logging
from agents.orchestrator.crew_orchestrator import CrewOrchestrator
from services.azure_services.blob_storage import BlobStorageService
from services.communication.a2a_protocol import A2AProtocol
from utils.mock_data_generator import MockDataGenerator

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class ComplianceMonitoringSystem:
    """Main system orchestrator for compliance monitoring."""
  
    def __init__(self):
        self.settings = Settings()
        self.orchestrator = CrewOrchestrator()
        self.blob_storage = BlobStorageService()
        self.a2a_protocol = A2AProtocol()
        self.mock_generator = MockDataGenerator()
      
    async def initialize(self):
        """Initialize all system components."""
        logger.info("Initializing CPG Compliance Monitoring System...")
      
        # Initialize services
        await self.blob_storage.initialize()
        await self.a2a_protocol.initialize()
      
        # Setup mock data if in development mode
        if self.settings.ENVIRONMENT == "development":
            await self.setup_mock_data()
          
        logger.info("System initialization complete.")
  
    async def setup_mock_data(self):
        """Setup mock data for development/testing."""
        logger.info("Setting up mock data...")
      
        # Generate mock contracts
        contracts = self.mock_generator.generate_contracts(5)
        for contract in contracts:
            await self.blob_storage.upload_contract(contract)
          
        # Generate mock planograms
        planograms = self.mock_generator.generate_planograms(10)
        for planogram in planograms:
            await self.blob_storage.upload_planogram(planogram)
          
        # Generate mock store images
        images = self.mock_generator.generate_store_images(20)
        for image in images:
            await self.blob_storage.upload_image(image)
          
        logger.info("Mock data setup complete.")
  
    async def run_daily_compliance_check(self, store_id: str = None):
        """Run the daily compliance monitoring workflow."""
        logger.info(f"Starting daily compliance check for store: {store_id or 'all stores'}")
      
        try:
            # Start the orchestrated workflow
            result = await self.orchestrator.run_compliance_workflow(
                store_id=store_id,
                date=datetime.now().date()
            )
          
            logger.info(f"Compliance check completed. Result: {result}")
            return result
          
        except Exception as e:
            logger.error(f"Error during compliance check: {str(e)}")
            raise
  
    async def run_continuous_monitoring(self):
        """Run continuous monitoring mode."""
        logger.info("Starting continuous monitoring mode...")
      
        while True:
            try:
                # Run compliance check for all stores
                await self.run_daily_compliance_check()
              
                # Wait for next cycle (configurable interval)
                await asyncio.sleep(self.settings.MONITORING_INTERVAL)
              
            except KeyboardInterrupt:
                logger.info("Stopping continuous monitoring...")
                break
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying

async def main():
    """Main application entry point."""
    system = ComplianceMonitoringSystem()
  
    try:
        await system.initialize()
      
        # Run based on configuration
        if system.settings.RUN_MODE == "continuous":
            await system.run_continuous_monitoring()
        else:
            # Single run mode
            result = await system.run_daily_compliance_check()
            print(f"Compliance check result: {result}")
          
    except KeyboardInterrupt:
        logger.info("Application stopped by user.")
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())