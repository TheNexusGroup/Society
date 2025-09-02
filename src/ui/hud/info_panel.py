import pygame
from typing import Dict, List, Tuple
from ..visualization.charts import LineChart, BarChart, PieChart

class InfoPanel:
    def __init__(self, screen, x=10, y=10, width=300, height=800):
        self.screen = screen
        self.rect = pygame.Rect(x, y, width, height)
        self.background_color = (30, 30, 40, 200)  # Dark with transparency
        self.text_color = (220, 220, 220)
        self.border_color = (100, 100, 150)
        self.visible = True
        
        # Create panel surface with transparency
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Font initialization
        self.title_font = pygame.font.SysFont('Arial', 20, bold=True)
        self.label_font = pygame.font.SysFont('Arial', 16)
        self.value_font = pygame.font.SysFont('Arial', 14)
        
        # Charts
        self.charts = {
            'population': LineChart(width-20, 100, ['Population']),
            'demographics': PieChart(width//2-20, 150),
            'resources': BarChart(width-20, 80, ['Food', 'Work'])
        }
        
        # Statistics
        self.stats = {
            'population': 0,
            'epoch': 0,
            'male_count': 0,
            'female_count': 0,
            'food_count': 0,
            'work_count': 0,
            'avg_age': 0,
            'avg_energy': 0,
            'avg_money': 0
        }
        
        # History for charts
        self.history = {
            'population': [],
            'resources': [[], []]  # Food, Work
        }
        
    def toggle(self):
        """Toggle visibility of the info panel"""
        self.visible = not self.visible
        
    def update(self, world):
        """Update panel with current simulation stats"""
        if not self.visible:
            return
        
        # Get metrics from world's metrics collector
        metrics = world.metrics
        
        # Update statistics from metrics
        self.stats['population'] = metrics.get_latest('population_size')
        self.stats['epoch'] = metrics.get_latest('epoch')
        self.stats['female_count'] = metrics.get_latest('female_count')
        self.stats['male_count'] = metrics.get_latest('male_count')
        self.stats['food_count'] = metrics.get_latest('food_count')
        self.stats['work_count'] = metrics.get_latest('work_count')
        self.stats['avg_age'] = metrics.get_latest('avg_age')
        self.stats['avg_energy'] = metrics.get_latest('avg_energy')
        self.stats['avg_money'] = metrics.get_latest('avg_money')
        
        # Update history for charts
        self.history['population'].append(self.stats['population'])
        if len(self.history['population']) > 100:
            self.history['population'] = self.history['population'][-100:]
        
        self.history['resources'][0].append(self.stats['food_count'])
        self.history['resources'][1].append(self.stats['work_count'])
        if len(self.history['resources'][0]) > 100:
            self.history['resources'][0] = self.history['resources'][0][-100:]
            self.history['resources'][1] = self.history['resources'][1][-100:]
        
        # Update charts
        self.charts['population'].update([self.history['population']])
        
        # Update demographics chart with labels and values separately
        self.charts['demographics'].update(
            ['Female', 'Male'],
            [self.stats['female_count'], self.stats['male_count']]
        )
        
        self.charts['resources'].update(
            [self.history['resources'][0][-10:] if self.history['resources'][0] else [],
             self.history['resources'][1][-10:] if self.history['resources'][1] else []]
        )
        
    def render(self):
        """Render the info panel to the screen"""
        if not self.visible:
            return
            
        # Clear panel surface
        self.surface.fill((0, 0, 0, 0))
        
        # Draw background with transparency
        pygame.draw.rect(self.surface, self.background_color, 
                        (0, 0, self.rect.width, self.rect.height))
        
        # Draw border
        pygame.draw.rect(self.surface, self.border_color, 
                        (0, 0, self.rect.width, self.rect.height), 2)
        
        # Draw title
        title = self.title_font.render("Simulation Statistics", True, self.text_color)
        self.surface.blit(title, (self.rect.width//2 - title.get_width()//2, 10))
        
        y_offset = 50
        
        # Population section
        section_title = self.label_font.render("Population", True, self.text_color)
        self.surface.blit(section_title, (10, y_offset))
        y_offset += 25
        
        # Population count
        pop_text = self.value_font.render(f"Count: {self.stats['population']}", True, self.text_color)
        self.surface.blit(pop_text, (20, y_offset))
        y_offset += 20
        
        # Epoch
        gen_text = self.value_font.render(f"Epoch: {self.stats['epoch']}", True, self.text_color)
        self.surface.blit(gen_text, (20, y_offset))
        y_offset += 20
        
        # Gender distribution
        gender_text = self.value_font.render(
            f"Gender: {self.stats['female_count']} females, {self.stats['male_count']} males", 
            True, self.text_color
        )
        self.surface.blit(gender_text, (20, y_offset))
        y_offset += 30
        
        # Population chart label
        chart_title = self.label_font.render("Population History", True, self.text_color)
        self.surface.blit(chart_title, (10, y_offset))
        y_offset += 20
        
        # Population chart
        self.surface.blit(self.charts['population'].surface, (10, y_offset))
        y_offset += 110
        
        # Demographics pie chart
        gender_title = self.label_font.render("Gender Distribution", True, self.text_color)
        self.surface.blit(gender_title, (10, y_offset))
        y_offset += 25
        self.surface.blit(self.charts['demographics'].surface, 
                         (self.rect.width//2 - self.charts['demographics'].width//2, y_offset))
        y_offset += 160
        
        # Resources section
        resource_title = self.label_font.render("Resources", True, self.text_color)
        self.surface.blit(resource_title, (10, y_offset))
        y_offset += 25
        
        # Resource counts
        food_text = self.value_font.render(f"Food: {self.stats['food_count']}", True, self.text_color)
        self.surface.blit(food_text, (20, y_offset))
        y_offset += 20
        
        work_text = self.value_font.render(f"Work: {self.stats['work_count']}", True, self.text_color)
        self.surface.blit(work_text, (20, y_offset))
        y_offset += 30
        
        # Resources chart label
        res_chart_title = self.label_font.render("Resource Trends (Last 100 Steps)", True, self.text_color)
        self.surface.blit(res_chart_title, (10, y_offset))
        y_offset += 20
        
        # Resources chart
        self.surface.blit(self.charts['resources'].surface, (10, y_offset))
        y_offset += 90
        
        # Agent averages section
        if self.stats['population'] > 0:
            avg_title = self.label_font.render("Population Averages", True, self.text_color)
            self.surface.blit(avg_title, (10, y_offset))
            y_offset += 25
            
            avg_age = self.value_font.render(f"Age: {self.stats['avg_age']:.1f}", True, self.text_color)
            self.surface.blit(avg_age, (20, y_offset))
            y_offset += 20
            
            avg_energy = self.value_font.render(f"Energy: {self.stats['avg_energy']:.1f}", True, self.text_color)
            self.surface.blit(avg_energy, (20, y_offset))
            y_offset += 20
            
            avg_money = self.value_font.render(f"Money: {self.stats['avg_money']:.1f}", True, self.text_color)
            self.surface.blit(avg_money, (20, y_offset))
        
        # Blit the panel surface to the screen
        self.screen.blit(self.surface, self.rect)
