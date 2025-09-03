"""
Speed Optimization System for Society Simulation
Enables 3x, 5x, and 10x simulation speeds with different rendering modes
"""

import time
from typing import Dict, Tuple, Optional
from enum import Enum
import threading
import queue

class SpeedMode(Enum):
    """Simulation speed modes"""
    NORMAL = 1.0      # 1x - Normal speed with full rendering
    FAST = 3.0        # 3x - Reduced rendering updates
    FASTER = 5.0      # 5x - Minimal rendering, batch updates
    FASTEST = 10.0    # 10x - Headless mode, statistics only

class RenderMode(Enum):
    """Rendering complexity modes"""
    FULL = "full"           # All sprites, animations, effects
    REDUCED = "reduced"     # Essential sprites only, no animations
    MINIMAL = "minimal"     # Basic shapes and indicators
    HEADLESS = "headless"   # No rendering, data only

class SpeedOptimizer:
    """Manages simulation speed and rendering optimization"""
    
    def __init__(self):
        self.current_speed = SpeedMode.NORMAL
        self.current_render_mode = RenderMode.FULL
        
        # Performance tracking
        self.frame_times = []
        self.max_frame_samples = 100
        self.target_fps = 60
        
        # Speed optimization settings
        self.speed_configs = {
            SpeedMode.NORMAL: {
                "render_mode": RenderMode.FULL,
                "physics_steps_per_frame": 1,
                "render_every_n_frames": 1,
                "system_update_frequency": 1.0,
                "batch_size": 1,
                "enable_animations": True,
                "enable_particles": True,
                "enable_shadows": True
            },
            SpeedMode.FAST: {
                "render_mode": RenderMode.REDUCED,
                "physics_steps_per_frame": 3,
                "render_every_n_frames": 2,
                "system_update_frequency": 0.7,
                "batch_size": 5,
                "enable_animations": False,
                "enable_particles": False,
                "enable_shadows": False
            },
            SpeedMode.FASTER: {
                "render_mode": RenderMode.MINIMAL,
                "physics_steps_per_frame": 5,
                "render_every_n_frames": 5,
                "system_update_frequency": 0.5,
                "batch_size": 10,
                "enable_animations": False,
                "enable_particles": False,
                "enable_shadows": False
            },
            SpeedMode.FASTEST: {
                "render_mode": RenderMode.HEADLESS,
                "physics_steps_per_frame": 10,
                "render_every_n_frames": 100,
                "system_update_frequency": 0.2,
                "batch_size": 50,
                "enable_animations": False,
                "enable_particles": False,
                "enable_shadows": False
            }
        }
        
        # Frame counting for selective rendering
        self.frame_count = 0
        self.last_render_frame = 0
        
        # Background processing
        self.background_thread = None
        self.background_queue = queue.Queue()
        self.is_background_processing = False
        
        # Performance metrics
        self.metrics = {
            "avg_fps": 0.0,
            "simulation_time": 0.0,
            "render_time": 0.0,
            "system_update_time": 0.0,
            "agents_processed": 0,
            "iterations_per_second": 0.0
        }
        
        # Time tracking
        self.last_update_time = time.time()
        self.accumulated_time = 0.0
    
    def set_speed_mode(self, speed_mode: SpeedMode):
        """Change simulation speed mode"""
        self.current_speed = speed_mode
        config = self.speed_configs[speed_mode]
        self.current_render_mode = config["render_mode"]
        
        print(f"🚀 Speed mode: {speed_mode.name} ({speed_mode.value}x)")
        print(f"   Render mode: {self.current_render_mode.value}")
        print(f"   Physics steps per frame: {config['physics_steps_per_frame']}")
        print(f"   Render every {config['render_every_n_frames']} frames")
    
    def get_current_config(self) -> Dict:
        """Get current optimization configuration"""
        return self.speed_configs[self.current_speed]
    
    def should_render_frame(self) -> bool:
        """Determine if current frame should be rendered"""
        config = self.get_current_config()
        render_interval = config["render_every_n_frames"]
        
        should_render = (self.frame_count % render_interval) == 0
        
        if should_render:
            self.last_render_frame = self.frame_count
        
        return should_render
    
    def get_physics_steps(self) -> int:
        """Get number of physics steps for current frame"""
        config = self.get_current_config()
        return config["physics_steps_per_frame"]
    
    def get_system_update_frequency(self) -> float:
        """Get system update frequency multiplier"""
        config = self.get_current_config()
        return config["system_update_frequency"]
    
    def get_batch_size(self) -> int:
        """Get batch processing size for current speed mode"""
        config = self.get_current_config()
        return config["batch_size"]
    
    def update_frame_timing(self, frame_start_time: float):
        """Update frame timing metrics"""
        frame_time = time.time() - frame_start_time
        
        # Keep rolling average of frame times
        self.frame_times.append(frame_time)
        if len(self.frame_times) > self.max_frame_samples:
            self.frame_times.pop(0)
        
        # Calculate metrics
        if self.frame_times:
            avg_frame_time = sum(self.frame_times) / len(self.frame_times)
            self.metrics["avg_fps"] = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
        
        self.frame_count += 1
    
    def optimize_world_update(self, world, dt: float) -> float:
        """Optimize world update based on current speed mode"""
        config = self.get_current_config()
        
        # Adjust delta time for speed
        optimized_dt = dt * self.current_speed.value
        
        # Batch multiple updates for higher speeds
        physics_steps = config["physics_steps_per_frame"]
        step_dt = optimized_dt / physics_steps
        
        update_start = time.time()
        
        for _ in range(physics_steps):
            # Update with reduced system frequency for performance
            world.update_with_frequency(step_dt, config["system_update_frequency"])
        
        self.metrics["system_update_time"] = time.time() - update_start
        self.metrics["agents_processed"] = len(world.ecs.get_entities_with_components(["behavior"]))
        
        return optimized_dt
    
    def optimize_rendering(self, render_manager, world):
        """Optimize rendering based on current mode"""
        if not self.should_render_frame():
            return False
        
        render_start = time.time()
        
        if self.current_render_mode == RenderMode.HEADLESS:
            # Skip all rendering
            return False
        
        elif self.current_render_mode == RenderMode.MINIMAL:
            # Render basic shapes only
            self._render_minimal(render_manager, world)
        
        elif self.current_render_mode == RenderMode.REDUCED:
            # Render essential sprites without animations
            self._render_reduced(render_manager, world)
        
        else:  # FULL rendering
            # Standard full rendering
            render_manager.render()
        
        self.metrics["render_time"] = time.time() - render_start
        return True
    
    def _render_minimal(self, render_manager, world):
        """Minimal rendering - basic shapes and colors"""
        import pygame
        
        # Clear background
        render_manager.screen.fill((30, 50, 30))
        
        # Draw agents as colored circles
        agents = world.ecs.get_entities_with_components(["transform", "behavior", "tag"])
        
        for entity_id in agents:
            transform = world.ecs.get_component(entity_id, "transform")
            behavior = world.ecs.get_component(entity_id, "behavior")
            tag = world.ecs.get_component(entity_id, "tag")
            
            if not transform or not behavior or not tag:
                continue
            
            # Color based on state
            color = (100, 100, 100)  # Default gray
            if behavior.state == "dead":
                color = (100, 0, 0)     # Dark red
            elif behavior.state == "eating":
                color = (0, 255, 0)     # Green
            elif behavior.state == "working":
                color = (0, 0, 255)     # Blue
            elif behavior.state == "mating":
                color = (255, 0, 255)   # Magenta
            elif tag.tag == "agent":
                color = (255, 255, 255) # White for healthy agents
            
            # Draw circle
            pos = (int(transform.position[0]), int(transform.position[1]))
            pygame.draw.circle(render_manager.screen, color, pos, 3)
    
    def _render_reduced(self, render_manager, world):
        """Reduced rendering - essential sprites only"""
        # Use render manager but skip animations and effects
        render_manager.render()
    
    def start_background_processing(self):
        """Start background thread for non-critical processing"""
        if self.background_thread and self.background_thread.is_alive():
            return
        
        self.is_background_processing = True
        self.background_thread = threading.Thread(target=self._background_worker)
        self.background_thread.daemon = True
        self.background_thread.start()
    
    def stop_background_processing(self):
        """Stop background processing thread"""
        self.is_background_processing = False
        if self.background_thread:
            self.background_thread.join(timeout=1.0)
    
    def _background_worker(self):
        """Background worker for non-critical tasks"""
        while self.is_background_processing:
            try:
                # Process background tasks (analytics, logging, etc.)
                task = self.background_queue.get(timeout=0.1)
                
                if task["type"] == "analytics":
                    self._process_analytics(task["data"])
                elif task["type"] == "logging":
                    self._process_logging(task["data"])
                
                self.background_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Background processing error: {e}")
    
    def _process_analytics(self, data):
        """Process analytics data in background"""
        # Calculate performance metrics, evolution statistics, etc.
        pass
    
    def _process_logging(self, data):
        """Process logging data in background"""
        # Write simulation logs, agent behavior logs, etc.
        pass
    
    def queue_background_task(self, task_type: str, data):
        """Queue a task for background processing"""
        if self.is_background_processing:
            self.background_queue.put({"type": task_type, "data": data})
    
    def get_performance_metrics(self) -> Dict:
        """Get current performance metrics"""
        current_time = time.time()
        self.accumulated_time += current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Calculate iterations per second
        if self.accumulated_time > 0:
            self.metrics["iterations_per_second"] = self.frame_count / self.accumulated_time
        
        self.metrics["simulation_time"] = self.accumulated_time
        
        return self.metrics.copy()
    
    def get_speed_summary(self) -> str:
        """Get human-readable speed summary"""
        metrics = self.get_performance_metrics()
        
        return f"""🚀 Speed Optimization Status:
Mode: {self.current_speed.name} ({self.current_speed.value}x)
Render: {self.current_render_mode.value}
FPS: {metrics['avg_fps']:.1f}
IPS: {metrics['iterations_per_second']:.1f}
Agents: {metrics['agents_processed']}
Sim Time: {metrics['simulation_time']:.1f}s"""
    
    def auto_optimize(self, target_fps: float = 60.0):
        """Automatically optimize speed based on performance"""
        current_fps = self.metrics["avg_fps"]
        
        if current_fps < target_fps * 0.8:  # Performance too low
            # Consider downgrading speed mode
            current_modes = list(SpeedMode)
            current_index = current_modes.index(self.current_speed)
            
            if current_index > 0:  # Can downgrade
                new_mode = current_modes[current_index - 1]
                self.set_speed_mode(new_mode)
                print(f"🔽 Auto-optimized: Reduced to {new_mode.name} for better performance")
        
        elif current_fps > target_fps * 1.2:  # Performance headroom available
            # Consider upgrading speed mode
            current_modes = list(SpeedMode)
            current_index = current_modes.index(self.current_speed)
            
            if current_index < len(current_modes) - 1:  # Can upgrade
                new_mode = current_modes[current_index + 1]
                self.set_speed_mode(new_mode)
                print(f"🔼 Auto-optimized: Increased to {new_mode.name} for faster simulation")
    
    def reset_metrics(self):
        """Reset performance metrics"""
        self.frame_times.clear()
        self.frame_count = 0
        self.accumulated_time = 0.0
        self.last_update_time = time.time()
        
        self.metrics = {
            "avg_fps": 0.0,
            "simulation_time": 0.0,
            "render_time": 0.0,
            "system_update_time": 0.0,
            "agents_processed": 0,
            "iterations_per_second": 0.0
        }