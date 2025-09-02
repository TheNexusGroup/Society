from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class WorkplaceComponent:
    entity_id: int
    
    # Staffing
    workers: List[int] = field(default_factory=list)
    max_workers: int = 5
    wages: Dict[int, float] = field(default_factory=dict)
    base_wage: float = 10.0
    
    # Inventory
    inventory: int = 0
    max_inventory: int = 100
    
    # Economic properties
    capital: float = 1000.0
    min_operating_capital: float = 100.0
    price: float = 25.0
    revenue: float = 0.0
    profit: float = 0.0
    expenses: float = 0.0
    operating_costs: float = 5.0
    
    # Customer handling
    customer_queue: List[int] = field(default_factory=list)
    
    # Investors
    investors: List[Dict[str, Any]] = field(default_factory=list)
    
    # Status flags
    has_staff: bool = False
    has_stock: bool = False
    is_funded: bool = True
    is_profitable: bool = False
    
    def add_worker(self, worker_id: int, wage: float = None):
        if len(self.workers) < self.max_workers:
            self.workers.append(worker_id)
            self.wages[worker_id] = wage or self.base_wage
            self.has_staff = True
            return True
        return False
    
    def remove_worker(self, worker_id: int):
        if worker_id in self.workers:
            self.workers.remove(worker_id)
            if worker_id in self.wages:
                del self.wages[worker_id]
            self.has_staff = len(self.workers) > 0
            return True
        return False
    
    def add_inventory(self, amount: int):
        space_left = self.max_inventory - self.inventory
        added = min(amount, space_left)
        self.inventory += added
        self.has_stock = self.inventory > 0
        return added
    
    def remove_inventory(self, amount: int):
        removed = min(amount, self.inventory)
        self.inventory -= removed
        self.has_stock = self.inventory > 0
        return removed
    
    def add_customer(self, customer_id: int):
        if customer_id not in self.customer_queue:
            self.customer_queue.append(customer_id)
            return True
        return False
    
    def process_next_customer(self):
        if self.customer_queue and self.has_stock:
            customer_id = self.customer_queue.pop(0)
            self.inventory -= 1
            self.has_stock = self.inventory > 0
            self.revenue += self.price
            return customer_id, self.price
        return None, 0
    
    def update_status(self):
        self.has_staff = len(self.workers) > 0
        self.has_stock = self.inventory > 0
        self.is_funded = self.capital > self.min_operating_capital
        
    def calculate_profit(self):
        self.expenses = sum(self.wages.values()) + self.operating_costs
        self.profit = self.revenue - self.expenses
        self.is_profitable = self.profit > 0
        return self.profit
