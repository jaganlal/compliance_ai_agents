"""
Memory management system for AI agents
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pathlib import Path
from collections import defaultdict

from config.settings import Settings

logger = logging.getLogger(__name__)

class MemoryManager:
    """Manages different types of memory for AI agents."""
  
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.settings = Settings()
      
        # Memory storage
        self.episodic_memory = []  # Event-based memories
        self.semantic_memory = {}  # Knowledge-based memories
        self.working_memory = {}   # Temporary working data
      
        # Memory file paths
        self.memory_dir = self.settings.DATA_DIR / "memory" / agent_id
        self.memory_dir.mkdir(parents=True, exist_ok=True)
      
        self.episodic_file = self.memory_dir / "episodic.json"
        self.semantic_file = self.memory_dir / "semantic.json"
      
        # Load existing memories
        asyncio.create_task(self._load_memories())
  
    async def _load_memories(self):
        """Load memories from persistent storage."""
        try:
            # Load episodic memory
            if self.episodic_file.exists():
                with open(self.episodic_file, 'r') as f:
                    data = json.load(f)
                    self.episodic_memory = data.get('memories', [])
          
            # Load semantic memory
            if self.semantic_file.exists():
                with open(self.semantic_file, 'r') as f:
                    self.semantic_memory = json.load(f)
          
            logger.info(f"Loaded memories for agent {self.agent_id}")
          
        except Exception as e:
            logger.error(f"Error loading memories for {self.agent_id}: {str(e)}")
  
    async def _save_memories(self):
        """Save memories to persistent storage."""
        try:
            # Save episodic memory
            with open(self.episodic_file, 'w') as f:
                json.dump({
                    'agent_id': self.agent_id,
                    'last_updated': datetime.now().isoformat(),
                    'memories': self.episodic_memory
                }, f, indent=2, default=str)
          
            # Save semantic memory
            with open(self.semantic_file, 'w') as f:
                json.dump(self.semantic_memory, f, indent=2, default=str)
          
        except Exception as e:
            logger.error(f"Error saving memories for {self.agent_id}: {str(e)}")
  
    async def store_episodic_memory(self, memory: Dict[str, Any]):
        """Store an episodic memory (event-based)."""
        memory_entry = {
            'id': len(self.episodic_memory) + 1,
            'timestamp': datetime.now().isoformat(),
            'agent_id': self.agent_id,
            'data': memory
        }
      
        self.episodic_memory.append(memory_entry)
      
        # Cleanup old memories
        await self._cleanup_old_memories()
      
        # Save to disk
        await self._save_memories()
      
        logger.debug(f"Stored episodic memory for {self.agent_id}")
  
    async def store_semantic_memory(self, key: str, value: Any):
        """Store semantic memory (knowledge-based)."""
        self.semantic_memory[key] = {
            'value': value,
            'timestamp': datetime.now().isoformat(),
            'agent_id': self.agent_id
        }
      
        # Save to disk
        await self._save_memories()
      
        logger.debug(f"Stored semantic memory '{key}' for {self.agent_id}")
  
    async def retrieve_episodic_memories(self, query: Dict[str, Any] = None, 
                                       limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve episodic memories based on query."""
        memories = self.episodic_memory.copy()
      
        # Apply filters if query provided
        if query:
            filtered_memories = []
            for memory in memories:
                match = True
              
                # Check event type
                if 'event' in query and query['event'] != memory['data'].get('event'):
                    match = False
              
                # Check date range
                if 'start_date' in query:
                    memory_date = datetime.fromisoformat(memory['timestamp'])
                    start_date = datetime.fromisoformat(query['start_date'])
                    if memory_date < start_date:
                        match = False
              
                if 'end_date' in query:
                    memory_date = datetime.fromisoformat(memory['timestamp'])
                    end_date = datetime.fromisoformat(query['end_date'])
                    if memory_date > end_date:
                        match = False
              
                if match:
                    filtered_memories.append(memory)
          
            memories = filtered_memories
      
        # Sort by timestamp (most recent first)
        memories.sort(key=lambda x: x['timestamp'], reverse=True)
      
        return memories[:limit]
  
    async def retrieve_semantic_memories(self, query: str = "", 
                                       limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve semantic memories based on query."""
        if not query:
            # Return all semantic memories
            return [
                {'key': k, **v} 
                for k, v in list(self.semantic_memory.items())[:limit]
            ]
      
        # Simple text matching
        matching_memories = []
        for key, value in self.semantic_memory.items():
            if (query.lower() in key.lower() or 
                query.lower() in str(value.get('value', '')).lower()):
                matching_memories.append({'key': key, **value})
      
        return matching_memories[:limit]
  
    def set_working_memory(self, key: str, value: Any):
        """Set working memory (temporary)."""
        self.working_memory[key] = {
            'value': value,
            'timestamp': datetime.now().isoformat()
        }
      
        logger.debug(f"Set working memory '{key}' for {self.agent_id}")
  
    def get_working_memory(self, key: str) -> Any:
        """Get working memory value."""
        entry = self.working_memory.get(key)
        return entry['value'] if entry else None
  
    def clear_working_memory(self):
        """Clear all working memory."""
        self.working_memory.clear()
        logger.debug(f"Cleared working memory for {self.agent_id}")
  
    async def _cleanup_old_memories(self):
        """Remove old episodic memories based on retention policy."""
        cutoff_date = datetime.now() - timedelta(days=self.settings.MEMORY_RETENTION_DAYS)
      
        original_count = len(self.episodic_memory)
        self.episodic_memory = [
            memory for memory in self.episodic_memory
            if datetime.fromisoformat(memory['timestamp']) > cutoff_date
        ]
      
        removed_count = original_count - len(self.episodic_memory)
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old memories for {self.agent_id}")
  
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        return {
            'agent_id': self.agent_id,
            'episodic_count': len(self.episodic_memory),
            'semantic_count': len(self.semantic_memory),
            'working_count': len(self.working_memory),
            'oldest_episodic': (
                min(self.episodic_memory, key=lambda x: x['timestamp'])['timestamp']
                if self.episodic_memory else None
            ),
            'newest_episodic': (
                max(self.episodic_memory, key=lambda x: x['timestamp'])['timestamp']
                if self.episodic_memory else None
            )
        }