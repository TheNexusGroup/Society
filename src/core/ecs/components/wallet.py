from dataclasses import dataclass

@dataclass
class WalletComponent:
    entity_id: int
    money: float = 0.0
    
    def add_money(self, amount: float):
        self.money += amount
        return self.money
    
    def remove_money(self, amount: float):
        if self.money >= amount:
            self.money -= amount
            return True
        return False
    
    def can_afford(self, amount: float):
        return self.money >= amount
