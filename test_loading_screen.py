#!/usr/bin/env python3
"""Test the loading screen functionality"""

import pygame
import time
from src.ui.screens.loading_screen import LoadingScreen
from src.simulation.model_manager import ModelManager

def test_loading_screen():
    """Test loading screen functionality"""
    print("🎮 Testing Loading Screen System\n")
    
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((1200, 800))
    pygame.display.set_caption("Loading Screen Test")
    
    try:
        # Test 1: Initialize loading screen
        print("1️⃣ Testing loading screen initialization...")
        loading_screen = LoadingScreen(1200, 800)
        loading_screen.init_pygame(screen)
        print("   ✅ Loading screen initialized")
        
        # Test 2: Create some test models
        print("2️⃣ Setting up test models...")
        manager = ModelManager("test_models")
        
        # Create a few test models
        model1 = manager.create_model("test_baseline", "Test baseline model", {
            "population_size": 50,
            "learning_rate": 0.1
        })
        
        model2 = manager.create_model("test_advanced", "Test advanced model", {
            "population_size": 100,
            "learning_rate": 0.2,
            "exploration_rate": 0.3
        })
        
        print(f"   Created models: {model1}, {model2}")
        
        # Test 3: Load models into loading screen
        print("3️⃣ Loading models into loading screen...")
        loading_screen.load_available_models(manager)
        print(f"   Loaded {len(loading_screen.available_models)} models")
        
        # Test 4: Test screen transitions
        print("4️⃣ Testing screen transitions...")
        
        # Start at main menu
        assert loading_screen.current_screen == "main_menu"
        print("   ✅ Started at main menu")
        
        # Simulate key events
        event = type('MockEvent', (), {})()
        event.type = pygame.KEYDOWN
        event.key = pygame.K_DOWN
        
        # Test navigation
        old_button = loading_screen.selected_button
        loading_screen.handle_event(event)
        new_button = loading_screen.selected_button
        
        assert new_button == old_button + 1, "Down key should move selection down"
        print("   ✅ Navigation working")
        
        # Test 5: Test loading progress
        print("5️⃣ Testing loading progress...")
        loading_screen.start_loading()
        assert loading_screen.current_screen == "loading"
        print("   ✅ Loading screen activated")
        
        # Simulate loading progress
        for i in range(25):  # Need more iterations to reach 100%
            loading_screen.update(0.1)
            progress_pct = loading_screen.loading_progress * 100
            if i % 5 == 0:  # Print every 5th iteration
                print(f"   Loading progress: {progress_pct:.1f}%")
            if loading_screen.is_loading_complete():
                break
        
        assert loading_screen.is_loading_complete()
        print("   ✅ Loading completed")
        
        # Test 6: Render test (just make sure it doesn't crash)
        print("6️⃣ Testing rendering...")
        
        # Test different screens
        screens = ["main_menu", "model_select", "config", "loading"]
        for screen_name in screens:
            loading_screen.current_screen = screen_name
            loading_screen.render()  # Should not crash
            pygame.display.flip()
        
        print("   ✅ All screens render without error")
        
        # Test 7: Model selection
        print("7️⃣ Testing model selection...")
        loading_screen.current_screen = "model_select"
        loading_screen.selected_button = 0  # First model
        
        # Simulate selecting model
        event.key = pygame.K_RETURN
        action = loading_screen.handle_event(event)
        
        # Should have selected the model
        assert loading_screen.selected_model is not None
        print(f"   ✅ Selected model: {loading_screen.selected_model}")
        
        print("\n✅ Loading Screen tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Loading screen test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        pygame.quit()

if __name__ == "__main__":
    test_loading_screen()