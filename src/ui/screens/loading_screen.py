"""
Loading/Landing Screen for Society Simulation
Provides model selection, configuration, and simulation startup
"""

import pygame
import json
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class LoadingScreen:
    """Interactive loading and model selection screen"""
    
    def __init__(self, screen_width: int = 1200, screen_height: int = 800):
        self.width = screen_width
        self.height = screen_height
        self.screen = None
        
        # Colors
        self.colors = {
            'background': (15, 23, 42),      # Dark slate
            'primary': (99, 102, 241),       # Indigo
            'secondary': (34, 197, 94),      # Green
            'accent': (245, 101, 101),       # Red
            'text_primary': (241, 245, 249), # Light gray
            'text_secondary': (148, 163, 184), # Medium gray
            'surface': (30, 41, 59),         # Dark surface
            'surface_hover': (51, 65, 85),   # Hover surface
            'border': (71, 85, 105),         # Border gray
        }
        
        # Fonts (will be initialized in init_pygame)
        self.fonts = {}
        
        # UI State
        self.current_screen = "main_menu"  # main_menu, model_select, config, loading
        self.selected_model = None
        self.config_options = {}
        self.loading_progress = 0.0
        self.loading_text = "Initializing..."
        self.animation_time = 0.0
        
        # Models and configuration
        self.available_models = []
        self.model_configs = {}
        
        # UI Elements
        self.buttons = []
        self.input_fields = []
        self.selected_button = 0
        
    def init_pygame(self, screen):
        """Initialize pygame components"""
        self.screen = screen
        
        # Initialize fonts
        pygame.font.init()
        try:
            self.fonts = {
                'title': pygame.font.Font(None, 72),
                'heading': pygame.font.Font(None, 48),
                'body': pygame.font.Font(None, 32),
                'small': pygame.font.Font(None, 24),
                'mono': pygame.font.Font(None, 28)
            }
        except:
            # Fallback to default font
            self.fonts = {
                'title': pygame.font.Font(None, 72),
                'heading': pygame.font.Font(None, 48),  
                'body': pygame.font.Font(None, 32),
                'small': pygame.font.Font(None, 24),
                'mono': pygame.font.Font(None, 28)
            }
    
    def load_available_models(self, model_manager):
        """Load available models from model manager"""
        self.available_models = model_manager.list_models()
        
        # Load configurations for each model
        for model in self.available_models:
            info = model_manager.get_model_info(model['name'])
            self.model_configs[model['name']] = info.get('config', {})
    
    def handle_event(self, event) -> Optional[str]:
        """Handle pygame events, return action if any"""
        if event.type == pygame.KEYDOWN:
            if self.current_screen == "main_menu":
                return self._handle_main_menu_keys(event)
            elif self.current_screen == "model_select":
                return self._handle_model_select_keys(event)
            elif self.current_screen == "config":
                return self._handle_config_keys(event)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                return self._handle_mouse_click(event.pos)
        
        return None
    
    def _handle_main_menu_keys(self, event) -> Optional[str]:
        """Handle main menu keyboard input"""
        if event.key == pygame.K_UP:
            self.selected_button = max(0, self.selected_button - 1)
        elif event.key == pygame.K_DOWN:
            self.selected_button = min(3, self.selected_button + 1)
        elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
            if self.selected_button == 0:  # New Simulation
                self.current_screen = "model_select"
                self.selected_button = 0
            elif self.selected_button == 1:  # Continue Simulation
                return "continue_last"
            elif self.selected_button == 2:  # Load Model
                self.current_screen = "model_select"
                self.selected_button = 0
            elif self.selected_button == 3:  # Exit
                return "exit"
        
        return None
    
    def _handle_model_select_keys(self, event) -> Optional[str]:
        """Handle model selection keyboard input"""
        if event.key == pygame.K_ESCAPE:
            self.current_screen = "main_menu"
            self.selected_button = 0
        elif event.key == pygame.K_UP:
            self.selected_button = max(0, self.selected_button - 1)
        elif event.key == pygame.K_DOWN:
            self.selected_button = min(len(self.available_models), self.selected_button + 1)
        elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
            if self.selected_button < len(self.available_models):
                self.selected_model = self.available_models[self.selected_button]['name']
                self.current_screen = "config"
                self.selected_button = 0
            elif self.selected_button == len(self.available_models):  # Create New Model
                return "create_new_model"
        
        return None
    
    def _handle_config_keys(self, event) -> Optional[str]:
        """Handle configuration screen keyboard input"""
        if event.key == pygame.K_ESCAPE:
            self.current_screen = "model_select"
            self.selected_button = 0
        elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
            if self.selected_button == 0:  # Start Simulation
                return "start_simulation"
            elif self.selected_button == 1:  # Advanced Config
                return "advanced_config"
        elif event.key == pygame.K_UP:
            self.selected_button = max(0, self.selected_button - 1)
        elif event.key == pygame.K_DOWN:
            self.selected_button = min(1, self.selected_button + 1)
        
        return None
    
    def _handle_mouse_click(self, pos: Tuple[int, int]) -> Optional[str]:
        """Handle mouse clicks"""
        # Simple button detection based on screen areas
        # This would be expanded with proper button collision detection
        return None
    
    def update(self, dt: float):
        """Update animation and loading progress"""
        self.animation_time += dt
        
        if self.current_screen == "loading":
            # Simulate loading progress
            self.loading_progress = min(1.0, self.loading_progress + dt * 0.5)
            
            # Update loading text
            phases = [
                "Initializing simulation engine...",
                "Loading agent neural networks...",
                "Setting up economic systems...",
                "Preparing social dynamics...",
                "Optimizing performance...",
                "Ready to begin!"
            ]
            
            phase_index = int(self.loading_progress * len(phases))
            if phase_index < len(phases):
                self.loading_text = phases[phase_index]
    
    def render(self):
        """Render the current screen"""
        if not self.screen:
            return
        
        self.screen.fill(self.colors['background'])
        
        if self.current_screen == "main_menu":
            self._render_main_menu()
        elif self.current_screen == "model_select":
            self._render_model_select()
        elif self.current_screen == "config":
            self._render_config()
        elif self.current_screen == "loading":
            self._render_loading()
        
        pygame.display.flip()
    
    def _render_main_menu(self):
        """Render main menu screen"""
        center_x = self.width // 2
        
        # Title
        title_text = self.fonts['title'].render("SOCIETY SIMULATION", True, self.colors['primary'])
        title_rect = title_text.get_rect(center=(center_x, 150))
        self.screen.blit(title_text, title_rect)
        
        # Subtitle
        subtitle_text = self.fonts['body'].render("Agent-Based Social & Economic Evolution", True, self.colors['text_secondary'])
        subtitle_rect = subtitle_text.get_rect(center=(center_x, 200))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Menu options
        menu_options = [
            "New Simulation",
            "Continue Last Session",
            "Load Existing Model", 
            "Exit"
        ]
        
        for i, option in enumerate(menu_options):
            color = self.colors['secondary'] if i == self.selected_button else self.colors['text_primary']
            bg_color = self.colors['surface_hover'] if i == self.selected_button else self.colors['surface']
            
            # Button background
            button_rect = pygame.Rect(center_x - 150, 300 + i * 80, 300, 60)
            pygame.draw.rect(self.screen, bg_color, button_rect, border_radius=8)
            pygame.draw.rect(self.screen, self.colors['border'], button_rect, 2, border_radius=8)
            
            # Button text
            text = self.fonts['body'].render(option, True, color)
            text_rect = text.get_rect(center=button_rect.center)
            self.screen.blit(text, text_rect)
        
        # Instructions
        instruction_text = self.fonts['small'].render("Use ↑↓ arrows and ENTER to navigate", True, self.colors['text_secondary'])
        instruction_rect = instruction_text.get_rect(center=(center_x, self.height - 50))
        self.screen.blit(instruction_text, instruction_rect)
        
        # Version info
        version_text = self.fonts['small'].render("Society Sim v2.0 - ML Enhanced", True, self.colors['text_secondary'])
        version_rect = version_text.get_rect(bottomright=(self.width - 20, self.height - 20))
        self.screen.blit(version_text, version_rect)
    
    def _render_model_select(self):
        """Render model selection screen"""
        center_x = self.width // 2
        
        # Header
        header_text = self.fonts['heading'].render("Select Training Model", True, self.colors['primary'])
        header_rect = header_text.get_rect(center=(center_x, 80))
        self.screen.blit(header_text, header_rect)
        
        # Model list
        y_start = 150
        for i, model in enumerate(self.available_models):
            is_selected = i == self.selected_button
            
            # Model card
            card_rect = pygame.Rect(100, y_start + i * 100, self.width - 200, 80)
            bg_color = self.colors['surface_hover'] if is_selected else self.colors['surface']
            pygame.draw.rect(self.screen, bg_color, card_rect, border_radius=8)
            pygame.draw.rect(self.screen, self.colors['border'], card_rect, 2, border_radius=8)
            
            # Model name
            name_color = self.colors['secondary'] if is_selected else self.colors['text_primary']
            name_text = self.fonts['body'].render(model['name'], True, name_color)
            name_rect = name_text.get_rect(topleft=(card_rect.x + 20, card_rect.y + 10))
            self.screen.blit(name_text, name_rect)
            
            # Model description
            desc_text = self.fonts['small'].render(model['description'][:60] + "..." if len(model['description']) > 60 else model['description'], True, self.colors['text_secondary'])
            desc_rect = desc_text.get_rect(topleft=(card_rect.x + 20, card_rect.y + 40))
            self.screen.blit(desc_text, desc_rect)
            
            # Model stats
            stats_text = f"Iterations: {model['iterations']} | Checkpoints: {model['checkpoints']}"
            stats_render = self.fonts['small'].render(stats_text, True, self.colors['text_secondary'])
            stats_rect = stats_render.get_rect(topright=(card_rect.right - 20, card_rect.y + 10))
            self.screen.blit(stats_render, stats_rect)
        
        # Create new model option
        new_model_selected = self.selected_button == len(self.available_models)
        new_card_rect = pygame.Rect(100, y_start + len(self.available_models) * 100, self.width - 200, 80)
        new_bg_color = self.colors['accent'] if new_model_selected else self.colors['surface']
        pygame.draw.rect(self.screen, new_bg_color, new_card_rect, border_radius=8)
        pygame.draw.rect(self.screen, self.colors['border'], new_card_rect, 2, border_radius=8)
        
        new_text_color = self.colors['text_primary']
        new_text = self.fonts['body'].render("+ Create New Model", True, new_text_color)
        new_text_rect = new_text.get_rect(center=new_card_rect.center)
        self.screen.blit(new_text, new_text_rect)
        
        # Instructions
        instruction_text = self.fonts['small'].render("ESC: Back | ↑↓: Navigate | ENTER: Select", True, self.colors['text_secondary'])
        instruction_rect = instruction_text.get_rect(center=(center_x, self.height - 50))
        self.screen.blit(instruction_text, instruction_rect)
    
    def _render_config(self):
        """Render configuration screen"""
        if not self.selected_model:
            return
        
        center_x = self.width // 2
        
        # Header
        header_text = self.fonts['heading'].render(f"Configure: {self.selected_model}", True, self.colors['primary'])
        header_rect = header_text.get_rect(center=(center_x, 80))
        self.screen.blit(header_text, header_rect)
        
        # Model configuration display
        config = self.model_configs.get(self.selected_model, {})
        
        y_pos = 150
        for key, value in config.items():
            key_text = self.fonts['body'].render(f"{key}:", True, self.colors['text_primary'])
            value_text = self.fonts['body'].render(str(value), True, self.colors['secondary'])
            
            self.screen.blit(key_text, (200, y_pos))
            self.screen.blit(value_text, (400, y_pos))
            y_pos += 40
        
        # Action buttons
        button_options = ["Start Simulation", "Advanced Configuration"]
        
        for i, option in enumerate(button_options):
            is_selected = i == self.selected_button
            
            button_rect = pygame.Rect(center_x - 150, 450 + i * 80, 300, 60)
            bg_color = self.colors['surface_hover'] if is_selected else self.colors['surface']
            text_color = self.colors['secondary'] if is_selected else self.colors['text_primary']
            
            pygame.draw.rect(self.screen, bg_color, button_rect, border_radius=8)
            pygame.draw.rect(self.screen, self.colors['border'], button_rect, 2, border_radius=8)
            
            text = self.fonts['body'].render(option, True, text_color)
            text_rect = text.get_rect(center=button_rect.center)
            self.screen.blit(text, text_rect)
        
        # Instructions
        instruction_text = self.fonts['small'].render("ESC: Back | ↑↓: Navigate | ENTER: Select", True, self.colors['text_secondary'])
        instruction_rect = instruction_text.get_rect(center=(center_x, self.height - 50))
        self.screen.blit(instruction_text, instruction_rect)
    
    def _render_loading(self):
        """Render loading screen with progress"""
        center_x = self.width // 2
        center_y = self.height // 2
        
        # Loading title
        loading_text = self.fonts['heading'].render("Initializing Simulation", True, self.colors['primary'])
        loading_rect = loading_text.get_rect(center=(center_x, center_y - 100))
        self.screen.blit(loading_text, loading_rect)
        
        # Progress bar
        bar_width = 400
        bar_height = 20
        bar_x = center_x - bar_width // 2
        bar_y = center_y - 20
        
        # Background
        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(self.screen, self.colors['surface'], bg_rect, border_radius=10)
        pygame.draw.rect(self.screen, self.colors['border'], bg_rect, 2, border_radius=10)
        
        # Progress fill
        fill_width = int(bar_width * self.loading_progress)
        if fill_width > 0:
            fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
            pygame.draw.rect(self.screen, self.colors['secondary'], fill_rect, border_radius=10)
        
        # Progress percentage
        percent_text = f"{int(self.loading_progress * 100)}%"
        percent_render = self.fonts['body'].render(percent_text, True, self.colors['text_primary'])
        percent_rect = percent_render.get_rect(center=(center_x, bar_y + bar_height + 30))
        self.screen.blit(percent_render, percent_rect)
        
        # Loading status text
        status_render = self.fonts['body'].render(self.loading_text, True, self.colors['text_secondary'])
        status_rect = status_render.get_rect(center=(center_x, center_y + 60))
        self.screen.blit(status_render, status_rect)
        
        # Animated loading dots
        dots_count = int(self.animation_time * 2) % 4
        dots_text = "Loading" + "." * dots_count + " " * (3 - dots_count)
        dots_render = self.fonts['small'].render(dots_text, True, self.colors['text_secondary'])
        dots_rect = dots_render.get_rect(center=(center_x, center_y + 100))
        self.screen.blit(dots_render, dots_rect)
    
    def start_loading(self):
        """Switch to loading screen"""
        self.current_screen = "loading"
        self.loading_progress = 0.0
        self.loading_text = "Initializing..."
    
    def is_loading_complete(self) -> bool:
        """Check if loading is complete"""
        return self.loading_progress >= 1.0
    
    def get_selected_model(self) -> Optional[str]:
        """Get the currently selected model"""
        return self.selected_model
    
    def set_models(self, models: List[Dict]):
        """Set available models list"""
        self.available_models = models