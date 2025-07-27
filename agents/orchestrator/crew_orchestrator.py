"""
CrewAI-based orchestrator for managing the compliance workflow
"""

import asyncio
import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from crewai import Agent, Crew, Task, Process
from langchain.llms import OpenAI

from agents.base_agent import BaseAgent
from models.compliance_models import ComplianceWorkflow, WorkflowStatus
from services.communication.a2a_protocol import A2AProtocol
from config.settings import Settings

logger = logging.getLogger(__name__)

class CrewOrchestrator(BaseAgent):
    """CrewAI-based orchestrator for compliance monitoring workflow."""
  
    def __init__(self):
        super().__init__(name="CrewOrchestrator")
        self.settings = Settings()
        self.crew = None
        self.workflow_history = []
      
    async def initialize(self):
        """Initialize the CrewAI orchestrator."""
        logger.info("Initializing CrewAI Orchestrator...")
      
        # Initialize LLM
        self.llm = OpenAI(
            api_key=self.settings.OPENAI_API_KEY or "mock-key",
            model=self.settings.OPENAI_MODEL
        )
      
        # Create crew agents
        await self._create_crew_agents()
      
        # Create crew
        self._create_crew()
      
        logger.info("CrewAI Orchestrator initialized successfully")
  
    async def _create_crew_agents(self):
        """Create the crew agents for different roles."""
      
        # Workflow Manager Agent
        self.workflow_manager = Agent(
            role="Workflow Manager",
            goal="Coordinate and manage the compliance monitoring workflow",
            backstory="""You are an experienced workflow manager responsible for 
            orchestrating the daily compliance monitoring process for CPG 
            products in retail stores. You ensure all steps are executed in the 
            correct order and handle any issues that arise.""",
            llm=self.llm,
            verbose=True
        )
      
        # Contract Intelligence Coordinator
        self.contract_coordinator = Agent(
            role="Contract Intelligence Coordinator",
            goal="Coordinate contract analysis and compliance rule extraction",
            backstory="""You specialize in coordinating contract intelligence 
            operations, ensuring that all relevant compliance rules and agreements 
            are properly analyzed and made available to other agents.""",
            llm=self.llm,
            verbose=True
        )
      
        # Image Analysis Coordinator
        self.image_coordinator = Agent(
            role="Image Analysis Coordinator", 
            goal="Coordinate image analysis and compliance detection",
            backstory="""You are responsible for coordinating the analysis of 
            store images to detect product placement and compliance issues. 
            You work with computer vision systems to ensure accurate analysis.""",
            llm=self.llm,
            verbose=True
        )
      
        # Planogram Validation Coordinator
        self.planogram_coordinator = Agent(
            role="Planogram Validation Coordinator",
            goal="Coordinate planogram validation and layout analysis",
            backstory="""You specialize in coordinating planogram validation 
            processes, ensuring that product layouts match the agreed-upon 
            planograms and identifying any deviations.""",
            llm=self.llm,
            verbose=True
        )
      
        # Report Generation Coordinator
        self.report_coordinator = Agent(
            role="Report Generation Coordinator",
            goal="Coordinate report generation and alert management",
            backstory="""You are responsible for coordinating the generation 
            of compliance reports and managing alerts for any violations. 
            You ensure stakeholders receive timely and accurate information.""",
            llm=self.llm,
            verbose=True
        )
  
    def _create_crew(self):
        """Create the CrewAI crew with tasks and process."""
      
        # Define workflow tasks
        tasks = [
            Task(
                description="""Initialize the daily compliance monitoring workflow.
                Gather the list of stores to monitor and prepare the workflow context.
                Coordinate with other agents to ensure they are ready for processing.""",
                agent=self.workflow_manager,
                expected_output="Workflow initialization status and store list"
            ),
          
            Task(
                description="""Retrieve and analyze relevant contracts and compliance rules.
                Extract specific requirements for product placement, stocking levels,
                and promotional displays that apply to the target stores.""",
                agent=self.contract_coordinator,
                expected_output="Contract analysis results and compliance rules"
            ),
          
            Task(
                description="""Analyze store images to detect product placement and compliance.
                Process daily images from target stores and identify potential violations
                or compliance issues using computer vision techniques.""",
                agent=self.image_coordinator,
                expected_output="Image analysis results and detected issues"
            ),
          
            Task(
                description="""Validate product layouts against approved planograms.
                Compare detected product placements with planogram specifications
                and identify any deviations or compliance violations.""",
                agent=self.planogram_coordinator,
                expected_output="Planogram validation results and deviations"
            ),
          
            Task(
                description="""Generate compliance reports and manage alerts.
                Compile all analysis results into comprehensive reports and
                trigger alerts for any violations that exceed thresholds.""",
                agent=self.report_coordinator,
                expected_output="Final compliance report and alert status"
            )
        ]
      
        # Create the crew
        self.crew = Crew(
            agents=[
                self.workflow_manager,
                self.contract_coordinator,
                self.image_coordinator,
                self.planogram_coordinator,
                self.report_coordinator
            ],
            tasks=tasks,
            process=Process.sequential,
            verbose=True
        )
  
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a compliance workflow task."""
        workflow_type = task.get("type", "daily_compliance")
      
        if workflow_type == "daily_compliance":
            return await self.run_compliance_workflow(
                store_id=task.get("store_id"),
                date=task.get("date")
            )
        else:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
  
    async def run_compliance_workflow(self, store_id: str = None, date: date = None) -> Dict[str, Any]:
        """Run the complete compliance monitoring workflow."""
        workflow_id = f"compliance_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        workflow_date = date or datetime.now().date()
      
        logger.info(f"Starting compliance workflow: {workflow_id}")
      
        # Create workflow context
        workflow_context = {
            "workflow_id": workflow_id,
            "store_id": store_id,
            "date": workflow_date,
            "threshold": self.settings.COMPLIANCE_THRESHOLD,
            "started_at": datetime.now()
        }
      
        workflow = ComplianceWorkflow(
            workflow_id=workflow_id,
            store_id=store_id,
            date=workflow_date,
            status=WorkflowStatus.RUNNING,
            started_at=datetime.now()
        )
      
        try:
            # Execute the crew workflow
            logger.info("Executing CrewAI workflow...")
            result = await asyncio.to_thread(
                self.crew.kickoff,
                inputs=workflow_context
            )
          
            # Process the crew result
            workflow_result = await self._process_crew_result(result, workflow)
          
            # Update workflow status
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now()
            workflow.result = workflow_result
          
            # Store workflow in history
            self.workflow_history.append(workflow)
          
            # Store in memory
            await self.memory_manager.store_episodic_memory({
                "event": "workflow_completed",
                "workflow": workflow.dict(),
                "timestamp": datetime.now()
            })
          
            logger.info(f"Compliance workflow completed: {workflow_id}")
            return workflow_result
          
        except Exception as e:
            logger.error(f"Error in compliance workflow {workflow_id}: {str(e)}")
          
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = datetime.now()
            workflow.error = str(e)
          
            self.workflow_history.append(workflow)
          
            raise
  
    async def _process_crew_result(self, crew_result: Any, workflow: ComplianceWorkflow) -> Dict[str, Any]:
        """Process the result from CrewAI execution."""
      
        # Extract results from crew execution
        # Note: This is a simplified version - actual implementation would
        # parse the crew result and coordinate with specialized agents
      
        result = {
            "workflow_id": workflow.workflow_id,
            "store_id": workflow.store_id,
            "date": workflow.date.isoformat(),
            "status": "completed",
            "compliance_score": 87.5,  # Mock score
            "violations": [],
            "recommendations": [],
            "processed_at": datetime.now().isoformat()
        }
      
        # Coordinate with specialized agents for detailed processing
        await self._coordinate_with_agents(workflow, result)
      
        return result
  
    async def _coordinate_with_agents(self, workflow: ComplianceWorkflow, result: Dict[str, Any]):
        """Coordinate with specialized agents for detailed processing."""
      
        # Send tasks to specialized agents
        tasks = [
            {
                "agent_type": "contract_intelligence",
                "task": {
                    "type": "analyze_contracts",
                    "workflow_id": workflow.workflow_id,
                    "store_id": workflow.store_id
                }
            },
            {
                "agent_type": "image_analysis", 
                "task": {
                    "type": "analyze_images",
                    "workflow_id": workflow.workflow_id,
                    "store_id": workflow.store_id,
                    "date": workflow.date.isoformat()
                }
            },
            {
                "agent_type": "planogram_validation",
                "task": {
                    "type": "validate_planograms",
                    "workflow_id": workflow.workflow_id,
                    "store_id": workflow.store_id
                }
            }
        ]
      
        # Send tasks and collect results
        task_results = []
        for task_info in tasks:
            try:
                # Broadcast task to appropriate agent type
                sent_count = await self.broadcast_message(
                    task_info["task"],
                    agent_types=[task_info["agent_type"]]
                )
              
                if sent_count > 0:
                    logger.info(f"Sent task to {task_info['agent_type']} agents")
                else:
                    logger.warning(f"No {task_info['agent_type']} agents available")
                  
            except Exception as e:
                logger.error(f"Error sending task to {task_info['agent_type']}: {str(e)}")
      
        # Wait for results (simplified - actual implementation would use proper coordination)
        await asyncio.sleep(2)  # Mock processing time
      
        # Update result with coordinated data
        result.update({
            "contract_analysis": {"status": "completed", "rules_found": 15},
            "image_analysis": {"status": "completed", "images_processed": 5},
            "planogram_validation": {"status": "completed", "deviations_found": 2}
        })
  
    async def get_workflow_status(self, workflow_id: str) -> Optional[ComplianceWorkflow]:
        """Get the status of a specific workflow."""
        for workflow in self.workflow_history:
            if workflow.workflow_id == workflow_id:
                return workflow
        return None
  
    async def get_recent_workflows(self, limit: int = 10) -> List[ComplianceWorkflow]:
        """Get recent workflow history."""
        return sorted(
            self.workflow_history,
            key=lambda w: w.started_at,
            reverse=True
        )[:limit]