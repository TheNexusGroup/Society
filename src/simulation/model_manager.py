"""Model Manager for Society Simulation
Manages multiple training models, save states, and experiment tracking
"""

import os
import json
import shutil
import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import pickle
import numpy as np

class ModelManager:
    """Manages different society training models and their states"""
    
    def __init__(self, base_dir: str = "models"):
        """Initialize model manager with base directory for all models"""
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Track current active model
        self.current_model: Optional[str] = None
        self.models_metadata: Dict = self._load_metadata()
        
    def _load_metadata(self) -> Dict:
        """Load metadata about all saved models"""
        metadata_file = self.base_dir / "models_metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self):
        """Save metadata about all models"""
        metadata_file = self.base_dir / "models_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(self.models_metadata, f, indent=2)
    
    def create_model(self, name: str, description: str = "", config: Dict = None) -> str:
        """Create a new model/experiment with given configuration"""
        model_dir = self.base_dir / name
        
        if model_dir.exists():
            # Append timestamp if model name exists
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"{name}_{timestamp}"
            model_dir = self.base_dir / name
        
        model_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (model_dir / "checkpoints").mkdir(exist_ok=True)
        (model_dir / "metrics").mkdir(exist_ok=True)
        (model_dir / "neural_nets").mkdir(exist_ok=True)
        (model_dir / "q_tables").mkdir(exist_ok=True)
        
        # Initialize model metadata
        self.models_metadata[name] = {
            "created": datetime.datetime.now().isoformat(),
            "description": description,
            "config": config or {},
            "checkpoints": [],
            "current_iteration": 0,
            "total_iterations": 0,
            "last_modified": datetime.datetime.now().isoformat()
        }
        
        self._save_metadata()
        self.current_model = name
        
        # Save initial configuration
        if config:
            with open(model_dir / "config.json", 'w') as f:
                json.dump(config, f, indent=2)
        
        return name
    
    def list_models(self) -> List[Dict]:
        """List all available models with their metadata"""
        models = []
        for name, metadata in self.models_metadata.items():
            model_info = {
                "name": name,
                "created": metadata["created"],
                "description": metadata["description"],
                "iterations": metadata["total_iterations"],
                "last_modified": metadata["last_modified"],
                "checkpoints": len(metadata["checkpoints"])
            }
            models.append(model_info)
        return sorted(models, key=lambda x: x["last_modified"], reverse=True)
    
    def save_checkpoint(self, world, name: str = None, auto_save: bool = False) -> str:
        """Save current simulation state as a checkpoint"""
        if not self.current_model:
            raise ValueError("No model selected. Use load_model() or create_model() first.")
        
        model_dir = self.base_dir / self.current_model
        checkpoints_dir = model_dir / "checkpoints"
        
        # Generate checkpoint name
        iteration = self.models_metadata[self.current_model]["current_iteration"]
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if name:
            checkpoint_name = f"{name}_iter{iteration}_{timestamp}"
        elif auto_save:
            checkpoint_name = f"auto_iter{iteration}_{timestamp}"
        else:
            checkpoint_name = f"checkpoint_iter{iteration}_{timestamp}"
        
        checkpoint_file = checkpoints_dir / f"{checkpoint_name}.pkl"
        
        # Collect all simulation data
        checkpoint_data = {
            "iteration": iteration,
            "timestamp": datetime.datetime.now().isoformat(),
            "world_state": self._serialize_world(world),
            "ecs_state": self._serialize_ecs(world.ecs),
            "metrics": self._serialize_metrics(world),
            "population": len(world.ecs.get_entities_with_components(["behavior", "tag"])),
            "config": self.models_metadata[self.current_model]["config"]
        }
        
        # Save checkpoint
        with open(checkpoint_file, 'wb') as f:
            pickle.dump(checkpoint_data, f)
        
        # Save neural networks separately for each agent
        nn_dir = model_dir / "neural_nets" / checkpoint_name
        nn_dir.mkdir(exist_ok=True)
        self._save_neural_networks(world, nn_dir)
        
        # Save Q-tables
        qt_dir = model_dir / "q_tables" / checkpoint_name
        qt_dir.mkdir(exist_ok=True)
        self._save_q_tables(world, qt_dir)
        
        # Update metadata
        checkpoint_info = {
            "name": checkpoint_name,
            "file": str(checkpoint_file.relative_to(self.base_dir)),
            "iteration": iteration,
            "timestamp": timestamp,
            "population": checkpoint_data["population"]
        }
        
        self.models_metadata[self.current_model]["checkpoints"].append(checkpoint_info)
        self.models_metadata[self.current_model]["last_modified"] = datetime.datetime.now().isoformat()
        self.models_metadata[self.current_model]["current_iteration"] = iteration
        self._save_metadata()
        
        print(f"✅ Checkpoint saved: {checkpoint_name} (Iteration {iteration}, Population {checkpoint_data['population']})")
        return checkpoint_name
    
    def load_checkpoint(self, checkpoint_name: str, world) -> bool:
        """Load a specific checkpoint"""
        if not self.current_model:
            raise ValueError("No model selected. Use load_model() first.")
        
        model_dir = self.base_dir / self.current_model
        
        # Find checkpoint file
        checkpoint_file = None
        for checkpoint in self.models_metadata[self.current_model]["checkpoints"]:
            if checkpoint["name"] == checkpoint_name:
                checkpoint_file = self.base_dir / checkpoint["file"]
                break
        
        if not checkpoint_file or not checkpoint_file.exists():
            print(f"❌ Checkpoint {checkpoint_name} not found")
            return False
        
        try:
            # Load checkpoint data
            with open(checkpoint_file, 'rb') as f:
                checkpoint_data = pickle.load(f)
            
            # Clear current world
            world.reset()
            
            # Restore world state
            self._deserialize_world(world, checkpoint_data["world_state"])
            
            # Restore ECS state
            self._deserialize_ecs(world.ecs, checkpoint_data["ecs_state"])
            
            # Restore metrics
            if "metrics" in checkpoint_data:
                self._deserialize_metrics(world, checkpoint_data["metrics"])
            
            # Load neural networks
            nn_dir = model_dir / "neural_nets" / checkpoint_name
            if nn_dir.exists():
                self._load_neural_networks(world, nn_dir)
            
            # Load Q-tables
            qt_dir = model_dir / "q_tables" / checkpoint_name
            if qt_dir.exists():
                self._load_q_tables(world, qt_dir)
            
            # Update current iteration
            self.models_metadata[self.current_model]["current_iteration"] = checkpoint_data["iteration"]
            
            print(f"✅ Loaded checkpoint: {checkpoint_name} (Iteration {checkpoint_data['iteration']}, Population {checkpoint_data['population']})")
            return True
            
        except Exception as e:
            print(f"❌ Error loading checkpoint: {e}")
            return False
    
    def load_model(self, name: str) -> bool:
        """Switch to a different model"""
        if name not in self.models_metadata:
            print(f"❌ Model '{name}' not found")
            return False
        
        self.current_model = name
        print(f"✅ Switched to model: {name}")
        return True
    
    def delete_model(self, name: str) -> bool:
        """Delete a model and all its data"""
        if name not in self.models_metadata:
            return False
        
        model_dir = self.base_dir / name
        if model_dir.exists():
            shutil.rmtree(model_dir)
        
        del self.models_metadata[name]
        self._save_metadata()
        
        if self.current_model == name:
            self.current_model = None
        
        print(f"✅ Deleted model: {name}")
        return True
    
    def increment_iteration(self, count: int = 1):
        """Increment the current iteration counter"""
        if self.current_model:
            self.models_metadata[self.current_model]["current_iteration"] += count
            self.models_metadata[self.current_model]["total_iterations"] += count
            self._save_metadata()
    
    def get_model_info(self, name: str = None) -> Dict:
        """Get detailed information about a model"""
        model_name = name or self.current_model
        if not model_name or model_name not in self.models_metadata:
            return {}
        
        metadata = self.models_metadata[model_name]
        model_dir = self.base_dir / model_name
        
        # Calculate disk usage
        total_size = sum(f.stat().st_size for f in model_dir.rglob('*') if f.is_file())
        
        return {
            "name": model_name,
            "created": metadata["created"],
            "description": metadata["description"],
            "config": metadata["config"],
            "current_iteration": metadata["current_iteration"],
            "total_iterations": metadata["total_iterations"],
            "checkpoints": metadata["checkpoints"],
            "last_modified": metadata["last_modified"],
            "disk_usage_mb": total_size / (1024 * 1024)
        }
    
    def compare_models(self, model_names: List[str]) -> Dict:
        """Compare metrics across multiple models"""
        comparison = {}
        
        for name in model_names:
            if name in self.models_metadata:
                model_dir = self.base_dir / name
                metrics_file = model_dir / "metrics" / "summary.json"
                
                if metrics_file.exists():
                    with open(metrics_file, 'r') as f:
                        metrics = json.load(f)
                        comparison[name] = metrics
        
        return comparison
    
    # Serialization helpers
    def _serialize_world(self, world) -> Dict:
        """Serialize world state"""
        return {
            "width": world.width,
            "height": world.height,
            "current_time": getattr(world, 'current_time', 0),
            "seed": getattr(world, 'seed', None)
        }
    
    def _deserialize_world(self, world, data: Dict):
        """Deserialize world state"""
        world.width = data["width"]
        world.height = data["height"]
        if "current_time" in data:
            world.current_time = data["current_time"]
        if "seed" in data:
            world.seed = data["seed"]
    
    def _serialize_ecs(self, ecs) -> Dict:
        """Serialize ECS state including all entities and components"""
        entities_data = {}
        
        for entity_id, entity in ecs.entities.items():
            entity_components = {}
            
            # Serialize each component type
            for comp_type, components in ecs.components.items():
                if entity_id in components:
                    comp = components[entity_id]
                    # Serialize component based on its type
                    entity_components[comp_type] = self._serialize_component(comp, comp_type)
            
            entities_data[entity_id] = {
                "id": entity_id,
                "components": entity_components
            }
        
        return {
            "entities": entities_data,
            "next_entity_id": max(ecs.entities.keys()) + 1 if ecs.entities else 0
        }
    
    def _deserialize_ecs(self, ecs, data: Dict):
        """Deserialize ECS state"""
        # Clear existing entities
        ecs.entities.clear()
        ecs.components.clear()
        
        # Recreate entities and components
        for entity_id_str, entity_data in data["entities"].items():
            entity_id = int(entity_id_str)
            
            # Create entity
            from src.core.ecs.entity import Entity
            entity = Entity()
            entity.id = entity_id
            ecs.entities[entity_id] = entity
            
            # Recreate components
            for comp_type, comp_data in entity_data["components"].items():
                component = self._deserialize_component(comp_data, comp_type)
                if component:
                    ecs.add_component(entity_id, comp_type, component)
    
    def _serialize_component(self, component, comp_type: str) -> Dict:
        """Serialize a component based on its type"""
        # Generic serialization for common attributes
        data = {
            "entity_id": component.entity_id
        }
        
        # Add type-specific attributes
        if comp_type == "behavior":
            data.update({
                "state": component.state,
                "target": component.target,
                "properties": component.properties
            })
        elif comp_type == "transform":
            data.update({
                "position": component.position,
                "velocity": component.velocity,
                "direction": component.direction
            })
        elif comp_type == "wallet":
            data.update({
                "money": component.money,
                "food": component.food,
                "energy": component.energy
            })
        elif comp_type == "social":
            data.update({
                "relationships": {str(k): v.__dict__ for k, v in component.relationships.items()},
                "mood": component.mood,
                "social_energy": component.social_energy
            })
        elif comp_type == "tag":
            data.update({
                "tag": component.tag,
                "entity_type": component.entity_type
            })
        # Add more component types as needed
        
        return data
    
    def _deserialize_component(self, data: Dict, comp_type: str):
        """Deserialize a component based on its type"""
        # Import component classes
        if comp_type == "behavior":
            from src.core.ecs.components.behaviour import BehaviorComponent
            comp = BehaviorComponent(data["entity_id"])
            comp.state = data["state"]
            comp.target = data["target"]
            comp.properties = data["properties"]
            return comp
        elif comp_type == "transform":
            from src.core.ecs.components.transform import TransformComponent
            comp = TransformComponent(data["entity_id"])
            comp.position = tuple(data["position"])
            comp.velocity = tuple(data["velocity"])
            comp.direction = data["direction"]
            return comp
        elif comp_type == "wallet":
            from src.core.ecs.components.wallet import WalletComponent
            comp = WalletComponent(data["entity_id"])
            comp.money = data["money"]
            comp.food = data["food"]
            comp.energy = data["energy"]
            return comp
        elif comp_type == "social":
            from src.core.ecs.components.social import Social, SocialRelationship
            comp = Social(data["entity_id"])
            # Recreate relationships
            for agent_id_str, rel_data in data["relationships"].items():
                rel = SocialRelationship(int(agent_id_str))
                rel.trust = rel_data["trust"]
                rel.affinity = rel_data["affinity"]
                comp.relationships[int(agent_id_str)] = rel
            comp.mood = data["mood"]
            comp.social_energy = data["social_energy"]
            return comp
        elif comp_type == "tag":
            from src.core.ecs.components.tag import TagComponent
            comp = TagComponent(data["entity_id"])
            comp.tag = data["tag"]
            comp.entity_type = data["entity_type"]
            return comp
        
        return None
    
    def _serialize_metrics(self, world) -> Dict:
        """Serialize world metrics"""
        metrics = getattr(world, 'metrics', None)
        if not metrics:
            return {}
        
        return {
            "population_history": getattr(metrics, 'population_history', []),
            "wealth_history": getattr(metrics, 'wealth_history', []),
            "food_history": getattr(metrics, 'food_history', []),
            "death_count": getattr(metrics, 'death_count', 0),
            "birth_count": getattr(metrics, 'birth_count', 0)
        }
    
    def _deserialize_metrics(self, world, data: Dict):
        """Deserialize world metrics"""
        if hasattr(world, 'metrics'):
            for key, value in data.items():
                setattr(world.metrics, key, value)
    
    def _save_neural_networks(self, world, directory: Path):
        """Save all agent neural networks"""
        # Get all agents with brains
        for entity_id in world.ecs.get_entities_with_components(["behavior", "tag"]):
            tag = world.ecs.get_component(entity_id, "tag")
            if tag and tag.tag == "agent":
                # Try to get brain through the agent entity
                behavior = world.ecs.get_component(entity_id, "behavior")
                if behavior and "brain" in behavior.properties:
                    brain = behavior.properties["brain"]
                    if hasattr(brain, 'neural_network') and brain.neural_network:
                        nn_file = directory / f"agent_{entity_id}_nn.npz"
                        np.savez(
                            nn_file,
                            w_input_hidden=brain.neural_network.weights_input_hidden,
                            w_hidden_output=brain.neural_network.weights_hidden_output,
                            b_hidden=brain.neural_network.bias_hidden,
                            b_output=brain.neural_network.bias_output
                        )
    
    def _load_neural_networks(self, world, directory: Path):
        """Load all agent neural networks"""
        for nn_file in directory.glob("agent_*_nn.npz"):
            # Extract entity ID from filename
            entity_id = int(nn_file.stem.split('_')[1])
            
            # Get the agent's brain
            behavior = world.ecs.get_component(entity_id, "behavior")
            if behavior and "brain" in behavior.properties:
                brain = behavior.properties["brain"]
                if hasattr(brain, 'neural_network') and brain.neural_network:
                    data = np.load(nn_file)
                    brain.neural_network.weights_input_hidden = data['w_input_hidden']
                    brain.neural_network.weights_hidden_output = data['w_hidden_output']
                    brain.neural_network.bias_hidden = data['b_hidden']
                    brain.neural_network.bias_output = data['b_output']
    
    def _save_q_tables(self, world, directory: Path):
        """Save all agent Q-tables"""
        for entity_id in world.ecs.get_entities_with_components(["behavior", "tag"]):
            tag = world.ecs.get_component(entity_id, "tag")
            if tag and tag.tag == "agent":
                behavior = world.ecs.get_component(entity_id, "behavior")
                if behavior and "brain" in behavior.properties:
                    brain = behavior.properties["brain"]
                    if hasattr(brain, 'q_table'):
                        qt_file = directory / f"agent_{entity_id}_qtable.json"
                        with open(qt_file, 'w') as f:
                            json.dump(brain.q_table, f)
    
    def _load_q_tables(self, world, directory: Path):
        """Load all agent Q-tables"""
        for qt_file in directory.glob("agent_*_qtable.json"):
            entity_id = int(qt_file.stem.split('_')[1])
            
            behavior = world.ecs.get_component(entity_id, "behavior")
            if behavior and "brain" in behavior.properties:
                brain = behavior.properties["brain"]
                if hasattr(brain, 'q_table'):
                    with open(qt_file, 'r') as f:
                        brain.q_table = json.load(f)