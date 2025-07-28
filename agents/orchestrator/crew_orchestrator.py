"""
CrewAI Orchestrator for CPG Compliance Monitoring
Manages the coordination of AI agents for compliance checking workflows.
"""

import asyncio
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from uuid import uuid4
from enum import Enum

from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from config.settings import Settings
from agents.base_agent import BaseAgent
from services.azure_services.blob_storage import BlobStorageService
from services.communication.a2a_protocol import A2AProtocol

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class WorkflowResult(BaseModel):
    """Result of a compliance workflow execution."""
    workflow_id: str
    store_id: str
    date: date
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    compliance_score: Optional[float] = None
    violations: List[Dict[str, Any]] = []
    recommendations: List[str] = []
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class CrewOrchestrator(BaseAgent):
    """
    Orchestrates CrewAI agents for compliance monitoring workflows.
    """
    
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.blob_storage = BlobStorageService()
        self.a2a_protocol = A2AProtocol()
        
        # CrewAI components
        self.llm = None
        self.agents = []
        self.tasks = []
        self.crew = None
        
        # Workflow tracking
        self.active_workflows: Dict[str, WorkflowResult] = {}
        self.workflow_history: List[WorkflowResult] = []
        
        self.initialized = False
    
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implementation of the abstract method from BaseAgent.
        Processes a compliance monitoring task using CrewAI.
        
        Args:
            task_data: Dictionary containing task information
            
        Returns:
            Dictionary containing the processed task result
        """
        logger.info(f"Processing task with CrewAI: {task_data.get('task_id', 'unknown')}")
        
        try:
            # Extract task parameters
            store_id = task_data.get('store_id')
            date_str = task_data.get('date')
            task_date = datetime.fromisoformat(date_str).date() if date_str else date.today()
            
            # Run the compliance workflow
            workflow_result = await self.run_compliance_workflow(store_id, task_date)
            
            # Convert workflow result to dictionary format expected by BaseAgent
            return {
                'task_id': task_data.get('task_id'),
                'status': workflow_result.status.value,
                'result': workflow_result.result,
                'compliance_score': workflow_result.compliance_score,
                'violations': workflow_result.violations,
                'recommendations': workflow_result.recommendations,
                'completed_at': workflow_result.completed_at.isoformat() if workflow_result.completed_at else None,
                'error_message': workflow_result.error_message
            }
            
        except Exception as e:
            logger.error(f"Error processing task: {str(e)}")
            return {
                'task_id': task_data.get('task_id'),
                'status': 'failed',
                'error_message': str(e),
                'completed_at': datetime.now().isoformat()
            }
    
    async def initialize(self):
        """Initialize the CrewAI orchestrator."""
        if self.initialized:
            logger.info("CrewAI Orchestrator already initialized")
            return
            
        logger.info("Initializing CrewAI Orchestrator...")
        
        try:
            # Initialize LLM
            self._initialize_llm()
            
            # Create agents and tasks
            self._create_agents()
            self._create_tasks()
            
            # Create crew with MEMORY DISABLED to avoid CHROMA_OPENAI_API_KEY error
            self._create_crew()
            
            self.initialized = True
            logger.info("CrewAI Orchestrator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize CrewAI Orchestrator: {str(e)}")
            raise
    
    def _initialize_llm(self):
        """Initialize the Language Model."""
        try:
            # Check if we have a valid OpenAI API key
            if not self.settings.OPENAI_API_KEY or self.settings.OPENAI_API_KEY == "your_openai_api_key_here":
                logger.warning("No valid OpenAI API key found, using mock mode")
                self.llm = None
                return
                
            # Use ChatOpenAI with the API key
            self.llm = ChatOpenAI(
                model=self.settings.OPENAI_MODEL,
                temperature=0.1,
                max_tokens=2000,
                openai_api_key=self.settings.OPENAI_API_KEY
            )
            logger.info(f"LLM initialized with model: {self.settings.OPENAI_MODEL}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {str(e)}")
            logger.warning("Falling back to mock mode")
            self.llm = None
    
    def _create_agents(self):
        """Create CrewAI agents for different compliance tasks."""
        logger.info("Creating crew agents...")
        
        try:
            # Contract Analysis Agent
            contract_agent = Agent(
                role="Contract Analysis Specialist",
                goal="Analyze retail contracts and extract compliance requirements",
                backstory="You are an expert in retail contract analysis with deep knowledge of compliance requirements, promotional terms, and merchandising standards.",
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
                memory=False  # Disable memory to avoid CHROMA error
            )
            
            # Planogram Analysis Agent
            planogram_agent = Agent(
                role="Planogram Compliance Analyst",
                goal="Analyze planograms and verify product placement compliance",
                backstory="You specialize in planogram analysis and shelf compliance, ensuring products are placed according to contractual agreements.",
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
                memory=False  # Disable memory to avoid CHROMA error
            )
            
            # Image Analysis Agent
            image_agent = Agent(
                role="Visual Compliance Inspector",
                goal="Analyze store images to identify compliance violations",
                backstory="You are an expert in visual inspection of retail environments, identifying product placement, promotional compliance, and merchandising issues.",
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
                memory=False  # Disable memory to avoid CHROMA error
            )
            
            # Compliance Scoring Agent
            scoring_agent = Agent(
                role="Compliance Scoring Specialist",
                goal="Calculate compliance scores and generate recommendations",
                backstory="You specialize in compliance scoring methodologies and provide actionable recommendations for improving retail compliance.",
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
                memory=False  # Disable memory to avoid CHROMA error
            )
            
            # Report Generation Agent
            report_agent = Agent(
                role="Compliance Report Generator",
                goal="Generate comprehensive compliance reports with findings and recommendations",
                backstory="You are an expert in creating detailed compliance reports that are clear, actionable, and suitable for management review.",
                llm=self.llm,
                verbose=True,
                allow_delegation=False,
                memory=False  # Disable memory to avoid CHROMA error
            )
            
            self.agents = [contract_agent, planogram_agent, image_agent, scoring_agent, report_agent]
            logger.info(f"Created {len(self.agents)} crew agents successfully")
            
        except Exception as e:
            logger.error(f"Error creating agents: {str(e)}")
            raise
    
    def _create_tasks(self):
        """Create tasks for the compliance workflow."""
        logger.info("Creating tasks for crew...")
        
        try:
            # Task 1: Contract Analysis
            contract_task = Task(
                description="Analyze the retail contracts to extract compliance requirements, promotional terms, and merchandising standards for the specified store.",
                expected_output="A structured analysis of contract requirements including key compliance metrics, promotional obligations, and merchandising standards.",
                agent=self.agents[0]  # Contract agent
            )
            
            # Task 2: Planogram Analysis
            planogram_task = Task(
                description="Analyze planograms to understand the expected product placement, shelf allocation, and merchandising layout requirements.",
                expected_output="Detailed planogram analysis with expected product positions, shelf allocations, and compliance checkpoints.",
                agent=self.agents[1]  # Planogram agent
            )
            
            # Task 3: Image Analysis
            image_task = Task(
                description="Analyze store images to identify actual product placement, promotional displays, and merchandising execution compared to requirements.",
                expected_output="Visual compliance analysis identifying discrepancies between actual and expected product placement and promotional execution.",
                agent=self.agents[2]  # Image agent
            )
            
            # Task 4: Compliance Scoring
            scoring_task = Task(
                description="Calculate compliance scores based on contract requirements, planogram adherence, and visual inspection findings.",
                expected_output="Comprehensive compliance score with breakdown by category and identification of major violations.",
                agent=self.agents[3]  # Scoring agent
            )
            
            # Task 5: Report Generation
            report_task = Task(
                description="Generate a comprehensive compliance report with findings, scores, violations, and actionable recommendations.",
                expected_output="A detailed compliance report suitable for management review with clear findings and actionable recommendations.",
                agent=self.agents[4]  # Report agent
            )
            
            self.tasks = [contract_task, planogram_task, image_task, scoring_task, report_task]
            logger.info(f"Created {len(self.tasks)} tasks for crew")
            
        except Exception as e:
            logger.error(f"Error creating tasks: {str(e)}")
            raise
    
    def _create_crew(self):
        """Create the CrewAI crew."""
        logger.info("Creating CrewAI crew...")
        
        try:
            self.crew = Crew(
                agents=self.agents,
                tasks=self.tasks,
                process=Process.sequential,
                verbose=True,
                memory=False,  # CRITICAL: Disable memory to avoid CHROMA_OPENAI_API_KEY error
                max_execution_time=300  # 5 minutes timeout
            )
            logger.info("CrewAI crew created successfully")
            
        except Exception as e:
            logger.error(f"Error creating crew: {str(e)}")
            raise
    
    async def run_compliance_workflow(self, store_id: str, date: date) -> WorkflowResult:
        """
        Run the complete compliance monitoring workflow for a store.
        
        Args:
            store_id: The store identifier
            date: The date for compliance checking
            
        Returns:
            WorkflowResult: The result of the workflow execution
        """
        if not self.initialized:
            await self.initialize()
            
        workflow_id = str(uuid4())
        logger.info(f"Starting compliance workflow {workflow_id} for store {store_id}")
        
        # Create workflow result
        workflow_result = WorkflowResult(
            workflow_id=workflow_id,
            store_id=store_id,
            date=date,
            status=WorkflowStatus.RUNNING,
            started_at=datetime.now()
        )
        
        self.active_workflows[workflow_id] = workflow_result
        
        try:
            # Prepare workflow inputs
            inputs = {
                "store_id": store_id,
                "date": date.isoformat(),
                "workflow_id": workflow_id
            }
            
            # Execute the crew workflow
            if self.crew and self.settings.ENVIRONMENT != "mock":
                logger.info("Executing CrewAI workflow...")
                crew_result = self.crew.kickoff(inputs=inputs)
                
                # Process crew result
                workflow_result.result = {
                    "crew_output": str(crew_result),
                    "tasks_completed": len(self.tasks)
                }
                
                # Extract compliance score (mock calculation for now)
                workflow_result.compliance_score = self._calculate_mock_compliance_score()
                workflow_result.violations = self._generate_mock_violations()
                workflow_result.recommendations = self._generate_mock_recommendations()
                
            else:
                # Mock mode for development/testing
                logger.info("Running in mock mode...")
                await asyncio.sleep(2)  # Simulate processing time
                
                workflow_result.result = {
                    "mock_mode": True,
                    "message": "Mock compliance workflow completed"
                }
                workflow_result.compliance_score = self._calculate_mock_compliance_score()
                workflow_result.violations = self._generate_mock_violations()
                workflow_result.recommendations = self._generate_mock_recommendations()
            
            # Mark as completed
            workflow_result.status = WorkflowStatus.COMPLETED
            workflow_result.completed_at = datetime.now()
            
            logger.info(f"Compliance workflow {workflow_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error in compliance workflow {workflow_id}: {str(e)}")
            workflow_result.status = WorkflowStatus.FAILED
            workflow_result.error_message = str(e)
            workflow_result.completed_at = datetime.now()
        
        finally:
            # Move to history
            self.workflow_history.append(workflow_result)
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
        
        return workflow_result
    
    def _calculate_mock_compliance_score(self) -> float:
        """Calculate a mock compliance score for testing."""
        import random
        return round(random.uniform(75.0, 95.0), 2)
    
    def _generate_mock_violations(self) -> List[Dict[str, Any]]:
        """Generate mock violations for testing."""
        violations = [
            {
                "type": "Product Placement",
                "severity": "Medium",
                "description": "CPG products not placed at eye level as per contract",
                "location": "Aisle 3, Shelf 2"
            },
            {
                "type": "Promotional Display",
                "severity": "High",
                "description": "Missing promotional end cap display for summer campaign",
                "location": "End of Aisle 5"
            }
        ]
        import random
        return violations[:random.randint(0, 2)]  # Return 0-2 violations randomly
    
    def _generate_mock_recommendations(self) -> List[str]:
        """Generate mock recommendations for testing."""
        recommendations = [
            "Relocate CPG products to eye-level positions in beverage aisle",
            "Install promotional end cap display for summer campaign",
            "Ensure proper spacing between competing products",
            "Update shelf tags to match current promotional pricing"
        ]
        import random
        return recommendations[:random.randint(1, 3)]  # Return 1-3 recommendations
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowResult]:
        """Get the status of a specific workflow."""
        if workflow_id in self.active_workflows:
            return self.active_workflows[workflow_id]
        
        # Check history
        for workflow in self.workflow_history:
            if workflow.workflow_id == workflow_id:
                return workflow
        
        return None
    
    async def get_recent_workflows(self, limit: int = 10) -> List[WorkflowResult]:
        """Get recent workflow results."""
        # Combine active and historical workflows
        all_workflows = list(self.active_workflows.values()) + self.workflow_history
        
        # Sort by start time (most recent first)
        sorted_workflows = sorted(all_workflows, key=lambda x: x.started_at, reverse=True)
        
        return sorted_workflows[:limit]
    
    async def shutdown(self):
        """Shutdown the orchestrator and cleanup resources."""
        logger.info("Shutting down CrewAI Orchestrator...")
        
        # Cancel any active workflows
        for workflow_id in list(self.active_workflows.keys()):
            workflow = self.active_workflows[workflow_id]
            if workflow.status == WorkflowStatus.RUNNING:
                workflow.status = WorkflowStatus.FAILED
                workflow.error_message = "Shutdown requested"
                workflow.completed_at = datetime.now()
                self.workflow_history.append(workflow)
        
        self.active_workflows.clear()
        self.initialized = False
        
        logger.info("CrewAI Orchestrator shutdown complete")