# 🏛️ Society Simulation - Model Management Guide

## Overview

The Society simulation now includes a powerful **Model Management System** that allows you to:
- 🔄 Create and manage multiple training models simultaneously
- 💾 Save and load simulation states at any point
- 📊 Compare different experimental configurations
- 🔁 Switch between models without losing progress
- 📈 Track training iterations across different approaches

This solves the exact problem you described: **"save and load our state, start over using a different one, then go back and load the old one that has n number of iterations."**

---

## 🚀 Quick Start

### 1. Basic Usage

```python
from src.simulation.model_manager import ModelManager

# Create model manager
manager = ModelManager("models")  # Creates "models/" directory

# Create your first society model
model_name = manager.create_model(
    name="baseline_society",
    description="Default parameters for initial experiments",
    config={
        "population_size": 100,
        "learning_rate": 0.1,
        "exploration_rate": 0.3
    }
)

print(f"Created model: {model_name}")
```

### 2. Save Simulation State

```python
# During simulation, save checkpoints
checkpoint = manager.save_checkpoint(
    world,  # Your World instance
    name="after_1000_iterations",  # Optional name
    auto_save=False  # Set True for automatic naming
)

print(f"Saved checkpoint: {checkpoint}")
```

### 3. Switch Between Models

```python
# Create different experimental models
manager.create_model("aggressive_economy", "High competition model", {
    "wage_multiplier": 2.0,
    "competition_factor": 1.5
})

manager.create_model("cooperative_society", "Enhanced cooperation", {
    "social_bonus": 1.8,
    "sharing_tendency": 0.7
})

# Switch between them
manager.load_model("aggressive_economy")
# ... run experiments ...

manager.load_model("cooperative_society") 
# ... run different experiments ...

# Go back to baseline
manager.load_model("baseline_society")
```

### 4. Load Previous State

```python
# Load a specific checkpoint from current model
success = manager.load_checkpoint("after_1000_iterations", world)
if success:
    print("Resumed from iteration 1000!")
```

---

## 📁 Directory Structure

When you use the Model Manager, it creates this organized structure:

```
models/
├── models_metadata.json              # Index of all models
├── baseline_society/
│   ├── config.json                   # Model configuration
│   ├── checkpoints/                  # Simulation snapshots
│   │   ├── checkpoint_iter100.pkl
│   │   ├── after_1000_iterations.pkl
│   │   └── auto_iter500.pkl
│   ├── neural_nets/                  # Agent AI states
│   │   ├── checkpoint_iter100/
│   │   └── after_1000_iterations/
│   ├── q_tables/                     # Q-learning tables
│   │   ├── checkpoint_iter100/
│   │   └── after_1000_iterations/
│   └── metrics/                      # Training analytics
├── aggressive_economy/
│   └── [same structure]
└── cooperative_society/
    └── [same structure]
```

---

## 🎮 Complete Workflow Example

### Scenario: Testing Different Economic Policies

```python
#!/usr/bin/env python3
"""Example: Compare economic policies across multiple models"""

import pygame
from src.simulation.model_manager import ModelManager
from src.simulation.world.world import World

def run_economic_experiment():
    # Setup
    pygame.init()
    screen = pygame.display.set_mode((1200, 800))
    manager = ModelManager("economic_experiments")
    
    # Create different economic models
    models = [
        ("laissez_faire", "Minimal economic intervention", {
            "tax_rate": 0.0,
            "welfare_support": 0.0,
            "wage_regulation": False
        }),
        ("social_democracy", "Balanced social support", {
            "tax_rate": 0.25,
            "welfare_support": 0.6,
            "wage_regulation": True,
            "min_wage": 15.0
        }),
        ("command_economy", "Central planning approach", {
            "tax_rate": 0.60,
            "welfare_support": 0.9,
            "wage_regulation": True,
            "resource_redistribution": True
        })
    ]
    
    # Create and train each model
    results = {}
    
    for name, desc, config in models:
        print(f"\\n🏗️  Setting up {name} model...")
        
        # Create model
        manager.create_model(name, desc, config)
        
        # Create world for this model
        world = World(1200, 800)
        
        # Run simulation for 1000 iterations
        for iteration in range(1000):
            world.update(0.016)  # ~60 FPS
            
            # Save checkpoint every 250 iterations
            if iteration % 250 == 0:
                checkpoint = manager.save_checkpoint(
                    world, 
                    name=f"iter_{iteration}"
                )
                print(f"   💾 Saved checkpoint: {checkpoint}")
            
            # Track progress
            if iteration % 100 == 0:
                population = len(world.ecs.get_entities_with_components(["behavior"]))
                print(f"   Iteration {iteration}: Population {population}")
        
        manager.increment_iteration(1000)
        
        # Save final results
        final_checkpoint = manager.save_checkpoint(world, name="final_state")
        print(f"   ✅ Completed {name}: {final_checkpoint}")
        
        # Store results
        results[name] = manager.get_model_info(name)
    
    # Compare results
    print("\\n📊 EXPERIMENT RESULTS:")
    for name, info in results.items():
        print(f"\\n{name.upper()}:")
        print(f"  - Total iterations: {info['total_iterations']}")
        print(f"  - Checkpoints saved: {len(info['checkpoints'])}")
        print(f"  - Config: {info['config']}")
    
    # You can now reload any model and continue from any checkpoint!
    print("\\n🔄 All models saved! You can now:")
    print("  1. Load any model: manager.load_model('laissez_faire')")
    print("  2. Resume from any checkpoint: manager.load_checkpoint('iter_750', world)")
    print("  3. Compare different approaches side by side")
    
    pygame.quit()
    return results

if __name__ == "__main__":
    run_economic_experiment()
```

---

## 🔧 Advanced Features

### 1. Auto-Save During Training

```python
def training_loop_with_autosave(world, manager, iterations=5000):
    """Training loop with automatic checkpoint saving"""
    
    for i in range(iterations):
        world.update(0.016)
        
        # Auto-save every 500 iterations
        if i % 500 == 0:
            manager.save_checkpoint(world, auto_save=True)
            print(f"Auto-saved at iteration {i}")
        
        # Increment iteration counter
        if i % 10 == 0:  # Update every 10 frames
            manager.increment_iteration(1)
    
    # Save final state
    manager.save_checkpoint(world, name="training_complete")
```

### 2. Model Comparison and Analysis

```python
def analyze_models(manager, model_names):
    """Analyze and compare multiple models"""
    
    print("🔍 MODEL ANALYSIS")
    print("=" * 50)
    
    for name in model_names:
        info = manager.get_model_info(name)
        
        print(f"\\n📊 {name.upper()}")
        print(f"   Description: {info['description']}")
        print(f"   Created: {info['created']}")
        print(f"   Total iterations: {info['total_iterations']}")
        print(f"   Checkpoints: {len(info['checkpoints'])}")
        print(f"   Disk usage: {info['disk_usage_mb']:.2f} MB")
        print(f"   Configuration:")
        
        for key, value in info['config'].items():
            print(f"     - {key}: {value}")
        
        # Show latest checkpoints
        if info['checkpoints']:
            print(f"   Latest checkpoints:")
            for checkpoint in info['checkpoints'][-3:]:  # Last 3
                print(f"     - {checkpoint['name']} (Population: {checkpoint['population']})")

# Usage
analyze_models(manager, ["baseline_society", "aggressive_economy", "cooperative_society"])
```

### 3. Resuming Long-Running Experiments

```python
def resume_experiment(model_name, checkpoint_name=None):
    """Resume a long-running experiment from a checkpoint"""
    
    manager = ModelManager("models")
    
    # Load the model
    manager.load_model(model_name)
    
    # Get model info
    info = manager.get_model_info()
    print(f"Model: {model_name}")
    print(f"Current iterations: {info['current_iteration']}")
    print(f"Available checkpoints: {len(info['checkpoints'])}")
    
    # Load specific checkpoint or latest
    if checkpoint_name:
        checkpoint_to_load = checkpoint_name
    else:
        # Load latest checkpoint
        if info['checkpoints']:
            checkpoint_to_load = info['checkpoints'][-1]['name']
        else:
            print("No checkpoints found!")
            return
    
    # Create world and load state
    world = World(1200, 800)
    success = manager.load_checkpoint(checkpoint_to_load, world)
    
    if success:
        print(f"✅ Resumed from checkpoint: {checkpoint_to_load}")
        print(f"Ready to continue training from iteration {info['current_iteration']}")
        return world, manager
    else:
        print(f"❌ Failed to load checkpoint: {checkpoint_to_load}")
        return None, None

# Usage
world, manager = resume_experiment("baseline_society", "after_1000_iterations")
if world:
    # Continue training...
    pass
```

---

## 🎯 Use Cases

### Research Scenarios

1. **A/B Testing**: Create models with different AI parameters, train both, compare results
2. **Economic Policy Research**: Test different economic rules and their emergent outcomes  
3. **Long-term Studies**: Save state every N iterations, analyze population evolution over time
4. **Parameter Sweeps**: Create models with different hyperparameters, find optimal settings
5. **Scenario Analysis**: Save a "base state", then test different crisis scenarios

### Development Workflows

1. **Feature Testing**: Save stable state, test new features, rollback if needed
2. **Performance Comparison**: Test optimizations against baseline models
3. **Bug Investigation**: Reproduce issues by loading specific problematic states
4. **Demo Preparation**: Save interesting states for presentations and demos

---

## 🛠️ Integration with Main Simulation

### Method 1: Add to Existing main.py

```python
# Add to your main.py
from src.simulation.model_manager import ModelManager

def main():
    # Initialize model manager
    manager = ModelManager("models")
    
    # Check if we should resume an existing model
    models = manager.list_models()
    if models:
        print("Available models:")
        for i, model in enumerate(models):
            print(f"{i+1}. {model['name']} ({model['iterations']} iterations)")
        
        choice = input("Load existing model (1-N) or create new (N): ")
        if choice.isdigit() and 1 <= int(choice) <= len(models):
            selected_model = models[int(choice)-1]['name']
            manager.load_model(selected_model)
            print(f"Loaded model: {selected_model}")
    
    # Your existing simulation code...
    world = World(1200, 800)
    
    # Main game loop with periodic saving
    iteration = 0
    while running:
        world.update(0.016)
        
        # Auto-save every 1000 iterations
        iteration += 1
        if iteration % 1000 == 0:
            manager.increment_iteration(1000)
            checkpoint = manager.save_checkpoint(world, auto_save=True)
            print(f"Auto-saved: {checkpoint}")
        
        # Your existing game loop code...
```

### Method 2: Keyboard Shortcuts for Save/Load

```python
# Add to your event handling
if event.type == pygame.KEYDOWN:
    if event.key == pygame.K_F5:  # F5 to save
        checkpoint = manager.save_checkpoint(world, name="manual_save")
        print(f"Manual save: {checkpoint}")
    
    elif event.key == pygame.K_F9:  # F9 to load
        checkpoints = manager.get_model_info()['checkpoints']
        if checkpoints:
            latest = checkpoints[-1]['name']
            if manager.load_checkpoint(latest, world):
                print(f"Loaded: {latest}")
    
    elif event.key == pygame.K_F1:  # F1 to switch models
        models = manager.list_models()
        print("Available models:")
        for model in models:
            print(f"- {model['name']}")
```

---

## ✅ Fixed Issues Summary

### 1. ✅ Save/Load System
- **Problem**: No way to save simulation states and resume later
- **Solution**: Complete model management system with checkpoints
- **Result**: Can save/load any simulation state, switch between models

### 2. ✅ Rendering Issues  
- **Problem**: Sprites clipping, disappearing, transparency not working
- **Solution**: Fixed z-ordering, proper alpha channel handling, layered rendering
- **Result**: Proper sprite layering, transparent backgrounds, no more disappearing sprites

### 3. ✅ Multiple Training Models
- **Problem**: No way to run parallel experiments or compare different approaches  
- **Solution**: Model manager with isolated configurations and states
- **Result**: Can run unlimited parallel experiments, each with separate progress tracking

---

## 🎉 Your Society Simulation Now Has:

✅ **Professional Model Management** - Create, save, load multiple experimental setups  
✅ **Checkpoint System** - Save/resume from any point in training  
✅ **Configuration Tracking** - Each model remembers its parameters  
✅ **Progress Isolation** - Models don't interfere with each other  
✅ **Fixed Rendering** - No more disappearing sprites or clipping issues  
✅ **Transparency Support** - Proper alpha blending for all assets  
✅ **Z-Order Rendering** - Correct layering (dead agents, resources, living agents)  

**Bottom Line**: You can now run multiple society experiments in parallel, save/load states at will, and compare different approaches - exactly what you asked for! 🚀