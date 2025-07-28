"""
Command Line Interface for CPG Compliance AI Agents
"""

import asyncio
import click
import json
import logging
from datetime import datetime, date
from pathlib import Path

from main import get_system, ComplianceMonitoringSystem
from config.settings import Settings
from config.logging_config import setup_logging
from utils.mock_data_generator import MockDataGenerator

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@click.group()
@click.version_option(version="1.0.0")
def cli():
    """CPG Compliance AI Agents CLI"""
    pass

@cli.command()
@click.option('--store-id', help='Specific store ID to check')
@click.option('--date', help='Date for compliance check (YYYY-MM-DD)')
@click.option('--output', '-o', help='Output file for results')
def check_compliance(store_id, date, output):
    """Run compliance check for specified store and date."""
    
    async def run_check():
        system = None
        try:
            # Get the initialized system
            system = await get_system()
            
            # Parse date if provided
            check_date = None
            if date:
                try:
                    check_date = datetime.strptime(date, '%Y-%m-%d').date()
                except ValueError:
                    click.echo(f"❌ Invalid date format: {date}. Use YYYY-MM-DD format.", err=True)
                    return
            
            # Run compliance check
            click.echo(f"🔍 Running compliance check for store: {store_id or 'default'}")
            result = await system.run_daily_compliance_check(store_id)
            
            # Format result for display
            if output:
                with open(output, 'w') as f:
                    json.dump(result, f, indent=2, default=str)
                click.echo(f"✅ Results saved to {output}")
            else:
                # Display formatted results
                click.echo(f"\n✅ Compliance check completed!")
                click.echo(f"Store ID: {result.store_id}")
                click.echo(f"Date: {result.date}")
                click.echo(f"Status: {result.status.value}")
                click.echo(f"Compliance Score: {result.compliance_score or 'N/A'}")
                click.echo(f"Workflow ID: {result.workflow_id or 'N/A'}")
                
                if result.violations:
                    click.echo(f"Violations Found: {len(result['violations'])}")
                
                if result.recommendations:
                    click.echo(f"Recommendations: {len(result['recommendations'])}")
                
                # Show detailed JSON if requested
                if click.confirm('\nShow detailed results?'):
                    click.echo(json.dumps(result, indent=2, default=str))
                    
        except Exception as e:
            logger.error(f"CLI error: {str(e)}")
            click.echo(f"❌ Error: {str(e)}", err=True)
            raise
        finally:
            if system:
                await system.shutdown()
  
    asyncio.run(run_check())

@cli.command()
@click.option('--store-id', help='Specific store ID to get report for')
@click.option('--date', help='Date for report (YYYY-MM-DD)')
@click.option('--output', '-o', help='Output file for report')
def get_report(store_id, date, output):
    """Get compliance report for a specific store."""
    
    async def run_report():
        system = None
        try:
            system = await get_system()
            
            # Get compliance report
            click.echo(f"📊 Getting compliance report for store: {store_id or 'all'}")
            report = await system.get_compliance_report(store_id, date)
            
            if output:
                with open(output, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
                click.echo(f"✅ Report saved to {output}")
            else:
                # Display formatted report
                click.echo(f"\n📊 Compliance Report")
                click.echo(f"Store ID: {report.get('store_id', 'All')}")
                click.echo(f"Date: {report.get('date', 'N/A')}")
                click.echo(f"Workflows Found: {len(report.get('workflows', []))}")
                
                # Show workflow summary
                for workflow in report.get('workflows', [])[:5]:  # Show first 5
                    click.echo(f"  - {workflow['workflow_id']}: {workflow['status']}")
                
                if click.confirm('\nShow detailed report?'):
                    click.echo(json.dumps(report, indent=2, default=str))
                    
        except Exception as e:
            logger.error(f"CLI error: {str(e)}")
            click.echo(f"❌ Error: {str(e)}", err=True)
            raise
        finally:
            if system:
                await system.shutdown()
    
    asyncio.run(run_report())

@cli.command()
@click.option('--contracts', default=5, help='Number of mock contracts to generate')
@click.option('--planograms', default=10, help='Number of mock planograms to generate')
@click.option('--images', default=20, help='Number of mock images to generate')
def generate_mock_data(contracts, planograms, images):
    """Generate mock data for testing."""
    
    async def generate():
        system = None
        try:
            generator = MockDataGenerator()
            system = await get_system()
            
            click.echo("🔧 Generating mock data...")
            
            # Generate contracts
            click.echo(f"Generating {contracts} contracts...")
            contract_data = generator.generate_contracts(contracts)
            for contract in contract_data:
                await system.blob_storage.upload_contract(contract)
            
            # Generate planograms
            click.echo(f"Generating {planograms} planograms...")
            planogram_data = generator.generate_planograms(planograms)
            for planogram in planogram_data:
                await system.blob_storage.upload_planogram(planogram)
            
            # Generate images
            click.echo(f"Generating {images} images...")
            image_data = generator.generate_store_images(images)
            for image in image_data:
                await system.blob_storage.upload_image(image)
            
            click.echo(f"✅ Generated {contracts} contracts, {planograms} planograms, {images} images")
            
        except Exception as e:
            logger.error(f"Mock data generation error: {str(e)}")
            click.echo(f"❌ Error: {str(e)}", err=True)
            raise
        finally:
            if system:
                await system.shutdown()
  
    asyncio.run(generate())

@cli.command()
def start_monitoring():
    """Start continuous compliance monitoring."""
    
    async def monitor():
        system = None
        try:
            system = await get_system()
            click.echo("🔄 Starting continuous monitoring... (Press Ctrl+C to stop)")
            await system.run_continuous_monitoring()
        except KeyboardInterrupt:
            click.echo("\n⏹️  Monitoring stopped by user.")
        except Exception as e:
            logger.error(f"Monitoring error: {str(e)}")
            click.echo(f"❌ Error: {str(e)}", err=True)
            raise
        finally:
            if system:
                await system.shutdown()
  
    asyncio.run(monitor())

@cli.command()
@click.option('--port', default=8000, help='API server port')
def start_api(port):
    """Start the REST API server."""
    try:
        import uvicorn
        from api.main import app
        
        click.echo(f"🚀 Starting API server on port {port}...")
        uvicorn.run(app, host="0.0.0.0", port=port)
    except ImportError:
        click.echo("❌ API dependencies not installed. Install with: pip install uvicorn fastapi", err=True)
    except Exception as e:
        click.echo(f"❌ Error starting API server: {str(e)}", err=True)

@cli.command()
def status():
    """Show system status and configuration."""
    
    async def check_status():
        try:
            settings = Settings()
            
            click.echo("=== CPG Compliance AI Agents Status ===")
            click.echo(f"Environment: {settings.ENVIRONMENT}")
            click.echo(f"Run Mode: {getattr(settings, 'RUN_MODE', 'single')}")
            click.echo(f"Monitoring Interval: {getattr(settings, 'MONITORING_INTERVAL', 3600)}s")
            click.echo(f"Compliance Threshold: {settings.COMPLIANCE_THRESHOLD}%")
            click.echo(f"Data Directory: {settings.DATA_DIR}")
            
            # Check service status
            click.echo("\n=== Service Status ===")
            click.echo("✓ Configuration loaded")
            click.echo("✓ Logging configured")
            
            # Try to initialize system to check health
            try:
                system = await get_system()
                click.echo("✓ System initialization successful")
                click.echo(f"✓ System initialized: {system.initialized}")
                await system.shutdown()
            except Exception as e:
                click.echo(f"❌ System initialization failed: {str(e)}")
                
        except Exception as e:
            logger.error(f"Status check error: {str(e)}")
            click.echo(f"❌ Error checking status: {str(e)}", err=True)
    
    asyncio.run(check_status())

if __name__ == '__main__':
    cli()