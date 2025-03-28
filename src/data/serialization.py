import json
import pickle
import os
import numpy as np
import datetime
from typing import Dict, Any, Optional, List, Tuple, Union

class Serialization:
    """Handles saving and loading simulation state to/from disk"""
    
    @staticmethod
    def save_simulation(world, filepath: str = None) -> str:
        """Save complete simulation state to disk"""
        if filepath is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"saves/simulation_{timestamp}.json"
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Collect simulation data
        data = {
            "world": Serialization._serialize_world(world),
            "metrics": Serialization._serialize_metrics(world.metrics),
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
        return filepath
    
    @staticmethod
    def load_simulation(world, filepath: str) -> bool:
        """Load simulation state from disk"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            # Reset the world first
            world.reset_world()
            
            # Load world data
            Serialization._deserialize_world(world, data["world"])
            
            # Load metrics
            if "metrics" in data:
                Serialization._deserialize_metrics(world.metrics, data["metrics"])
                
            return True
        except Exception as e:
            print(f"Error loading simulation: {e}")
            return False
    
    @staticmethod
    def save_neural_network(network, filename: str) -> None:
        """Save neural network weights and biases"""
        np.savez(
            filename, 
            w_input_hidden=network.weights_input_hidden,
            w_hidden_output=network.weights_hidden_output,
            b_hidden=network.bias_hidden,
            b_output=network.bias_output
        )
    
    @staticmethod
    def load_neural_network(network, filename: str) -> bool:
        """Load neural network weights and biases"""
        try:
            data = np.load(filename)
            network.weights_input_hidden = data['w_input_hidden']
            network.weights_hidden_output = data['w_hidden_output']
            network.bias_hidden = data['b_hidden']
            network.bias_output = data['b_output']
            return True
        except Exception as e:
            print(f"Error loading neural network: {e}")
            return False
    
    @staticmethod
    def save_q_table(q_table: Dict, filepath: str) -> None:
        """Save Q-table to disk"""
        with open(filepath, 'w') as f:
            json.dump(q_table, f, indent=2)
    
    @staticmethod
    def load_q_table(filepath: str) -> Dict:
        """Load Q-table from disk"""
        with open(filepath, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def export_metrics_csv(metrics, filename: str = "simulation_metrics.csv") -> str:
        """Export metrics to CSV file"""
        return metrics.export_csv(filename)
    
    @staticmethod
    def _serialize_world(world) -> Dict:
        """Serialize world state"""
        return {
            "width": world.width,
            "height": world.height,
            "entities": Serialization._serialize_entities(world.entities),
            "society": {
                "epoch": world.society.epoch,
                "population": Serialization._serialize_agents(world.society.population),
                "metrics": world.society.metrics
            }
        }
    
    @staticmethod
    def _deserialize_world(world, data: Dict) -> None:
        """Deserialize world state"""
        world.width = data["width"]
        world.height = data["height"]
        
        # Recreate entities
        Serialization._deserialize_entities(world, data["entities"])
        
        # Set society data
        world.society.epoch = data["society"]["epoch"]
        
        # Recreate population
        Serialization._deserialize_agents(world, data["society"]["population"])
        
        # Set society metrics
        world.society.metrics = data["society"]["metrics"]
    
    @staticmethod
    def _serialize_entities(entities: List) -> List[Dict]:
        """Serialize entities excluding agents"""
        result = []
        for entity in entities:
            # Skip agents as they are handled separately
            if hasattr(entity, 'genome'):
                continue
                
            entity_data = {
                "entity_type": entity.entity_type.value,
                "position": entity.position,
                "size": entity.size
            }
            
            # Add entity-specific properties
            if hasattr(entity, 'nutrition_value'):
                entity_data["nutrition_value"] = entity.nutrition_value
                
            result.append(entity_data)
        
        return result
    
    @staticmethod
    def _deserialize_entities(world, entities_data: List[Dict]) -> None:
        """Recreate entities from serialized data"""
        from constants import EntityType
        
        for entity_data in entities_data:
            entity_type = EntityType(entity_data["entity_type"])
            position = tuple(entity_data["position"])
            
            # Create entity based on type
            if entity_type == EntityType.FOOD:
                nutrition = entity_data.get("nutrition_value", 50)
                world.create_food(position=position, nutrition=nutrition)
            elif entity_type == EntityType.WORK:
                world.create_work(position=position)
    
    @staticmethod
    def _serialize_agents(agents: List) -> List[Dict]:
        """Serialize agent population"""
        result = []
        for agent in agents:
            agent_data = {
                "id": agent.id,
                "entity_type": agent.entity_type.value,
                "position": agent.position,
                "size": agent.size,
                "is_alive": agent.is_alive,
                "age": agent.age,
                "energy": agent.energy,
                "money": agent.money,
                "mood": agent.mood,
                "generation": agent.generation,
                "offspring_generations": agent.offspring_generations,
                "offspring_count": agent.offspring_count,
                "genome": Serialization._serialize_genome(agent.genome),
                "brain": Serialization._serialize_brain(agent.brain) if hasattr(agent, 'brain') and agent.brain else None
            }
            result.append(agent_data)
        
        return result
    
    @staticmethod
    def _deserialize_agents(world, agents_data: List[Dict]) -> None:
        """Recreate agent population from serialized data"""
        from simulation.entities.types.farm import Agent
        from constants import EntityType, Gender
        
        for agent_data in agents_data:
            # Create a new agent
            agent = Agent(agent_data["id"], world.world_screen)
            
            # Set basic properties
            agent.position = tuple(agent_data["position"])
            agent.size = tuple(agent_data["size"])
            agent.is_alive = agent_data["is_alive"]
            agent.age = agent_data["age"]
            agent.energy = agent_data["energy"]
            agent.money = agent_data["money"]
            agent.mood = agent_data["mood"]
            agent.generation = agent_data["generation"]
            agent.offspring_generations = agent_data["offspring_generations"]
            agent.offspring_count = agent_data["offspring_count"]
            
            # Set genome
            Serialization._deserialize_genome(agent.genome, agent_data["genome"])
            
            # Set entity type based on gender
            agent.entity_type = EntityType.PERSON_MALE if agent.genome.gender == Gender.MALE else EntityType.PERSON_FEMALE
            
            # Add to world
            world.add_entity(agent)
            
            # Create brain and load brain data
            if agent_data["brain"]:
                from src.simulation.agent.logic.brain import AgentBrain
                agent.brain = AgentBrain(agent.id, agent.genome)
                Serialization._deserialize_brain(agent.brain, agent_data["brain"])
    
    @staticmethod
    def _serialize_genome(genome) -> Dict:
        """Serialize agent genome"""
        return {
            "gender": genome.gender.value,
            "metabolism": genome.metabolism,
            "stamina": genome.stamina,
            "learning_capacity": genome.learning_capacity,
            "attraction_profile": genome.attraction_profile,
            "sexual_preference": genome.sexual_preference,
            "q_table": genome.q_table,
            "use_neural_network": genome.use_neural_network
        }
    
    @staticmethod
    def _deserialize_genome(genome, data: Dict) -> None:
        """Populate genome from serialized data"""
        from constants import Gender
        
        genome.gender = Gender(data["gender"])
        genome.metabolism = data["metabolism"]
        genome.stamina = data["stamina"]
        genome.learning_capacity = data["learning_capacity"]
        genome.attraction_profile = data["attraction_profile"]
        genome.sexual_preference = data["sexual_preference"]
        genome.q_table = data["q_table"]
        genome.use_neural_network = data["use_neural_network"]
    
    @staticmethod
    def _serialize_brain(brain) -> Dict:
        """Serialize agent brain"""
        return {
            "learning_rate": brain.learning_rate,
            "gamma": brain.gamma,
            "social_memory": brain.social_memory,
            "memory": {
                "replay_buffer": Serialization._serialize_experiences(brain.memory.replay_buffer.buffer),
                "episodic_memory": brain.memory.episodic_memory.memories,
                "use_prioritized": brain.memory.use_prioritized
            }
        }
    
    @staticmethod
    def _deserialize_brain(brain, data: Dict) -> None:
        """Populate brain from serialized data"""
        brain.learning_rate = data["learning_rate"]
        brain.gamma = data["gamma"]
        brain.social_memory = data["social_memory"]
        brain.memory.replay_buffer.buffer = data["memory"]["replay_buffer"]
        brain.memory.episodic_memory.memories = data["memory"]["episodic_memory"]
        brain.memory.use_prioritized = data["memory"]["use_prioritized"]
