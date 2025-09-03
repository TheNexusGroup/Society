#!/usr/bin/env python3
"""Test the speed optimization system"""

import time
from src.simulation.speed_optimizer import SpeedOptimizer, SpeedMode, RenderMode

def test_speed_optimizer():
    """Test speed optimizer functionality"""
    print("🚀 Testing Speed Optimization System\n")
    
    # Create optimizer
    optimizer = SpeedOptimizer()
    
    # Test 1: Speed mode changes
    print("1️⃣ Testing speed mode changes...")
    modes = [SpeedMode.NORMAL, SpeedMode.FAST, SpeedMode.FASTER, SpeedMode.FASTEST]
    
    for mode in modes:
        optimizer.set_speed_mode(mode)
        config = optimizer.get_current_config()
        
        print(f"   Mode: {mode.name} ({mode.value}x)")
        print(f"   - Render mode: {optimizer.current_render_mode.value}")
        print(f"   - Physics steps: {config['physics_steps_per_frame']}")
        print(f"   - Render interval: {config['render_every_n_frames']}")
        print(f"   - Batch size: {config['batch_size']}")
        print()
    
    # Test 2: Frame rendering logic
    print("2️⃣ Testing frame rendering logic...")
    optimizer.set_speed_mode(SpeedMode.FAST)  # Render every 2 frames
    
    render_count = 0
    for frame in range(10):
        optimizer.frame_count = frame
        should_render = optimizer.should_render_frame()
        if should_render:
            render_count += 1
        print(f"   Frame {frame}: {'Render' if should_render else 'Skip'}")
    
    expected_renders = 5  # Every 2nd frame
    print(f"   Expected renders: {expected_renders}, Actual: {render_count}")
    assert render_count == expected_renders, "Render logic failed"
    
    # Test 3: Performance tracking
    print("3️⃣ Testing performance tracking...")
    optimizer.reset_metrics()
    
    # Simulate some frame updates
    for i in range(5):
        frame_start = time.time()
        time.sleep(0.01)  # Simulate work
        optimizer.update_frame_timing(frame_start)
    
    metrics = optimizer.get_performance_metrics()
    print(f"   FPS: {metrics['avg_fps']:.1f}")
    print(f"   Frame count: {optimizer.frame_count}")
    print(f"   Simulation time: {metrics['simulation_time']:.2f}s")
    
    # Test 4: Physics steps
    print("4️⃣ Testing physics steps...")
    for mode in modes:
        optimizer.set_speed_mode(mode)
        steps = optimizer.get_physics_steps()
        print(f"   {mode.name}: {steps} physics steps per frame")
    
    # Test 5: Auto-optimization
    print("5️⃣ Testing auto-optimization...")
    
    # Simulate low performance
    optimizer.metrics['avg_fps'] = 30.0  # Below target of 60
    current_mode = optimizer.current_speed
    print(f"   Before auto-optimization: {current_mode.name}")
    
    optimizer.auto_optimize(target_fps=60.0)
    new_mode = optimizer.current_speed
    print(f"   After auto-optimization: {new_mode.name}")
    
    # Should have downgraded for better performance
    assert new_mode.value <= current_mode.value, "Auto-optimization should reduce speed when FPS is low"
    
    print("\n✅ Speed Optimizer tests passed!")
    return True

if __name__ == "__main__":
    test_speed_optimizer()