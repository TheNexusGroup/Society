import pygame
import math
from typing import List, Tuple

class LineChart:
    def __init__(self, width, height, labels=None, colors=None):
        self.width = width
        self.height = height
        self.labels = labels or ["Data"]
        self.colors = colors or [(0, 120, 255), (255, 100, 0), (0, 200, 0), (200, 0, 200)]
        self.max_value = 10  # Will be adjusted dynamically
        
        self.surface = pygame.Surface((width, height))
        self.background_color = (40, 40, 50)
        self.axis_color = (150, 150, 150)
        self.grid_color = (70, 70, 80)
        
    def update(self, data_series):
        """Update chart with new data series"""
        # Clear surface
        self.surface.fill(self.background_color)
        
        # Find max value for scaling
        max_val = 10
        for series in data_series:
            if series and max(series) > max_val:
                max_val = max(series)
        
        # Add 10% headroom
        self.max_value = max_val * 1.1 if max_val > 0 else 10
        
        # Draw grid
        self._draw_grid()
        
        # Draw each data series
        for i, series in enumerate(data_series):
            if not series:
                continue
                
            color = self.colors[i % len(self.colors)]
            self._draw_line(series, color)
            
    def _draw_grid(self):
        """Draw background grid and axes"""
        # Draw axes
        pygame.draw.line(self.surface, self.axis_color, 
                        (0, self.height-1), (self.width, self.height-1), 1)  # X-axis
        pygame.draw.line(self.surface, self.axis_color, 
                        (0, 0), (0, self.height), 1)  # Y-axis
        
        # Draw horizontal grid lines
        for i in range(4):
            y = self.height - 1 - (i + 1) * self.height // 5
            pygame.draw.line(self.surface, self.grid_color, 
                            (0, y), (self.width, y), 1)
            
        # Draw vertical grid lines
        for i in range(1, 10):
            x = i * self.width // 10
            pygame.draw.line(self.surface, self.grid_color, 
                            (x, 0), (x, self.height), 1)
            
    def _draw_line(self, data, color):
        """Draw a line series on the chart"""
        if not data:
            return
            
        # If not enough data points, pad with zeros
        points = []
        
        # Calculate points
        for i, value in enumerate(data):
            x = i * self.width // max(len(data) - 1, 1) if len(data) > 1 else self.width // 2
            y = self.height - int((value / self.max_value) * self.height)
            points.append((x, y))
            
        # Draw line connecting points
        if len(points) > 1:
            pygame.draw.lines(self.surface, color, False, points, 2)
            
        # Draw points
        for point in points:
            pygame.draw.circle(self.surface, color, point, 3)

class BarChart:
    def __init__(self, width, height, labels=None, colors=None):
        self.width = width
        self.height = height
        self.labels = labels or ["Data"]
        self.colors = colors or [(0, 120, 255), (255, 100, 0), (0, 200, 0), (200, 0, 200)]
        self.max_value = 10  # Will be adjusted dynamically
        
        self.surface = pygame.Surface((width, height))
        self.background_color = (40, 40, 50)
        self.axis_color = (150, 150, 150)
        self.grid_color = (70, 70, 80)
        
    def update(self, data_series):
        """Update chart with new data series"""
        # Clear surface
        self.surface.fill(self.background_color)
        
        # Find max value for scaling
        max_val = 10
        for series in data_series:
            if series and max(series) > max_val:
                max_val = max(series)
        
        # Add 10% headroom
        self.max_value = max_val * 1.1 if max_val > 0 else 10
        
        # Draw grid
        self._draw_grid()
        
        # Draw each data series
        for i, series in enumerate(data_series):
            if not series:
                continue
                
            color = self.colors[i % len(self.colors)]
            self._draw_bars(series, color, i, len(data_series))
            
    def _draw_grid(self):
        """Draw background grid and axes"""
        # Draw axes
        pygame.draw.line(self.surface, self.axis_color, 
                        (0, self.height-1), (self.width, self.height-1), 1)  # X-axis
        pygame.draw.line(self.surface, self.axis_color, 
                        (0, 0), (0, self.height), 1)  # Y-axis
        
        # Draw horizontal grid lines
        for i in range(4):
            y = self.height - 1 - (i + 1) * self.height // 5
            pygame.draw.line(self.surface, self.grid_color, 
                            (0, y), (self.width, y), 1)
            
    def _draw_bars(self, data, color, series_idx, total_series):
        """Draw a bar series on the chart"""
        if not data:
            return
            
        bar_width = self.width // (len(data) * total_series + 1)
        
        # Draw bars
        for i, value in enumerate(data):
            bar_height = int((value / self.max_value) * (self.height - 5))
            x = i * (bar_width * total_series + 2) + series_idx * bar_width + 2
            y = self.height - bar_height
            pygame.draw.rect(self.surface, color, (x, y, bar_width, bar_height))

class PieChart:
    def __init__(self, width, height, colors=None):
        self.width = max(width, height)  # Make it square by using max dimension
        self.height = self.width
        self.radius = min(self.width, self.height) // 2 - 10
        self.center = (self.width // 2, self.height // 2)
        
        self.colors = colors or [
            (255, 100, 100), (100, 100, 255), (100, 255, 100), 
            (255, 255, 100), (255, 100, 255), (100, 255, 255)
        ]
        
        self.surface = pygame.Surface((self.width, self.height))
        self.background_color = (40, 40, 50)
        
        # Default to empty
        self.slices = []
        self.values = []
        self.total = 0
        
    def update(self, labels, values):
        """Update chart with new values"""
        self.surface.fill(self.background_color)
        
        self.labels = labels
        self.values = values
        self.total = sum(values) if values else 1  # Avoid division by zero
        
        # Draw chart
        self._draw_segments()
        self._draw_legend()
        
    def _draw_segments(self):
        """Draw the pie chart slices"""
        if not self.values or self.total == 0:
            # Draw empty circle
            pygame.draw.circle(self.surface, (100, 100, 100), self.center, self.radius, 1)
            return
            
        start_angle = 0
        
        for i, value in enumerate(self.values):
            # Calculate slice angles
            angle = 360 * (value / self.total)
            end_angle = start_angle + angle
            
            # Draw slice
            self._draw_slice(start_angle, end_angle, self.colors[i % len(self.colors)])
            
            start_angle = end_angle
    
    def _draw_slice(self, start_angle, end_angle, color):
        """Draw a pie slice"""
        start_rad = math.radians(start_angle)
        end_rad = math.radians(end_angle)
        
        points = [self.center]
        
        # Add start point on arc
        x = self.center[0] + int(self.radius * math.cos(start_rad))
        y = self.center[1] - int(self.radius * math.sin(start_rad))
        points.append((x, y))
        
        # Add points along the arc
        steps = max(1, int((end_angle - start_angle) / 5))
        for i in range(1, steps + 1):
            angle = start_rad + (end_rad - start_rad) * i / steps
            x = self.center[0] + int(self.radius * math.cos(angle))
            y = self.center[1] - int(self.radius * math.sin(angle))
            points.append((x, y))
        
        # Draw polygon
        pygame.draw.polygon(self.surface, color, points)
        
        # Draw outline
        pygame.draw.line(self.surface, (0, 0, 0), self.center, points[1], 1)
        pygame.draw.line(self.surface, (0, 0, 0), self.center, points[-1], 1)
        pygame.draw.arc(self.surface, (0, 0, 0), 
                      (self.center[0] - self.radius, self.center[1] - self.radius,
                       self.radius * 2, self.radius * 2),
                      start_rad, end_rad, 1)
    
    def _draw_legend(self):
        """Draw chart legend"""
        if not self.labels or not self.values:
            return
            
        font = pygame.font.SysFont('Arial', 12)
        y_offset = self.height - 10 - (len(self.labels) * 15)
        
        for i, label in enumerate(self.labels):
            # Draw color box
            color_rect = pygame.Rect(5, y_offset, 10, 10)
            pygame.draw.rect(self.surface, self.colors[i % len(self.colors)], color_rect)
            pygame.draw.rect(self.surface, (0, 0, 0), color_rect, 1)
            
            # Draw label
            value_percent = (self.values[i] / self.total * 100) if self.total else 0
            text = f"{label}: {value_percent:.1f}%"
            text_surface = font.render(text, True, (200, 200, 200))
            self.surface.blit(text_surface, (20, y_offset))
            
            y_offset += 15
