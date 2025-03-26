# Society Simulation Design Document

## Overview
A society simulator using reinforcement learning and genetic algorithms where agents balance survival needs while having free agency to reproduce and evolve over generations.

## Agent Properties

Genome:
[Gender, Metabolism, Stamina, Learning Capacity, Attraction Profile, ..Q-learning table Values]

- **Basic Attributes**:
  - Gender: Male/Female
  - Age - Determines lifetime
  - Energy - Determines the ability to do actions or die
  - Hunger - Determines the ability to eat or die
  - Money - Determines the ability to buy food, and affects mating (or potentially requires working for it) - can be potentially inherited at a cost
  - Mood: Happiness (1) to Stress (-1)

- **Derived Inherited Attributes**:
  - Metabolic rate - Determines the rate at which energy is consumed (factor of mating, higher metabolic means more food is required, but work is more effective)
  - Stamina - Determines the ability to do actions or die (factor of mating, higher stamina means hunger is less of a factor, but can work longer)
  - Learning capacity - Determines Learning Rate in Q-learning (factor of mating)
  - Attraction profile - Determines the threshold for seeking a similar mate or higher trait mate (-1 - 1 : -1 = lower threshold, 1 = higher threshold)

- **Derived Non-Inherited Attributes**:
  - Generation - Determines the generation number of the agent
  - Offspring_Generations - Determines the number of generations the agent has had offspring
  - Offspring_Count - Determines the number of offspring the agent has had

## Actions
- Eat (consumes food, reduces hunger and generates energy)
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
- States: combinations of hunger/energy/money/mood levels and food/work/mate/rest/empty availability
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
5. **Society Formation**: Emergence of cooperation and competition
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
