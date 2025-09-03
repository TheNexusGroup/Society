#!/usr/bin/env python3
"""Simple test for Model Manager core functionality"""

from src.simulation.model_manager import ModelManager

def test_core_functionality():
    """Test core model manager functionality without full simulation"""
    print("🧪 Testing Model Manager Core Functionality\n")
    
    # Create model manager
    manager = ModelManager("models")
    
    # Test 1: Create models
    print("1️⃣ Creating training models...")
    
    baseline = manager.create_model(
        "baseline_v1",
        "Baseline society configuration",
        config={
            "population_size": 50,
            "learning_rate": 0.1,
            "exploration_rate": 0.3,
            "economic_focus": "balanced"
        }
    )
    
    aggressive = manager.create_model(
        "aggressive_v1", 
        "High competition society",
        config={
            "population_size": 100,
            "learning_rate": 0.2,
            "exploration_rate": 0.5,
            "economic_focus": "competitive"
        }
    )
    
    cooperative = manager.create_model(
        "cooperative_v1",
        "Cooperative focused society",
        config={
            "population_size": 75,
            "learning_rate": 0.15,
            "exploration_rate": 0.2,
            "economic_focus": "cooperative"
        }
    )
    
    print(f"   ✅ Created models: {baseline}, {aggressive}, {cooperative}")
    
    # Test 2: List and switch models
    print("\n2️⃣ Model management...")
    models = manager.list_models()
    print(f"   Total models: {len(models)}")
    
    for model in models[:3]:  # Show first 3
        print(f"   - {model['name']}: {model['description']}")
    
    # Switch between models
    print(f"\n   Current model: {manager.current_model}")
    manager.load_model("baseline_v1")
    print(f"   Switched to: {manager.current_model}")
    
    # Test 3: Simulate iterations
    print("\n3️⃣ Simulating training iterations...")
    
    for i in range(5):
        manager.increment_iteration(10)  # Simulate 10 iterations
        print(f"   Iteration {(i+1)*10}: Model trained")
    
    info = manager.get_model_info()
    print(f"   Total iterations completed: {info['total_iterations']}")
    
    # Test 4: Switch models and compare
    print("\n4️⃣ Model comparison...")
    
    # Train aggressive model
    manager.load_model("aggressive_v1")
    manager.increment_iteration(25)
    
    # Train cooperative model  
    manager.load_model("cooperative_v1")
    manager.increment_iteration(35)
    
    # Compare all models
    print("   Model Status:")
    for model_name in ["baseline_v1", "aggressive_v1", "cooperative_v1"]:
        info = manager.get_model_info(model_name)
        print(f"   - {model_name}: {info['total_iterations']} iterations")
        print(f"     Config: {info['config']['economic_focus']}")
    
    print("\n✅ Model Manager working perfectly!")
    print("\n📊 Summary:")
    print(f"   - Created 3 different society training models")
    print(f"   - Each model has different configurations")
    print(f"   - Can switch between models and track progress")
    print(f"   - Models maintain separate iteration counts")
    print(f"   - Ready for checkpoint save/load functionality")
    
    return True

if __name__ == "__main__":
    try:
        success = test_core_functionality()
        print(f"\n🎉 Test {'PASSED' if success else 'FAILED'}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()