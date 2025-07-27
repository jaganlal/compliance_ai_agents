"""
Base agent class for all AI agents in the system
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from memory.memory_manager import MemoryManager
from services.communication.a2a_protocol import A2AProtocol
from models.compliance_models import AgentMessage, AgentStatus

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all AI agents in the system."""
  
    def __init__(self, agent_id: str = None, name: str = None):
        self.agent_id = agent_id or str(uuid4())
        self.name = name or self.__class__.__name__
        self.status = AgentStatus.IDLE
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
      
        # Core components
        self.memory_manager = MemoryManager(agent_id=self.agent_id)
        self.a2a_protocol = A2AProtocol()
      
        # Agent state
        self.current_task = None
        self.task_history = []
      
        logger.info(f"Initialized agent: {self.name} ({self.agent_id})")
  
    @abstractmethod
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task assigned to this agent."""
        pass
  
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the agent and its dependencies."""
        pass
  
    async def start(self):
        """Start the agent and begin listening for tasks."""
        logger.info(f"Starting agent: {self.name}")
        self.status = AgentStatus.ACTIVE
      
        await self.initialize()
        await self.a2a_protocol.register_agent(self)
      
        # Start message listening loop
        asyncio.create_task(self._message_loop())
  
    async def stop(self):
        """Stop the agent gracefully."""
        logger.info(f"Stopping agent: {self.name}")
        self.status = AgentStatus.STOPPING
      
        await self.a2a_protocol.unregister_agent(self.agent_id)
        self.status = AgentStatus.STOPPED
  
    async def send_message(self, recipient_id: str, message: Dict[str, Any]) -> bool:
        """Send a message to another agent."""
        agent_message = AgentMessage(
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            message_type="task",
            content=message,
            timestamp=datetime.now()
        )
      
        return await self.a2a_protocol.send_message(agent_message)
  
    async def broadcast_message(self, message: Dict[str, Any], agent_types: List[str] = None) -> int:
        """Broadcast a message to multiple agents."""
        return await self.a2a_protocol.broadcast_message(
            sender_id=self.agent_id,
            message=message,
            agent_types=agent_types
        )
  
    async def _message_loop(self):
        """Main message processing loop."""
        while self.status in [AgentStatus.ACTIVE, AgentStatus.BUSY]:
            try:
                # Check for incoming messages
                messages = await self.a2a_protocol.get_messages(self.agent_id)
              
                for message in messages:
                    await self._handle_message(message)
              
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)
              
            except Exception as e:
                logger.error(f"Error in message loop for {self.name}: {str(e)}")
                await asyncio.sleep(1)
  
    async def _handle_message(self, message: AgentMessage):
        """Handle an incoming message."""
        try:
            self.last_activity = datetime.now()
          
            if message.message_type == "task":
                await self._handle_task_message(message)
            elif message.message_type == "status":
                await self._handle_status_message(message)
            elif message.message_type == "memory":
                await self._handle_memory_message(message)
            else:
                logger.warning(f"Unknown message type: {message.message_type}")
              
        except Exception as e:
            logger.error(f"Error handling message in {self.name}: {str(e)}")
  
    async def _handle_task_message(self, message: AgentMessage):
        """Handle a task message."""
        if self.status != AgentStatus.ACTIVE:
            logger.warning(f"Agent {self.name} received task but is not active")
            return
      
        self.status = AgentStatus.BUSY
        self.current_task = message.content
      
        try:
            # Process the task
            result = await self.process_task(message.content)
          
            # Send result back to sender
            await self.send_message(message.sender_id, {
                "type": "task_result",
                "task_id": message.content.get("task_id"),
                "result": result,
                "status": "completed"
            })
          
            # Store in memory
            await self.memory_manager.store_episodic_memory({
                "event": "task_completed",
                "task": message.content,
                "result": result,
                "timestamp": datetime.now()
            })
          
        except Exception as e:
            logger.error(f"Error processing task in {self.name}: {str(e)}")
          
            # Send error back to sender
            await self.send_message(message.sender_id, {
                "type": "task_error",
                "task_id": message.content.get("task_id"),
                "error": str(e),
                "status": "failed"
            })
      
        finally:
            self.current_task = None
            self.status = AgentStatus.ACTIVE
  
    async def _handle_status_message(self, message: AgentMessage):
        """Handle a status request message."""
        status_info = {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status.value,
            "last_activity": self.last_activity,
            "current_task": self.current_task
        }
      
        await self.send_message(message.sender_id, {
            "type": "status_response",
            "status": status_info
        })
  
    async def _handle_memory_message(self, message: AgentMessage):
        """Handle a memory-related message."""
        memory_type = message.content.get("memory_type")
        operation = message.content.get("operation")
      
        if operation == "retrieve":
            if memory_type == "episodic":
                memories = await self.memory_manager.retrieve_episodic_memories(
                    message.content.get("query", {}),
                    message.content.get("limit", 10)
                )
            elif memory_type == "semantic":
                memories = await self.memory_manager.retrieve_semantic_memories(
                    message.content.get("query", ""),
                    message.content.get("limit", 10)
                )
            else:
                memories = []
          
            await self.send_message(message.sender_id, {
                "type": "memory_response",
                "memories": memories
            })
  
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status.value,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "current_task": self.current_task,
            "task_count": len(self.task_history)
        }