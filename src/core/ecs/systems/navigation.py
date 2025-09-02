import random
import math

class NavigationSystem:
    def __init__(self, world):
        self.world = world
    
    def move_randomly(self, agent):
        """Move agent in a random direction with energy cost based on metabolism"""
        transform = self.world.ecs.get_component(agent.ecs_id, "transform")
        if not transform:
            return
            
        # Random direction vector
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(0.5, 1.5) * agent.genome.stamina
        
        # Calculate velocity
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        
        # Set velocity
        transform.velocity = (vx, vy)
        
        # Energy cost based on speed and metabolism
        energy_cost = speed * agent.genome.metabolism * 0.5
        agent.energy -= energy_cost
        
        return energy_cost
    
    def move_toward_target(self, agent, target_position, speed_factor=1.0):
        """Move agent toward a specific target with appropriate energy cost"""
        transform = self.world.ecs.get_component(agent.ecs_id, "transform")
        if not transform:
            return 0
            
        # Calculate direction to target
        x, y = transform.position
        tx, ty = target_position
        dx, dy = tx - x, ty - y
        distance = max(1.0, math.sqrt(dx*dx + dy*dy))
        
        # Calculate velocity (scaled by stamina and requested speed)
        speed = min(distance, 2.0 * agent.genome.stamina * speed_factor)
        vx = dx/distance * speed
        vy = dy/distance * speed
        
        # Set velocity
        transform.velocity = (vx, vy)
        
        # Energy cost based on speed and metabolism
        energy_cost = speed * agent.genome.metabolism * 0.5
        agent.energy -= energy_cost

        return energy_cost
        
    
    def navigate_to_goal(self, agent, goal_position, speed_factor=1.0):
        """Navigate agent toward a goal with obstacle awareness"""
        transform = self.world.ecs.get_component(agent.ecs_id, "transform")
        if not transform:
            return 0
        
        # Get current position
        x, y = transform.position
        
        # Calculate direct path to goal
        dx, dy = goal_position[0] - x, goal_position[1] - y
        distance = max(1.0, math.sqrt(dx*dx + dy*dy))
        
        # If we're very close to goal, slow down
        if distance < 10:
            speed_factor *= 0.5
        
        # Check for obstacles in path (simplified)
        spatial = self.world.ecs.get_system("spatial")
        if spatial:
            # Look ahead in our path
            look_ahead = 50.0
            check_position = (x + dx/distance * look_ahead, y + dy/distance * look_ahead)
            
            # Find obstacles near our projected path
            obstacles = spatial.find_by_tag(check_position, 30, "tag", "obstacle")
            
            # If obstacles found, adjust path
            if obstacles:
                # Simple avoidance - perturb the direction
                perturbation = random.uniform(-0.5, 0.5)
                angle = math.atan2(dy, dx) + perturbation
                dx = math.cos(angle) * distance
                dy = math.sin(angle) * distance
        
        # Calculate velocity
        speed = min(distance, 2.0 * agent.genome.stamina * speed_factor)
        vx = dx/distance * speed
        vy = dy/distance * speed
        
        # Set velocity
        transform.velocity = (vx, vy)
        
        # Energy cost based on speed and metabolism
        energy_cost = speed * agent.genome.metabolism * 0.5
        agent.energy -= energy_cost
        
        return energy_cost

    def update(self, dt):
        """Update method required by ECS - Navigation is primarily a utility system"""
        # NavigationSystem is primarily invoked by other systems
        # and doesn't need to perform autonomous updates
        pass
