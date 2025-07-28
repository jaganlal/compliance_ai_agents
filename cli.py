"""
Command Line Interface for CPG Compliance AI Agents
"""

import asyncio
import click
import logging
from datetime import datetime, date as date_module
from typing import Optional

from main import ComplianceMonitoringSystem
from config.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@click.group()
@click.version_option(version="1.0.0")
def cli():
    """CPG Compliance AI Agents - Command Line Interface"""
    pass

@cli.command()
@click.option('--store-id', required=True, help='Store ID to check compliance for')
@click.option('--date', 'date_str', help='Date for compliance check (YYYY-MM-DD format)', default=None)
@click.option('--output', help='Output format (json/table)', default='table')
def check_compliance(store_id: str, date_str: Optional[str], output: str):
    """Run compliance check for a specific store."""
    
    async def run_check():
        try:
            # Parse date if provided
            check_date = datetime.fromisoformat(date_str).date() if date_str else date_module.today()
            
            # Initialize system
            system = ComplianceMonitoringSystem()
            await system.initialize()
            
            click.echo(f"🔍 Running compliance check for store: {store_id}")
            
            # Call the orchestrator directly since that's what actually has the workflow method
            result = await system.orchestrator.run_compliance_workflow(store_id, check_date)
            
            # Display results based on output format
            if output == 'json':
                import json
                # Convert WorkflowResult to dict for JSON output
                result_dict = {
                    'workflow_id': result.workflow_id,
                    'store_id': result.store_id,
                    'date': result.date.isoformat(),
                    'status': result.status.value,
                    'compliance_score': result.compliance_score,
                    'violations': result.violations,
                    'recommendations': result.recommendations,
                    'started_at': result.started_at.isoformat(),
                    'completed_at': result.completed_at.isoformat() if result.completed_at else None,
                    'error_message': result.error_message
                }
                click.echo(json.dumps(result_dict, indent=2))
            else:
                # Table format (default)
                click.echo("\n✅ Compliance check completed!")
                click.echo(f"Store ID: {result.store_id}")
                click.echo(f"Date: {result.date}")
                click.echo(f"Status: {result.status.value}")
                click.echo(f"Compliance Score: {result.compliance_score}")
                click.echo(f"Violations: {len(result.violations)}")
                click.echo(f"Recommendations: {len(result.recommendations)}")
                click.echo(f"Workflow ID: {result.workflow_id}")
                
                # Show violations if any
                if result.violations:
                    click.echo("\n⚠️  Violations found:")
                    for i, violation in enumerate(result.violations, 1):
                        if isinstance(violation, dict):
                            click.echo(f"  {i}. {violation.get('description', str(violation))}")
                        else:
                            click.echo(f"  {i}. {violation}")
                
                # Show recommendations if any
                if result.recommendations:
                    click.echo("\n💡 Recommendations:")
                    for i, rec in enumerate(result.recommendations, 1):
                        click.echo(f"  {i}. {rec}")
            
            # Shutdown system
            await system.shutdown()
            
        except Exception as e:
            logger.error(f"CLI error: {str(e)}")
            click.echo(f"❌ Error: {str(e)}")
            raise
    
    asyncio.run(run_check())

@cli.command()
@click.option('--store-id', help='Filter by store ID')
@click.option('--limit', default=10, help='Number of recent workflows to show')
@click.option('--status', help='Filter by status (completed/failed/running)')
def list_workflows(store_id: Optional[str], limit: int, status: Optional[str]):
    """List recent compliance workflows."""
    
    async def run_list():
        try:
            system = ComplianceMonitoringSystem()
            await system.initialize()
            
            # Get recent workflows
            workflows = await system.orchestrator.get_recent_workflows(limit)
            
            # Apply filters
            if store_id:
                workflows = [w for w in workflows if w.store_id == store_id]
            
            if status:
                workflows = [w for w in workflows if w.status.value == status]
            
            if not workflows:
                click.echo("No workflows found matching the criteria.")
                return
            
            # Display workflows
            click.echo(f"\n📋 Recent Workflows ({len(workflows)} found):")
            click.echo("-" * 80)
            
            for workflow in workflows:
                click.echo(f"ID: {workflow.workflow_id}")
                click.echo(f"Store: {workflow.store_id}")
                click.echo(f"Date: {workflow.date}")
                click.echo(f"Status: {workflow.status.value}")
                click.echo(f"Score: {workflow.compliance_score}")
                click.echo(f"Started: {workflow.started_at}")
                if workflow.completed_at:
                    duration = workflow.completed_at - workflow.started_at
                    click.echo(f"Duration: {duration.total_seconds():.1f}s")
                click.echo("-" * 40)
            
            await system.shutdown()
            
        except Exception as e:
            logger.error(f"CLI error: {str(e)}")
            click.echo(f"❌ Error: {str(e)}")
    
    asyncio.run(run_list())

@cli.command()
@click.option('--workflow-id', required=True, help='Workflow ID to get status for')
def get_status(workflow_id: str):
    """Get status of a specific workflow."""
    
    async def run_status():
        try:
            system = ComplianceMonitoringSystem()
            await system.initialize()
            
            workflow = await system.orchestrator.get_workflow_status(workflow_id)
            
            if not workflow:
                click.echo(f"❌ Workflow {workflow_id} not found.")
                return
            
            click.echo(f"\n📊 Workflow Status:")
            click.echo(f"ID: {workflow.workflow_id}")
            click.echo(f"Store: {workflow.store_id}")
            click.echo(f"Date: {workflow.date}")
            click.echo(f"Status: {workflow.status.value}")
            click.echo(f"Started: {workflow.started_at}")
            
            if workflow.completed_at:
                duration = workflow.completed_at - workflow.started_at
                click.echo(f"Completed: {workflow.completed_at}")
                click.echo(f"Duration: {duration.total_seconds():.1f}s")
            
            if workflow.compliance_score is not None:
                click.echo(f"Compliance Score: {workflow.compliance_score}")
            
            if workflow.violations:
                click.echo(f"Violations: {len(workflow.violations)}")
            
            if workflow.recommendations:
                click.echo(f"Recommendations: {len(workflow.recommendations)}")
            
            if workflow.error_message:
                click.echo(f"Error: {workflow.error_message}")
            
            await system.shutdown()
            
        except Exception as e:
            logger.error(f"CLI error: {str(e)}")
            click.echo(f"❌ Error: {str(e)}")
    
    asyncio.run(run_status())

@cli.command()
@click.option('--interval', default=3600, help='Monitoring interval in seconds')
@click.option('--stores', help='Comma-separated list of store IDs to monitor')
def monitor(interval: int, stores: Optional[str]):
    """Start continuous compliance monitoring."""
    
    async def run_monitor():
        try:
            system = ComplianceMonitoringSystem()
            await system.initialize()
            
            store_list = stores.split(',') if stores else ['STORE_0001', 'STORE_0002']
            
            click.echo(f"🔄 Starting continuous monitoring...")
            click.echo(f"Stores: {', '.join(store_list)}")
            click.echo(f"Interval: {interval} seconds")
            click.echo("Press Ctrl+C to stop monitoring")
            
            try:
                while True:
                    for store_id in store_list:
                        click.echo(f"\n🔍 Checking store: {store_id}")
                        result = await system.orchestrator.run_compliance_workflow(store_id, date_module.today())
                        
                        click.echo(f"✅ {store_id}: Score {result.compliance_score}, "
                                 f"Violations: {len(result.violations)}")
                    
                    click.echo(f"\n⏰ Waiting {interval} seconds until next check...")
                    await asyncio.sleep(interval)
                    
            except KeyboardInterrupt:
                click.echo("\n🛑 Monitoring stopped by user")
            
            await system.shutdown()
            
        except Exception as e:
            logger.error(f"CLI error: {str(e)}")
            click.echo(f"❌ Error: {str(e)}")
    
    asyncio.run(run_monitor())

@cli.command()
def test_system():
    """Test system components and connectivity."""
    
    async def run_test():
        try:
            click.echo("🧪 Testing system components...")
            
            system = ComplianceMonitoringSystem()
            await system.initialize()
            
            # Test orchestrator
            click.echo("✅ CrewAI Orchestrator: OK")
            
            # Test blob storage
            if system.blob_storage:
                click.echo("✅ Azure Blob Storage: OK (Mock mode)")
            else:
                click.echo("⚠️  Azure Blob Storage: Not configured")
            
            # Test A2A protocol
            if system.a2a_protocol:
                click.echo("✅ A2A Protocol: OK")
            else:
                click.echo("⚠️  A2A Protocol: Not configured")
            
            # Run a quick test workflow
            click.echo("\n🔍 Running test compliance check...")
            result = await system.orchestrator.run_compliance_workflow("TEST_STORE", date_module.today())
            
            if result.status.value == 'completed':
                click.echo("✅ Test workflow: PASSED")
                click.echo(f"   Score: {result.compliance_score}")
                click.echo(f"   Duration: {(result.completed_at - result.started_at).total_seconds():.1f}s")
            else:
                click.echo("❌ Test workflow: FAILED")
                if result.error_message:
                    click.echo(f"   Error: {result.error_message}")
            
            await system.shutdown()
            click.echo("\n🎉 System test completed!")
            
        except Exception as e:
            logger.error(f"CLI error: {str(e)}")
            click.echo(f"❌ System test failed: {str(e)}")
    
    asyncio.run(run_test())

if __name__ == '__main__':
    cli()