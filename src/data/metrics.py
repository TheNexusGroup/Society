# Metrics should be used to track the performance of the simulation over a period of time

import time
from typing import Dict, List, Any
import csv
import os
import json

class MetricsCollector:
    def __init__(self, sampling_interval=10):
        self.sampling_interval = sampling_interval
        self.step_counter = 0
        self.metrics = {
            # Population metrics
            'population_size': [],
            'male_count': [],
            'female_count': [],
            'birth_count': [],
            'death_count': [],
            'working_count': [],
            'investor_count': [],
            'farmer_count': [],
            'thief_count': [],
            'total_food_yield': [],
            'epoch': [],
            
            # Resource metrics
            'food_count': [],
            'work_count': [],
            
            # Agent metrics
            'avg_age': [],
            'avg_energy': [],
            'avg_money': [],
            'avg_mood': [],
            'min_age': [],
            'max_age': [],
            'median_age': [],
            'min_money': [],
            'max_money': [],
            'median_money': [],
            'min_energy': [],
            'max_energy': [],
            'median_energy': [],
            
            # Farm metrics
            'farm_count': [],
            'avg_farm_yield': [],
            'min_farm_yield': [],
            'max_farm_yield': [],
            'total_farmland': [],
            'unused_farmland': [],
            
            # Work metrics
            'employment_rate': [],
            'avg_productivity': [],
            'total_wages_paid': [],
            'job_vacancies': [],
            
            # Society metrics
            'wealth_gini': [],
            'crime_rate': [],
            'social_mobility': [],
            'starving_count': [],
            
            # Action distribution
            'action_eat': [],
            'action_work': [],
            'action_rest': [],
            'action_mate': [],
            'action_search': [],
            'action_plant_food': [],
            'action_harvest_food': [],
            'action_gift_food': [],
            'action_gift_money': [],
            'action_invest': [],
            'action_buy_food': [],
            'action_sell_food': [],
            'action_trade_food_for_money': [],
            'action_trade_money_for_food': [],
            
            # System metrics
            'timestamp': [],
            'steps_per_second': []
        }
        self.last_collection_time = time.time()
        self.last_sample_step = 0
    
    def collect(self, metrics_dict):
        """Collect metrics directly from a dictionary of values"""
        self.step_counter += 1
        
        # Only sample at defined intervals
        if self.step_counter % self.sampling_interval != 0:
            return
            
        current_time = time.time()
        steps_per_second = (self.step_counter - self.last_sample_step) / (current_time - self.last_collection_time) if (current_time - self.last_collection_time) > 0 else 0
        
        # Store each metric from the dictionary
        for key, value in metrics_dict.items():
            if key in self.metrics:
                self.metrics[key].append(value)
        
        # System metrics
        self.metrics['timestamp'].append(current_time)
        self.metrics['steps_per_second'].append(steps_per_second)
        
        # Update collection time
        self.last_collection_time = current_time
        self.last_sample_step = self.step_counter
    
    def get_latest(self, metric_name):
        """Get the most recent value for a given metric"""
        if metric_name in self.metrics and self.metrics[metric_name]:
            return self.metrics[metric_name][-1]
        return 0
    
    def get_series(self, metric_name, limit=None):
        """Get a time series for a given metric, optionally limited to last N samples"""
        if metric_name not in self.metrics:
            return []
            
        series = self.metrics[metric_name]
        if limit and len(series) > limit:
            return series[-limit:]
        return series
    
    def export_csv(self, filename="simulation_metrics.csv"):
        """Export metrics to CSV file"""
        directory = "metrics"
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, filename)
        
        # Get all metrics with same length (in case of inconsistencies)
        min_length = min(len(series) for series in self.metrics.values())
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow(self.metrics.keys())
            # Write rows
            for i in range(min_length):
                writer.writerow([series[i] for series in self.metrics.values()])
        
        return filepath