from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import uuid
from .types import Agent, DomainType


class AgentRegistry:
    """Registry for managing multiple AI agents"""
    
    def __init__(self):
        self._agents: Dict[str, Agent] = {}
        self._domain_index: Dict[DomainType, List[str]] = {domain: [] for domain in DomainType}
        self._metadata: Dict[str, Any] = {}
    
    def register_agent(
        self,
        name: str,
        model_name: str,
        domain: DomainType = DomainType.GENERAL,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Register a new agent in the registry"""
        if agent_id is None:
            agent_id = f"agent_{uuid.uuid4().hex[:8]}"
        
        if agent_id in self._agents:
            raise ValueError(f"Agent with ID '{agent_id}' already exists")
        
        agent = Agent(
            id=agent_id,
            name=name,
            model_name=model_name,
            domain=domain,
            metadata=metadata or {}
        )
        
        self._agents[agent_id] = agent
        self._domain_index[domain].append(agent_id)
        
        return agent_id
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID"""
        return self._agents.get(agent_id)
    
    def get_agents_by_domain(self, domain: DomainType) -> List[Agent]:
        """Get all agents in a specific domain"""
        agent_ids = self._domain_index.get(domain, [])
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]
    
    def get_all_agents(self) -> List[Agent]:
        """Get all registered agents"""
        return list(self._agents.values())
    
    def get_agent_count(self) -> int:
        """Get total number of registered agents"""
        return len(self._agents)
    
    def get_domain_counts(self) -> Dict[DomainType, int]:
        """Get count of agents per domain"""
        return {domain: len(agent_ids) for domain, agent_ids in self._domain_index.items()}
    
    def update_agent_metadata(self, agent_id: str, metadata: Dict[str, Any]) -> bool:
        """Update agent metadata"""
        if agent_id not in self._agents:
            return False
        
        self._agents[agent_id].metadata.update(metadata)
        return True
    
    def remove_agent(self, agent_id: str) -> bool:
        """Remove an agent from the registry"""
        if agent_id not in self._agents:
            return False
        
        agent = self._agents[agent_id]
        self._domain_index[agent.domain].remove(agent_id)
        del self._agents[agent_id]
        return True
    
    def search_agents(
        self,
        name_pattern: Optional[str] = None,
        model_name: Optional[str] = None,
        domain: Optional[DomainType] = None
    ) -> List[Agent]:
        """Search agents by criteria"""
        results = []
        
        for agent in self._agents.values():
            if name_pattern and name_pattern.lower() not in agent.name.lower():
                continue
            if model_name and model_name.lower() not in agent.model_name.lower():
                continue
            if domain and agent.domain != domain:
                continue
            
            results.append(agent)
        
        return results
    
    def export_agents(self, filepath: str) -> bool:
        """Export agent registry to JSON file"""
        try:
            export_data = {
                "agents": {
                    agent_id: {
                        "id": agent.id,
                        "name": agent.name,
                        "model_name": agent.model_name,
                        "domain": agent.domain.value,
                        "metadata": agent.metadata,
                        "created_at": agent.created_at.isoformat()
                    }
                    for agent_id, agent in self._agents.items()
                },
                "domain_index": {
                    domain.value: agent_ids
                    for domain, agent_ids in self._domain_index.items()
                },
                "exported_at": datetime.now().isoformat()
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error exporting agents: {e}")
            return False
    
    def import_agents(self, filepath: str) -> bool:
        """Import agent registry from JSON file"""
        try:
            with open(filepath, 'r') as f:
                import_data = json.load(f)
            
            # Clear existing agents
            self._agents.clear()
            self._domain_index = {domain: [] for domain in DomainType}
            
            # Import agents
            for agent_id, agent_data in import_data.get("agents", {}).items():
                agent = Agent(
                    id=agent_data["id"],
                    name=agent_data["name"],
                    model_name=agent_data["model_name"],
                    domain=DomainType(agent_data["domain"]),
                    metadata=agent_data.get("metadata", {}),
                    created_at=datetime.fromisoformat(agent_data.get("created_at", datetime.now().isoformat()))
                )
                
                self._agents[agent_id] = agent
                self._domain_index[agent.domain].append(agent_id)
            
            return True
        except Exception as e:
            print(f"Error importing agents: {e}")
            return False
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        return {
            "total_agents": len(self._agents),
            "domain_counts": self.get_domain_counts(),
            "oldest_agent": min(self._agents.values(), key=lambda a: a.created_at).created_at.isoformat() if self._agents else None,
            "newest_agent": max(self._agents.values(), key=lambda a: a.created_at).created_at.isoformat() if self._agents else None,
            "model_distribution": self._get_model_distribution(),
        }
    
    def _get_model_distribution(self) -> Dict[str, int]:
        """Get distribution of model names"""
        model_counts = {}
        for agent in self._agents.values():
            model_counts[agent.model_name] = model_counts.get(agent.model_name, 0) + 1
        return model_counts
