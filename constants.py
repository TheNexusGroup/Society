from enum import Enum
from typing import Dict, Any

class EntityType(Enum):
    PERSON_MALE = "male"
    PERSON_FEMALE = "female" 
    WORK = "work"
    FARM = "farm"

    def __str__(self):
        return self.value
    

asset_map = {
    EntityType.PERSON_MALE: {
        "name": "male", 
        "path": "assets/male.png",
        "dead": "assets/male_dead.png",
        "eat": "assets/male_hungry.png",
        "work": "assets/male_broke.png",
        "mate": "assets/male_love.png",
        "search": "assets/male_search.png",
        "rest": "assets/male_rest.png",
        "farm": "assets/male_farm.png",
        "harvest": "assets/male_harvest.png",
        },
    EntityType.PERSON_FEMALE: {
        "name": "female", 
        "path": "assets/female.png", 
        "dead": "assets/female_dead.png",
        "eat": "assets/female_hungry.png",
        "work": "assets/female_broke.png",
        "mate": "assets/female_love.png",
        "rest": "assets/female_rest.png",
        "search": "assets/female_search.png",
        "farm": "assets/female_farm.png",
        "harvest": "assets/female_harvest.png",
        },
    EntityType.WORK: {
        "name": "work", "path": "assets/work.png",
        "out-of-stock": "assets/work_out-of-stock.png",
        "broke": "assets/work_broke.png",
        "understaffed": "assets/work.png",
        "closed": "assets/work.png",
        },
    EntityType.FARM: {
        "name": "farm", "path": "assets/farm.png", 
        "sewed": "assets/farm_sewed.png", 
        "yield": "assets/farm_yield.png"}
}

additional_assets = {
    EntityType.PERSON_MALE: {"name": "mate", "path": "assets/hearts_{}.png", "count": 3},
    EntityType.PERSON_FEMALE: {"name": "mate", "path": "assets/hearts_{}.png", "count": 3},
    EntityType.WORK: {"name": "working", "path": "assets/working_{}.png", "count": 3},
}

class Gender(Enum):
    MALE = "male"
    FEMALE = "female"

class FarmState(Enum):
    TILTH = "tilth"
    SEWED = "sewed"
    YIELD = "yield"

class WorkplaceState(Enum):
    OPERATIONAL = "operational"     # Defaults to working animation
    BUSY = "busy"                   # Defaults to working animation - TODO: Add busy animation
    CLOSED = "closed"               # Defaults to normal path state
    UNDERSTAFFED = "understaffed"   # Defaults to normal path state
    OUT_OF_STOCK = "out-of-stock"   # Defaults to out-of-stock path state
    BROKE = "broke"                 # Defaults to broke path state

workplace_state_map = {
    # has_staff, has_stock, is_funded -> WorkplaceState
    (True, True, True): WorkplaceState.OPERATIONAL,
    (False, True, True): WorkplaceState.UNDERSTAFFED,
    (False, True, False): WorkplaceState.UNDERSTAFFED,
    (True, False, True): WorkplaceState.OUT_OF_STOCK,
    (False, False, True): WorkplaceState.OUT_OF_STOCK,
    (True, True, False): WorkplaceState.BROKE,
    (True, False, False): WorkplaceState.BROKE,
    (False, False, False): WorkplaceState.CLOSED
}

class ActionType(Enum):
    REST = "rest"                                   # Personal
    SEARCH = "search"                               # Personal
    EAT = "eat"                                     # Person with Food
    MATE = "mate"                                   # Person to Person    
    PLANT_FOOD = "plant-food"                       # Person to Farm
    HARVEST_FOOD = "harvest-food"                   # Person to Farm
    GIFT_FOOD = "gift-food"                         # Person to Person        
    GIFT_MONEY = "gift-money"                       # Person to Person
    WORK = "work"                                   # Person to Workplace
    INVEST = "invest"                               # Person to Workplace
    BUY_FOOD = "buy-food"                           # Person to Workplace 
    SELL_FOOD = "sell-food"                         # Person to Workplace   
    TRADE_FOOD_FOR_MONEY = "trade-food-for-money"   # Person to Person
    TRADE_MONEY_FOR_FOOD = "trade-money-for-food"   # Person to Person

class ResourceType(Enum):
    FOOD = "food"
    MONEY = "money"
    ENERGY = "energy"
    WORK = "work"
    FARM = "farm"
    INVESTMENT = "investment"