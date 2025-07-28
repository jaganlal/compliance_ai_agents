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
        self.initialized = False
      
    async def initialize(self):
        """Initialize all system components."""
        if self.initialized:
            logger.info("System already initialized")
            return
            
        logger.info("Initializing CPG Compliance Monitoring System...")
      
        try:
            # Initialize services in proper order
            await self.blob_storage.initialize()
            await self.a2a_protocol.initialize()
            
            # CRITICAL: Initialize the orchestrator (this was missing!)
            await self.orchestrator.initialize()
            
            # Setup mock data if in development mode
            if self.settings.ENVIRONMENT == "development":
                await self.setup_mock_data()
            
            self.initialized = True
            logger.info("System initialization complete.")
            
        except Exception as e:
            logger.error(f"Failed to initialize system: {str(e)}")
            raise
  
    async def setup_mock_data(self):
        """Setup mock data for development/testing."""
        logger.info("Setting up mock data...")
      
        try:
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
            
        except Exception as e:
            logger.error(f"Error setting up mock data: {str(e)}")
            # Don't fail initialization if mock data setup fails
  
    async def run_daily_compliance_check(self, store_id: str = None):
        """Run the daily compliance monitoring workflow."""
        # Ensure system is initialized
        if not self.initialized:
            await self.initialize()
            
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
        # Ensure system is initialized
        if not self.initialized:
            await self.initialize()
            
        logger.info("Starting continuous monitoring mode...")
      
        while True:
            try:
                # Run compliance check for all stores
                await self.run_daily_compliance_check()
              
                # Wait for next cycle (configurable interval)
                monitoring_interval = getattr(self.settings, 'MONITORING_INTERVAL', 3600)  # Default 1 hour
                await asyncio.sleep(monitoring_interval)
              
            except KeyboardInterrupt:
                logger.info("Stopping continuous monitoring...")
                break
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def get_compliance_report(self, store_id: str, date: str = None):
        """Get compliance report for a specific store and date."""
        # Ensure system is initialized
        if not self.initialized:
            await self.initialize()
            
        logger.info(f"Getting compliance report for store: {store_id}, date: {date}")
        
        try:
            # Get recent workflows for the store
            recent_workflows = await self.orchestrator.get_recent_workflows(limit=10)
            
            # Filter by store_id if provided
            if store_id:
                recent_workflows = [w for w in recent_workflows if w.store_id == store_id]
            
            # Convert to dict format for JSON serialization
            report = {
                "store_id": store_id,
                "date": date or datetime.now().date().isoformat(),
                "workflows": [
                    {
                        "workflow_id": w.workflow_id,
                        "status": w.status.value,
                        "started_at": w.started_at.isoformat(),
                        "completed_at": w.completed_at.isoformat() if w.completed_at else None,
                        "result": w.result
                    }
                    for w in recent_workflows
                ]
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error getting compliance report: {str(e)}")
            raise
    
    async def shutdown(self):
        """Gracefully shutdown the system."""
        logger.info("Shutting down CPG Compliance Monitoring System...")
        
        try:
            # Shutdown components in reverse order
            if hasattr(self.orchestrator, 'shutdown'):
                await self.orchestrator.shutdown()
            
            if hasattr(self.a2a_protocol, 'shutdown'):
                await self.a2a_protocol.shutdown()
                
            if hasattr(self.blob_storage, 'shutdown'):
                await self.blob_storage.shutdown()
                
            self.initialized = False
            logger.info("System shutdown complete.")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")

# Global system instance
_system_instance = None

async def get_system() -> ComplianceMonitoringSystem:
    """Get or create the global system instance."""
    global _system_instance
    if _system_instance is None:
        _system_instance = ComplianceMonitoringSystem()
        await _system_instance.initialize()
    return _system_instance

async def main():
    """Main application entry point."""
    system = None
    try:
        # Initialize the system
        system = await get_system()
        
        # Run based on configuration
        run_mode = getattr(system.settings, 'RUN_MODE', 'single')
        
        if run_mode == "continuous":
            await system.run_continuous_monitoring()
        else:
            # Single run mode
            result = await system.run_daily_compliance_check("STORE_0001")
            print(f"Compliance check result: {result}")
          
    except KeyboardInterrupt:
        logger.info("Application stopped by user.")
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        raise
    finally:
        if system:
            await system.shutdown()

if __name__ == "__main__":
    asyncio.run(main())