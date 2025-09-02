from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class InvestorComponent:
    entity_id: int
    investments: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_investment(self, workplace_id: int, amount: float, return_rate: float):
        self.investments.append({
            "workplace_id": workplace_id,
            "amount": amount,
            "return_rate": return_rate,
            "return_amount": 0
        })
    
    def remove_investment(self, workplace_id: int):
        self.investments = [inv for inv in self.investments if inv["workplace_id"] != workplace_id]
    
    def update_returns(self, workplace_id: int, return_amount: float):
        for investment in self.investments:
            if investment["workplace_id"] == workplace_id:
                investment["return_amount"] = return_amount
                return True
        return False
