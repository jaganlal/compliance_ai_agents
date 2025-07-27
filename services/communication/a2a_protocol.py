"""
Agent-to-Agent (A2A) communication protocol implementation
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from collections import defaultdict, deque

from models.compliance_models import AgentMessage

logger = logging.getLogger(__name__)

class A2AProtocol:
    """Agent-to-Agent communication protocol using in-memory message broker."""
  
    def __init__(self):
        self.agents = {}  # agent_id -> agent_info
        self.message_queues = defaultdict(deque)  # agent_id -> message_queue
        self.message_history = deque(maxlen=1000)  # Recent message history
        self.subscriptions = defaultdict(list)  # message_type -> [agent_ids]
        self.agent_types = defaultdict(list)  # agent_type -> [agent_ids]
        self._lock = asyncio.Lock()
      
    async def initialize(self):
        """Initialize the A2A protocol."""
        logger.info("Initializing A2A Protocol...")
      
        # Start cleanup task for expired messages
        asyncio.create_task(self._cleanup_expired_messages())
      
        logger.info("A2A Protocol initialized successfully")
  
    async def register_agent(self, agent) -> bool:
        """Register an agent with the protocol."""
        async with self._lock:
            agent_info = {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "agent_type": agent.__class__.__name__.lower(),
                "status": agent.status,
                "registered_at": datetime.now(),
                "last_heartbeat": datetime.now()
            }
          
            self.agents[agent.agent_id] = agent_info
            self.agent_types[agent_info["agent_type"]].append(agent.agent_id)
          
            logger.info(f"Registered agent: {agent.name} ({agent.agent_id})")
            return True
  
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the protocol."""
        async with self._lock:
            if agent_id in self.agents:
                agent_info = self.agents[agent_id]
                agent_type = agent_info["agent_type"]
              
                # Remove from agents
                del self.agents[agent_id]
              
                # Remove from agent types
                if agent_id in self.agent_types[agent_type]:
                    self.agent_types[agent_type].remove(agent_id)
              
                # Clear message queue
                if agent_id in self.message_queues:
                    del self.message_queues[agent_id]
              
                logger.info(f"Unregistered agent: {agent_id}")
                return True
          
            return False
  
    async def send_message(self, message: AgentMessage) -> bool:
        """Send a message to a specific agent."""
        async with self._lock:
            # Check if recipient exists
            if message.recipient_id not in self.agents:
                logger.warning(f"Recipient agent not found: {message.recipient_id}")
                return False
          
            # Add to recipient's queue
            self.message_queues[message.recipient_id].append(message)
          
            # Add to history
            self.message_history.append(message)
          
            logger.debug(f"Message sent from {message.sender_id} to {message.recipient_id}")
            return True
  
    async def broadcast_message(self, sender_id: str, message: Dict[str, Any], 
                              agent_types: List[str] = None) -> int:
        """Broadcast a message to multiple agents."""
        sent_count = 0
      
        async with self._lock:
            target_agents = []
          
            if agent_types:
                # Send to specific agent types
                for agent_type in agent_types:
                    target_agents.extend(self.agent_types.get(agent_type, []))
            else:
                # Send to all agents except sender
                target_agents = [aid for aid in self.agents.keys() if aid != sender_id]
          
            # Remove duplicates
            target_agents = list(set(target_agents))
          
            # Send messages
            for agent_id in target_agents:
                agent_message = AgentMessage(
                    sender_id=sender_id,
                    recipient_id=agent_id,
                    message_type="broadcast",
                    content=message,
                    timestamp=datetime.now()
                )
              
                self.message_queues[agent_id].append(agent_message)
                self.message_history.append(agent_message)
                sent_count += 1
          
            logger.debug(f"Broadcast message sent to {sent_count} agents")
            return sent_count
  
    async def get_messages(self, agent_id: str, limit: int = 10) -> List[AgentMessage]:
        """Get messages for a specific agent."""
        async with self._lock:
            if agent_id not in self.message_queues:
                return []
          
            messages = []
            queue = self.message_queues[agent_id]
          
            # Get up to 'limit' messages
            for _ in range(min(limit, len(queue))):
                if queue:
                    message = queue.popleft()
                  
                    # Check if message has expired
                    if message.expires_at and datetime.now() > message.expires_at:
                        continue
                  
                    messages.append(message)
          
            return messages
  
    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific agent."""
        async with self._lock:
            return self.agents.get(agent_id)
  
    async def get_all_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all registered agents."""
        async with self._lock:
            return self.agents.copy()
  
    async def get_agents_by_type(self, agent_type: str) -> List[str]:
        """Get all agents of a specific type."""
        async with self._lock:
            return self.agent_types.get(agent_type, []).copy()
  
    async def update_agent_heartbeat(self, agent_id: str) -> bool:
        """Update agent heartbeat timestamp."""
        async with self._lock:
            if agent_id in self.agents:
                self.agents[agent_id]["last_heartbeat"] = datetime.now()
                return True
            return False
  
    async def _cleanup_expired_messages(self):
        """Cleanup expired messages periodically."""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
              
                async with self._lock:
                    current_time = datetime.now()
                  
                    # Clean up message queues
                    for agent_id, queue in self.message_queues.items():
                        # Filter out expired messages
                        valid_messages = deque()
                      
                        while queue:
                            message = queue.popleft()
                            if not message.expires_at or current_time <= message.expires_at:
                                valid_messages.append(message)
                      
                        self.message_queues[agent_id] = valid_messages
                  
                    # Clean up message history
                    cutoff_time = current_time - timedelta(hours=24)
                    while (self.message_history and 
                           self.message_history[0].timestamp < cutoff_time):
                        self.message_history.popleft()
                  
                    # Check for inactive agents
                    inactive_agents = []
                    for agent_id, agent_info in self.agents.items():
                        if (current_time - agent_info["last_heartbeat"]) > timedelta(minutes=10):
                            inactive_agents.append(agent_id)
                  
                    # Log inactive agents
                    for agent_id in inactive_agents:
                        logger.warning(f"Agent {agent_id} appears inactive")
                      
            except Exception as e:
                logger.error(f"Error in message cleanup: {str(e)}")
  
    def get_statistics(self) -> Dict[str, Any]:
        """Get protocol statistics."""
        return {
            "total_agents": len(self.agents),
            "agent_types": {k: len(v) for k, v in self.agent_types.items()},
            "total_queued_messages": sum(len(q) for q in self.message_queues.values()),
            "message_history_size": len(self.message_history),
            "active_queues": len([q for q in self.message_queues.values() if q])
        }