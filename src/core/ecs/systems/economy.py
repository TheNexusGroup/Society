import random
from ..system import System
from ..components.investor import InvestorComponent
from ..components.wallet import WalletComponent

class EconomicSystem(System):
    def __init__(self, world):
        super().__init__(world, update_frequency=2)  # Update every 2nd frame for performance
        self.world = world
        
    def update(self, delta_time):
        """Process all workplace-related economic activities each frame."""
        self.process_workplaces(delta_time)
        self.process_workers(delta_time)
        self.process_customers(delta_time)
        self.process_investors(delta_time)
        
    def process_workplaces(self, delta_time):
        """Update workplace states and process economic activities."""
        workplace_entities = self.world.ecs.get_entities_with_components(["workplace", "transform"])
        
        for entity_id in workplace_entities:
            workplace = self.world.ecs.get_component(entity_id, "workplace")
            if workplace:
                # Update workplace status indicators
                self.update_workplace_status(entity_id, workplace)
                
                # Process sales and revenue
                if workplace.has_stock and workplace.has_staff:
                    self.process_sales(entity_id, workplace, delta_time)
                    
                # Update profits and pay investors
                self.calculate_profits(entity_id, workplace)
    
    def process_workers(self, delta_time):
        """Process worker activities at workplaces with potential for misconduct"""
        worker_entities = self.world.ecs.get_entities_with_components(["tag", "wallet"])
        
        for entity_id in worker_entities:
            tag = self.world.ecs.get_component(entity_id, "tag")
            if tag and tag.tag == "agent":
                behavior = self.world.ecs.get_component(entity_id, "behavior")
                if behavior and behavior.state == "work" and hasattr(behavior.properties, "workplace_id"):
                    workplace_id = behavior.properties.workplace_id
                    workplace = self.world.ecs.get_component(workplace_id, "workplace")
                    
                    if workplace:
                        # Check for potential workplace misconduct
                        should_commit_misconduct = False
                        
                        # Get agent entity
                        agent = self.world.get_entity_by_id(entity_id)
                        
                        if hasattr(agent, 'genome') and agent.genome.agreeableness < 0.3:
                            # Low agreeableness increases chance of misconduct
                            misconduct_chance = (0.3 - agent.genome.agreeableness) * 0.5
                            should_commit_misconduct = random.random() < misconduct_chance
                        
                        if should_commit_misconduct:
                            # Determine misconduct type and impact
                            misconduct_type = random.choice(['theft', 'sabotage'])
                            damage_amount = random.uniform(5, 20)
                            
                            # Apply effects to workplace
                            if misconduct_type == 'theft':
                                # Worker steals money
                                stolen_amount = min(damage_amount, workplace.capital)
                                workplace.capital -= stolen_amount
                                
                                # Add money to agent
                                wallet = self.world.ecs.get_component(entity_id, "wallet")
                                if wallet:
                                    wallet.money += stolen_amount
                            elif misconduct_type == 'sabotage':
                                # Worker damages workplace productivity
                                workplace.operating_costs += damage_amount
                            
                            # Register misconduct in social system
                            social_system = self.world.ecs.get_system("social")
                            if social_system:
                                social_system.register_workplace_misconduct(
                                    entity_id, workplace_id, 
                                    misconduct_type, damage_amount
                                )
                            
                            # Record misconduct in worker's brain
                            if hasattr(agent, 'brain') and agent.brain:
                                importance = 0.6
                                memory_details = {
                                    'workplace_id': workplace_id,
                                    'misconduct_type': misconduct_type,
                                    'damage_amount': damage_amount
                                }
                                agent.brain.memory.add_memory('committed_workplace_misconduct', 
                                                             memory_details, importance)
                        
                        # Continue with normal worker processing
                        self.pay_worker(entity_id, workplace, delta_time)
    
    def process_customers(self, delta_time):
        """Process customer queue at workplaces."""
        agent_entities = self.world.ecs.get_entities_with_components(["tag", "behavior"])
        
        for entity_id in agent_entities:
            tag = self.world.ecs.get_component(entity_id, "tag")
            behavior = self.world.ecs.get_component(entity_id, "behavior")
            
            if tag and tag.tag == "agent" and behavior and hasattr(behavior.properties, "shopping_target"):
                shopping_target = behavior.properties.shopping_target
                if shopping_target:
                    workplace = self.world.ecs.get_component(shopping_target, "workplace")
                    if workplace and workplace.has_stock:
                        self.process_purchase(entity_id, workplace)
    
    def process_investors(self, delta_time):
        """Process investment returns for investors."""
        investor_entities = self.world.ecs.get_entities_with_components(["investor", "wallet"])
        
        for entity_id in investor_entities:
            investor = self.world.ecs.get_component(entity_id, "investor")
            wallet = self.world.ecs.get_component(entity_id, "wallet")
            
            if investor and wallet:
                for investment in investor.investments:
                    workplace_id = investment["workplace_id"]
                    workplace = self.world.ecs.get_component(workplace_id, "workplace")
                    
                    if workplace and workplace.is_profitable:
                        # Calculate return based on profit and investment share
                        return_amount = workplace.profit * investment["return_rate"]
                        
                        # Pay investor
                        wallet.money += return_amount
                        
                        # Update investment record
                        investment["return_amount"] = return_amount
    
    def update_workplace_status(self, entity_id, workplace):
        """Update visual status of workplace based on its economic state."""
        workplace.has_staff = len(workplace.workers) > 0
        workplace.has_stock = workplace.inventory > 0
        workplace.is_funded = workplace.capital > workplace.min_operating_capital
        
        # Update render component based on status
        render = self.world.ecs.get_component(entity_id, "render")
        if render:
            if not workplace.has_stock:
                render.current_state = "out-of-stock"
            elif not workplace.is_funded:
                render.current_state = "broke"
            else:
                render.current_state = "default"

    def process_sales(self, entity_id, workplace, delta_time):
        """Process sales for a workplace."""
        # Calculate sales based on customer queue, price, and available inventory
        potential_sales = min(len(workplace.customer_queue), workplace.inventory)
        actual_sales = 0
        
        for i in range(potential_sales):
            customer_id = workplace.customer_queue[i]
            wallet = self.world.ecs.get_component(customer_id, "wallet")
            
            if wallet and wallet.money >= workplace.price:
                actual_sales += 1
                wallet.money -= workplace.price
                workplace.revenue += workplace.price
                
        # Update inventory after sales
        workplace.inventory -= actual_sales
        # Remove customers who made purchases
        workplace.customer_queue = workplace.customer_queue[actual_sales:]
    
    def calculate_profits(self, entity_id, workplace):
        """Calculate profits and distribute to investors."""
        workplace.expenses = sum(workplace.wages.values()) + workplace.operating_costs
        workplace.profit = workplace.revenue - workplace.expenses
        workplace.is_profitable = workplace.profit > 0
    
    def pay_worker(self, worker_id, workplace, delta_time):
        """Pay wages to a worker."""
        if workplace.is_funded:
            hours_worked = delta_time / 3600  # Convert delta_time to hours
            wage_rate = workplace.wages.get(worker_id, workplace.base_wage)
            earned_wages = wage_rate * hours_worked
            
            wallet = self.world.ecs.get_component(worker_id, "wallet")
            if wallet:
                wallet.money += earned_wages
                workplace.expenses += earned_wages
    
    def process_purchase(self, customer_id, workplace):
        """Process a purchase from a customer."""
        if customer_id not in workplace.customer_queue:
            workplace.customer_queue.append(customer_id)
    
    def invest_in_workplace(self, investor_id, workplace_id, amount, expected_return_rate):
        """Allow individuals to invest in a workplace."""
        wallet = self.world.ecs.get_component(investor_id, "wallet")
        workplace = self.world.ecs.get_component(workplace_id, "workplace")
        
        if wallet and workplace and wallet.money >= amount:
            # Create investor component if it doesn't exist
            investor = self.world.ecs.get_component(investor_id, "investor")
            if not investor:
                investor = InvestorComponent(investor_id)
                self.world.ecs.add_component(investor_id, "investor", investor)
            
            # Add investment to investor's portfolio
            investor.add_investment(workplace_id, amount, expected_return_rate)
            
            # Update investor and workplace
            wallet.money -= amount
            workplace.capital += amount
            
            return True
        return False