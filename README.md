# Population Simulation Design Document

## Overview
A society simulator using reinforcement learning and genetic algorithms where agents balance survival needs while having free agency to reproduce and evolve over generations.

## Agent Properties

Genome:
[Gender, Metabolism, Stamina, Learning Capacity, Attraction Profile, ..Q-learning table Values]

- **Basic Attributes**:
  - Gender: Male/Female
  - Age - Determines lifetime
  - Energy - Determines the ability to do actions or die
  - Money - Determines the ability to buy food, and affects mating (or potentially requires working for it) - can be potentially inherited at a cost
  - Mood: Happiness (1) to Stress (-1)
  - Generation - Determines the generation number of the agent
  - Offspring_Generations - Determines the number of generations the agent has had offspring
  - Offspring_Count - Determines the number of offspring the agent has had

- **Derived Inherited Attributes**:
  - Metabolic rate - Determines the rate at which energy is consumed (factor of mating, higher metabolic means more food is required, but work is more effective)
  - Stamina - Determines the ability to do actions or die (factor of mating, higher stamina means energy consumption is less of a factor, but can work longer)
  - Learning capacity - Determines Learning Rate in Q-learning (factor of mating)
  - Attraction profile - Determines the threshold for seeking a similar mate or higher trait mate (-1 - 1 : -1 = lower threshold, 1 = higher threshold)

- **Derived Non-Inherited Attributes**:
  - Generation - Determines the generation number of the agent
  - Offspring_Generations - Determines the number of generations the agent has had offspring
  - Offspring_Count - Determines the number of offspring the agent has had

## Actions
- Eat (consumes food, and generates energy)
- Work (generates money, consumes energy)
- Rest (regenerates a small amount of energy, consumes time)
- Mate (affects mood, requires partner, energy and attraction profile)
- Search (for food, work, or potential mates)

## Resource Dynamics
- Food requires money to obtain, provides energy
- Work requires energy expenditure, generates money
- Potential for agents to accumulate enough money to create businesses
- Emergent economic structures without explicit instruction

## Learning Mechanism
- Q-learning table encoded in agent's genome
- States: combinations of energy/money/mood levels and food/work/mate/rest/empty availability
- Actions: eat/work/rest/mate/search
- Rewards: survival, reproduction success, generational growth

## Reproduction
- Requires male and female agents
- Success probability based on agent attributes
- Attraction based on:
  - Similar trait profiles (with standard deviation)
  - Complementary genetic traits
- Offspring inherits genetic material from both parents
- Children consume resources until maturity

## Genetic Evolution
- **Selection Method**:
  - 50% based on fitness metrics:
    - Happiness score
    - Number of offspring
    - Generation number
    - Longest Lifespan
  - 50% random selection

- **Genetic Operations**:
  - Crossover of parent genomes
  - 50% random mutation rate

## Simulation Layers
1. **Basic Survival**: Agents learn to balance eating, working, resting
2. **Social Interaction**: Mating mechanics and partner selection
3. **Family Dynamics**: Child-rearing and resource allocation
4. **Generational Evolution**: Genetic inheritance and mutation
5. **Population Formation**: Emergence of cooperation and competition
6. **Economic Emergence**: Development of business and trade without instruction

## Societal Factors
- Emergent social structures
- Resource competition
- Potential for cooperation or exploitation
- Development of specialized roles
- Formation of family units and communities

## Metrics & Visualization
- Population statistics
- Genetic diversity
- Survival rates
- Learning efficiency
- Generational improvements
- Economic distribution
- Social network analysis


## TODO:
 - [ ] Add a health/energy/money/mood BAR/GRAPH/CHART/etc.
 - [ ] Add a UI for simulation stats
   - [ ] Toggle Panel to Open and Close + Tabs
   - [ ] Add Info Panel for entire Epoch
   - [ ] Add Info Panel for Learning Models
   - [ ] Add Info Panel for Agent Specific Stats for selected agent
   - [ ] Neural Network Visualization Panel for selected agent
    - [ ] Action Network
    - [ ] Target Network
 
 - [X] Clear old assets on each epoch
 - [X] Change animations based on behaviors
  - [ ] Add 'mating' animation when 2 agents are mating
  - [ ] Add 'working' animation when an agent is working at a business
  - [ ] Add 'eating' animation when an agent is eating versus acquiring food
    - [ ] Storing/Gathering Food should be different from Eating Food - Seperate Actions
 - [ ] When an agent is dead, other agents within their proximity should have a negative mood affection
 - [X] Want to build trust networks, and establish some prisoner's dilemma type interactions
 - [ ] Mating with a descendant of your own family should have a negative mutation effect
 - [X] Food should be able to be bought from a business, if there are agents working there
 - [X] Businesses should be able to go bankrupt if they have a negative expense : income ratio
 - [X] Change behavior of food to farm, and add planting/harvesting abilities
 - [X] Change food behavior to 'acquire', 'eat', and 'trade'
 - [X] Allow trading between individuals, and businesses
 - [X] Businesses should require inventory, and employees
 - [X] Individuals can be 'investors' to 'buy' inventory for a business and pay employees, and gain a percentage of the profit
 - [X] Determine aspect of how agents can 'invest' in businesses
 - [ ] Iterative Learning Model
   - [ ] Add a logging system for ongoing statistics, which can later be used for graphing results
   - [ ] Modify our workflow to allow for every 10 epochs to be logged via metrics
   - [ ] Modify our display system to only display every 100 epochs


New System Design
src/
|-- core/                               # Core framework components
|   |-- ecs/                            # Entity Component System
|   |   |-- entity_manager.py           # Entity creation and management
|   |   |-- component_manager.py        # Component registration and storage
|   |   |-- system_manager.py           # System registration and execution
|   |   |-- components/                 # Component definitions
|   |   |   |-- base.py                 # Base component class
|   |   |   |-- transform.py            # Position, rotation, scale
|   |   |   |-- renderable.py           # Visual representation components
|   |   |   |-- behavior.py             # Agent behavior components
|   |   |   |-- physics.py              # Movement and collision components
|   |   |-- systems/                    # System implementations
|   |       |-- render_system.py        # Handles rendering entities
|   |       |-- physics_system.py       # Movement and collision detection
|   |       |-- behavior_system.py      # Agent decision processing
|   |       |-- debug_system.py         # Debugging visualizations
|   |-- event/                          # Event system for decoupled communication
|   |   |-- event_manager.py            # Event dispatching and subscription
|   |   |-- event_types.py              # Event type definitions
|   |-- assets/                         # Asset management
|   |   |-- asset_manager.py            # Central asset loading and caching
|   |   |-- animation.py                # Animation handling
|   |-- spatial/                        # Spatial partitioning
|       |-- grid.py                     # Grid-based spatial queries
|-- simulation/                         # Simulation-specific logic
|   |-- entities/                       # Entity factory and definitions
|   |   |-- entity_factory.py           # Creates entities with components
|   |   |-- entity_types.py             # Entity type definitions
|   |-- world/                          # World management
|   |   |-- world.py                    # Main world container and manager
|   |   |-- resource_manager.py         # Food, work, and resource spawning
|   |-- agent/                          # Agent logic and AI
|   |   |-- decision/                   # Decision making systems
|   |   |   |-- q_learning.py           # Q-learning implementation
|   |   |   |-- neural_network.py       # Neural network implementation
|   |   |   |-- brain.py                # Combined decision system
|   |   |-- navigation.py               # Agent movement logic
|   |   |-- memory.py                   # Agent memory systems
|   |   |-- social.py                   # Social interactions between agents
|   |-- genetics/                       # Genetic systems
|   |   |-- genome.py                   # Genetic representation
|   |   |-- evolution.py                # Selection and evolution algorithms
|   |   |-- reproduction.py             # Mating mechanics
|   |-- society/                        # Population-level systems
|       |-- population.py               # Population management
|       |-- economy.py                  # Economic systems
|-- ui/                                 # User interface
|   |-- render/                         # Rendering systems
|   |   |-- renderer.py                 # Main rendering manager
|   |   |-- camera.py                   # Camera and viewport management
|   |-- hud/                            # Heads-up display elements
|   |   |-- entity_info.py              # Entity information display
|   |   |-- info_panel.py               # Simulation statistics
|   |-- visualization/                  # Data visualization
|       |-- charts.py                   # Statistical charting
|       |-- graph.py                    # Network/relationship graphs
|-- utils/                              # Utility functions and tools
|   |-- config.py                       # Configuration management
|   |-- profiler.py                     # Performance profiling
|   |-- logger.py                       # Logging system
|   |-- object_pool.py                  # Memory management with object pooling
|   |-- math_utils.py                   # Math utility functions
|-- data/                               # Data management
|   |-- metrics.py                      # Statistical data collection
|   |-- serialization.py                # Save/load functionality
|-- constants.py                        # Global constants and enums
|-- main.py                             # Application entry point
