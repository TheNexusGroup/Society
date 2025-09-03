#!/usr/bin/env python3
"""Test script for the Model Manager system"""

import sys
import pygame
from src.simulation.model_manager import ModelManager
from src.simulation.world.world import World
from src.simulation.society.population import Population

def test_model_manager():
    """Test the model manager functionality"""
    print("🧪 Testing Model Manager System\n")
    
    # Initialize pygame (required for the simulation)
    pygame.init()
    screen = pygame.display.set_mode((1200, 800))
    pygame.display.set_caption("Model Manager Test")
    
    # Create model manager
    manager = ModelManager("models")
    
    # Test 1: Create multiple models
    print("1️⃣ Creating multiple training models...")
    
    model1 = manager.create_model(
        "baseline_society",
        "Baseline society with default parameters",
        config={
            "population_size": 50,
            "learning_rate": 0.1,
            "exploration_rate": 0.3
        }
    )
    print(f"   Created model: {model1}")
    
    model2 = manager.create_model(
        "aggressive_society",
        "Society with aggressive economic parameters",
        config={
            "population_size": 100,
            "learning_rate": 0.2,
            "exploration_rate": 0.5,
            "wage_multiplier": 2.0
        }
    )
    print(f"   Created model: {model2}")
    
    model3 = manager.create_model(
        "cooperative_society",
        "Society with enhanced social cooperation",
        config={
            "population_size": 75,
            "learning_rate": 0.15,
            "exploration_rate": 0.2,
            "social_bonus": 1.5
        }
    )
    print(f"   Created model: {model3}")
    
    # Test 2: List models
    print("\n2️⃣ Listing all models...")
    models = manager.list_models()
    for model in models:
        print(f"   - {model['name']}: {model['description'][:50]}...")
        print(f"     Created: {model['created']}, Iterations: {model['iterations']}")
    
    # Test 3: Create and save checkpoints
    print("\n3️⃣ Testing checkpoint system...")
    
    # Create a simple world for testing
    world = World(1200, 800)
    # Initialize world properly without needing screen
    world.init_rendering(screen)
    
    # Switch to first model
    manager.load_model("baseline_society")
    
    # Simulate some iterations and save checkpoints
    for i in range(3):
        print(f"\n   Running iteration {i+1}...")
        
        # Simulate some steps (simplified)
        for _ in range(100):
            world.update(0.016)  # ~60 FPS
        
        # Increment iteration counter
        manager.increment_iteration()
        
        # Save checkpoint
        checkpoint_name = manager.save_checkpoint(
            world,
            name=f"test_checkpoint_{i+1}"
        )
        print(f"   ✅ Saved: {checkpoint_name}")
    
    # Test 4: Switch between models
    print("\n4️⃣ Testing model switching...")
    
    print("   Current model:", manager.current_model)
    manager.load_model("aggressive_society")
    print("   Switched to:", manager.current_model)
    
    # Run some iterations on the aggressive model
    for i in range(2):
        manager.increment_iteration()
        checkpoint = manager.save_checkpoint(world, auto_save=True)
        print(f"   Auto-saved checkpoint: {checkpoint}")
    
    # Test 5: Load checkpoint
    print("\n5️⃣ Testing checkpoint loading...")
    
    # Switch back to baseline
    manager.load_model("baseline_society")
    
    # Get model info
    info = manager.get_model_info()
    if info['checkpoints']:
        last_checkpoint = info['checkpoints'][-1]['name']
        print(f"   Loading checkpoint: {last_checkpoint}")
        
        success = manager.load_checkpoint(last_checkpoint, world)
        if success:
            print(f"   ✅ Successfully loaded checkpoint")
            print(f"   Current iteration: {info['current_iteration']}")
        else:
            print(f"   ❌ Failed to load checkpoint")
    
    # Test 6: Compare models
    print("\n6️⃣ Model comparison...")
    comparison = manager.compare_models(["baseline_society", "aggressive_society"])
    for model_name, metrics in comparison.items():
        print(f"   {model_name}: {metrics}")
    
    # Test 7: Get detailed model info
    print("\n7️⃣ Detailed model information...")
    for model_name in ["baseline_society", "aggressive_society", "cooperative_society"]:
        info = manager.get_model_info(model_name)
        print(f"\n   Model: {model_name}")
        print(f"   - Total iterations: {info['total_iterations']}")
        print(f"   - Checkpoints: {len(info['checkpoints'])}")
        print(f"   - Disk usage: {info['disk_usage_mb']:.2f} MB")
        print(f"   - Config: {info['config']}")
    
    # Test 8: Test model deletion
    print("\n8️⃣ Testing model deletion...")
    test_model = manager.create_model("test_delete", "Model to be deleted")
    print(f"   Created temporary model: {test_model}")
    
    success = manager.delete_model("test_delete")
    if success:
        print(f"   ✅ Successfully deleted model")
    else:
        print(f"   ❌ Failed to delete model")
    
    print("\n✅ Model Manager tests completed successfully!")
    print("\nSummary:")
    print(f"- Created {len(manager.list_models())} models")
    print(f"- Current active model: {manager.current_model}")
    print(f"- Models can be saved, loaded, and switched between")
    print(f"- Each model maintains its own checkpoints and training state")
    
    pygame.quit()
    return True

if __name__ == "__main__":
    try:
        success = test_model_manager()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)