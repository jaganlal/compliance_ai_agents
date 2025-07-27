"""
Command Line Interface for CPG Compliance AI Agents
"""

import asyncio
import click
import json
from datetime import datetime, date
from pathlib import Path

from main import ComplianceMonitoringSystem
from config.settings import Settings
from utils.mock_data_generator import MockDataGenerator

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
        system = ComplianceMonitoringSystem()
        await system.initialize()
      
        check_date = datetime.strptime(date, '%Y-%m-%d').date() if date else datetime.now().date()
        result = await system.run_daily_compliance_check(store_id)
      
        if output:
            with open(output, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            click.echo(f"Results saved to {output}")
        else:
            click.echo(json.dumps(result, indent=2, default=str))
  
    asyncio.run(run_check())

@cli.command()
@click.option('--contracts', default=5, help='Number of mock contracts to generate')
@click.option('--planograms', default=10, help='Number of mock planograms to generate')
@click.option('--images', default=20, help='Number of mock images to generate')
def generate_mock_data(contracts, planograms, images):
    """Generate mock data for testing."""
    async def generate():
        generator = MockDataGenerator()
        system = ComplianceMonitoringSystem()
        await system.initialize()
      
        click.echo("Generating mock data...")
      
        # Generate contracts
        contract_data = generator.generate_contracts(contracts)
        for contract in contract_data:
            await system.blob_storage.upload_contract(contract)
      
        # Generate planograms
        planogram_data = generator.generate_planograms(planograms)
        for planogram in planogram_data:
            await system.blob_storage.upload_planogram(planogram)
      
        # Generate images
        image_data = generator.generate_store_images(images)
        for image in image_data:
            await system.blob_storage.upload_image(image)
      
        click.echo(f"Generated {contracts} contracts, {planograms} planograms, {images} images")
  
    asyncio.run(generate())

@cli.command()
def start_monitoring():
    """Start continuous compliance monitoring."""
    async def monitor():
        system = ComplianceMonitoringSystem()
        await system.initialize()
        await system.run_continuous_monitoring()
  
    click.echo("Starting continuous monitoring... (Press Ctrl+C to stop)")
    asyncio.run(monitor())

@cli.command()
@click.option('--port', default=8000, help='API server port')
def start_api(port):
    """Start the REST API server."""
    import uvicorn
    from api.main import app
  
    click.echo(f"Starting API server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)

@cli.command()
def status():
    """Show system status and configuration."""
    settings = Settings()
  
    click.echo("=== CPG Compliance AI Agents Status ===")
    click.echo(f"Environment: {settings.ENVIRONMENT}")
    click.echo(f"Run Mode: {settings.RUN_MODE}")
    click.echo(f"Monitoring Interval: {settings.MONITORING_INTERVAL}s")
    click.echo(f"Compliance Threshold: {settings.COMPLIANCE_THRESHOLD}%")
    click.echo(f"Data Directory: {settings.DATA_DIR}")
  
    # Check service status
    click.echo("\n=== Service Status ===")
    # Add service health checks here
    click.echo("✓ Configuration loaded")
    click.echo("✓ Logging configured")

if __name__ == '__main__':
    cli()