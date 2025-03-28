import random

class EconomicSystem:
    def __init__(self, world):
        self.world = world
        
    def update(self, delta_time):
        """Process all workplace-related economic activities each frame."""
        self.process_workplaces(delta_time)
        self.process_workers(delta_time)
        self.process_customers(delta_time)
        self.process_investors(delta_time)
        
    def process_workplaces(self, delta_time):
        """Update workplace states and process economic activities."""
        workplaces = self.world.get_components_of_type("Workplace")
        for entity_id, workplace in workplaces:
            # Update workplace status indicators
            self.update_workplace_status(entity_id, workplace)
            
            # Process sales and revenue
            if workplace.has_stock and workplace.has_staff:
                self.process_sales(entity_id, workplace, delta_time)
                
            # Update profits and pay investors
            self.calculate_profits(entity_id, workplace)
    
    def process_workers(self, delta_time):
        """Process worker activities at workplaces with potential for misconduct"""
        workers = self.world.get_components_of_type("Worker")
        for entity_id, worker in workers:
            if worker.is_working and worker.workplace_id:
                workplace = self.world.get_component(worker.workplace_id, "Workplace")
                if workplace:
                    # Check for potential workplace misconduct
                    should_commit_misconduct = False
                    
                    # Get social component to check personality traits
                    agent = self.world.get_entity_by_id(entity_id)
                    social = self.world.ecs.get_component(entity_id, "social")
                    
                    if social and social.agreeableness < 0.3:
                        # Low agreeableness increases chance of misconduct
                        misconduct_chance = (0.3 - social.agreeableness) * 0.5
                        should_commit_misconduct = random.random() < misconduct_chance
                    
                    if should_commit_misconduct:
                        # Determine misconduct type and impact
                        misconduct_type = random.choice(['theft', 'sabotage'])
                        damage_amount = random.uniform(5, 20)
                        
                        # Apply effects to workplace
                        if misconduct_type == 'theft':
                            # Worker steals money
                            stolen_amount = min(damage_amount, workplace.funds)
                            workplace.funds -= stolen_amount
                            agent.money += stolen_amount
                        elif misconduct_type == 'sabotage':
                            # Worker damages workplace productivity
                            workplace.productivity *= max(0.5, 1.0 - (damage_amount / 100.0))
                        
                        # Register misconduct in social system
                        social_system = self.world.ecs.get_system("social")
                        if social_system:
                            social_system.register_workplace_misconduct(
                                entity_id, worker.workplace_id, 
                                misconduct_type, damage_amount
                            )
                        
                        # Record misconduct in worker's brain
                        if hasattr(agent, 'brain') and agent.brain:
                            importance = 0.6
                            memory_details = {
                                'workplace_id': worker.workplace_id,
                                'misconduct_type': misconduct_type,
                                'damage_amount': damage_amount
                            }
                            agent.brain.memory.add_memory('committed_workplace_misconduct', 
                                                         memory_details, importance)
                        
                        # Short-term reward for misconduct
                        # This reinforces the behavior in Q-learning but will have social consequences
                        reward = damage_amount / 10.0  # Immediate reward
                        
                        # Update agent's Q-learning
                        if hasattr(agent, 'brain') and agent.brain:
                            state = agent.get_state_representation()
                            next_state = state  # Assuming state doesn't change immediately
                            agent.brain.update_q_value(state, 'work', reward, next_state)
                    
                    # Continue with normal worker processing
                    self.pay_worker(entity_id, worker, workplace, delta_time)
    
    def process_customers(self, delta_time):
        """Process customer queue at workplaces."""
        agents = self.world.get_components_of_type("Agent")
        for entity_id, agent in agents:
            if agent.shopping_target:
                workplace = self.world.get_component(agent.shopping_target, "Workplace")
                if workplace and workplace.has_stock:
                    self.process_purchase(entity_id, agent, workplace)
    
    def process_investors(self, delta_time):
        """Process investment returns for investors."""
        investors = self.world.get_components_of_type("Investor")
        for entity_id, investor in investors:
            for investment in investor.investments:
                workplace = self.world.get_component(investment.workplace_id, "Workplace")
                if workplace and workplace.is_profitable:
                    self.pay_investor(entity_id, investor, workplace, investment)
    
    def update_workplace_status(self, entity_id, workplace):
        """Update visual status of workplace based on its economic state."""
        workplace.has_staff = len(workplace.workers) > 0
        workplace.has_stock = workplace.inventory > 0
        workplace.is_funded = workplace.capital > workplace.min_operating_capital
        
        # Update animation states based on status
        animation = self.world.get_component(entity_id, "Animation")
        if animation:
            if workplace.has_staff:
                animation.current_state = "working"
            else:
                animation.current_state = None
        else:
            # Set the asset to the appropriate state
            asset = self.world.get_component(entity_id, "Asset")
            if asset:
                if not workplace.has_stock:
                    asset.current_state = "out-of-stock"
                elif not workplace.is_funded:
                    asset.current_state = "broke"

    def process_sales(self, entity_id, workplace, delta_time):
        """Process sales for a workplace."""
        # Calculate sales based on customer queue, price, and available inventory
        potential_sales = min(len(workplace.customer_queue), workplace.inventory)
        actual_sales = 0
        
        for i in range(potential_sales):
            customer_id = workplace.customer_queue[i]
            customer = self.world.get_component(customer_id, "Agent")
            wallet = self.world.get_component(customer_id, "Wallet")
            
            if customer and wallet and wallet.money >= workplace.price:
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
        
        # Distribute profits to investors based on investment share
        if workplace.is_profitable and workplace.investors:
            total_investment = sum(inv.amount for inv in workplace.investors)
            for investor in workplace.investors:
                share = investor.amount / total_investment
                investor.return_amount = workplace.profit * share * investor.return_rate
    
    def pay_worker(self, entity_id, worker, workplace, delta_time):
        """Pay wages to a worker."""
        if workplace.is_funded:
            hours_worked = delta_time / 3600  # Convert delta_time to hours
            wage_rate = workplace.wages.get(entity_id, workplace.base_wage)
            earned_wages = wage_rate * hours_worked
            
            wallet = self.world.get_component(entity_id, "Wallet")
            if wallet:
                wallet.money += earned_wages
                workplace.expenses += earned_wages
    
    def process_purchase(self, entity_id, agent, workplace):
        """Process a purchase from a customer."""
        if entity_id not in workplace.customer_queue:
            workplace.customer_queue.append(entity_id)
    
    def pay_investor(self, entity_id, investor, workplace, investment):
        """Pay returns to an investor."""
        wallet = self.world.get_component(entity_id, "Wallet")
        if wallet and investment.return_amount > 0:
            wallet.money += investment.return_amount
            workplace.profit -= investment.return_amount
    
    def sell_to_workplace(self, seller_id, workplace_id, item_type, quantity, price_per_unit):
        """Allow individuals to sell goods to a workplace."""
        seller_inventory = self.world.get_component(seller_id, "Inventory")
        seller_wallet = self.world.get_component(seller_id, "Wallet")
        workplace = self.world.get_component(workplace_id, "Workplace")
        
        if seller_inventory and seller_wallet and workplace:
            if seller_inventory.get_item_count(item_type) >= quantity and workplace.capital >= price_per_unit * quantity:
                # Execute the transaction
                total_price = price_per_unit * quantity
                
                seller_inventory.remove_items(item_type, quantity)
                seller_wallet.money += total_price
                
                workplace.inventory += quantity
                workplace.capital -= total_price
                
                return True
        return False
    
    def invest_in_workplace(self, investor_id, workplace_id, amount, expected_return_rate):
        """Allow individuals to invest in a workplace."""
        investor_wallet = self.world.get_component(investor_id, "Wallet")
        workplace = self.world.get_component(workplace_id, "Workplace")
        
        if investor_wallet and workplace and investor_wallet.money >= amount:
            # Create new investment
            investment = {
                "investor_id": investor_id,
                "amount": amount,
                "return_rate": expected_return_rate,
                "return_amount": 0
            }
            
            # Update investor and workplace
            investor_wallet.money -= amount
            workplace.capital += amount
            workplace.investors.append(investment)
            
            # Add investor component if it doesn't exist
            if not self.world.has_component(investor_id, "Investor"):
                self.world.add_component(investor_id, "Investor", {"investments": []})
            
            investor_component = self.world.get_component(investor_id, "Investor")
            investor_component.investments.append({
                "workplace_id": workplace_id,
                "amount": amount,
                "return_rate": expected_return_rate
            })
            
            return True
        return False