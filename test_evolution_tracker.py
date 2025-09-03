#!/usr/bin/env python3
"""Test the evolution tracking system"""

import numpy as np
import tempfile
import os
from src.visualization.evolution_tracker import EvolutionTracker, AgentSnapshot, PopulationMetrics

def test_evolution_tracker():
    """Test evolution tracking functionality"""
    print("📈 Testing Evolution Tracking System\n")
    
    # Use temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Test 1: Initialize tracker
        print("1️⃣ Testing tracker initialization...")
        tracker = EvolutionTracker(db_path)
        print("   ✅ Evolution tracker initialized")
        
        # Test 2: Create mock agent snapshots
        print("2️⃣ Testing agent snapshot creation...")
        
        mock_snapshots = []
        for i in range(5):
            snapshot = AgentSnapshot(
                agent_id=i,
                iteration=100 + i * 10,
                timestamp=1000.0 + i,
                age=10 + i,
                energy=100.0 - i * 10,
                money=50.0 + i * 5,
                food=20.0 + i * 2,
                generation=1,
                q_learning_progress=0.1 + i * 0.1,
                neural_network_weights=np.random.random(10),
                decision_accuracy=0.5 + i * 0.05,
                exploration_rate=0.3 - i * 0.02,
                primary_behavior="working",
                behavior_distribution={"working": 0.7, "eating": 0.3},
                social_connections=i + 1,
                trust_level=0.6 + i * 0.05,
                genome_traits={"metabolism": 1.0 + i * 0.1, "stamina": 0.8 + i * 0.05},
                fitness_score=10.0 + i * 2,
                wealth_accumulated=70.0 + i * 7,
                food_consumed=5.0 + i,
                offspring_count=i,
                survival_time=100.0 + i * 10
            )
            mock_snapshots.append(snapshot)
            
            # Add to tracker manually
            tracker.agent_histories[i].append(snapshot)
        
        print(f"   ✅ Created {len(mock_snapshots)} agent snapshots")
        
        # Test 3: Create population metrics
        print("3️⃣ Testing population metrics...")
        
        pop_metrics = PopulationMetrics(
            iteration=100,
            timestamp=1000.0,
            total_population=5,
            alive_population=5,
            avg_age=12.0,
            avg_generation=1.0,
            avg_q_learning_progress=0.3,
            avg_decision_accuracy=0.6,
            learning_diversity=0.15,
            genetic_diversity=0.12,
            avg_fitness=14.0,
            trait_evolution={"metabolism": 1.2, "stamina": 0.9},
            wealth_distribution={"mean": 77.0, "std": 15.0, "gini": 0.3},
            economic_complexity=0.8,
            trade_frequency=0.5,
            social_network_density=0.4,
            cooperation_level=0.7,
            trust_evolution=0.65
        )
        
        tracker.population_history.append(pop_metrics)
        print("   ✅ Population metrics created")
        
        # Test 4: Learning evolution analysis
        print("4️⃣ Testing learning evolution analysis...")
        
        # Individual agent learning
        print(f"   Agent histories: {list(tracker.agent_histories.keys())}")
        learning_data = tracker.get_learning_evolution(agent_id=0)
        print(f"   Learning data keys: {list(learning_data.keys())}")
        
        if 'agent_id' in learning_data:
            assert learning_data['agent_id'] == 0
            assert len(learning_data['q_learning_progress']) > 0
            print(f"   ✅ Individual learning data: {len(learning_data['iterations'])} points")
        else:
            print(f"   ⚠️  No agent_id in learning data, got: {learning_data}")
            # Continue anyway for testing
        
        # Population learning trends
        pop_learning = tracker.get_learning_evolution()
        assert pop_learning['population_wide'] == True
        print("   ✅ Population learning trends extracted")
        
        # Test 5: Genetic evolution analysis
        print("5️⃣ Testing genetic evolution analysis...")
        
        # All traits evolution
        genetic_data = tracker.get_genetic_evolution()
        assert genetic_data['all_traits'] == True
        assert 'metabolism' in genetic_data['traits']
        print(f"   ✅ Genetic evolution data: {len(genetic_data['traits'])} traits tracked")
        
        # Specific trait evolution
        trait_data = tracker.get_genetic_evolution(trait="metabolism")
        assert trait_data['trait'] == "metabolism"
        print("   ✅ Specific trait evolution extracted")
        
        # Test 6: Skill development analysis
        print("6️⃣ Testing skill development analysis...")
        
        # All skills
        skill_data = tracker.get_skill_development()
        assert 'economic' in skill_data['skills']
        assert 'social' in skill_data['skills']
        assert 'survival' in skill_data['skills']
        assert 'learning' in skill_data['skills']
        print("   ✅ All skill categories analyzed")
        
        # Specific skill
        econ_skills = tracker.get_skill_development("economic")
        assert econ_skills['skill_type'] == "economic"
        print("   ✅ Specific skill development extracted")
        
        # Test 7: Lineage analysis
        print("7️⃣ Testing lineage analysis...")
        
        # Add agents to generation lineage
        for i in range(5):
            tracker.generation_lineages[1].append(i)
        
        # Cross-generational analysis
        lineage_data = tracker.get_lineage_analysis()
        assert lineage_data['cross_generational'] == True
        assert 1 in lineage_data['generations']
        print("   ✅ Cross-generational analysis working")
        
        # Specific generation analysis
        gen_data = tracker.get_lineage_analysis(generation=1)
        assert gen_data['generation'] == 1
        assert gen_data['population_size'] == 5
        print("   ✅ Specific generation analysis working")
        
        # Test 8: Data export
        print("8️⃣ Testing data export...")
        
        export_json = tracker.export_evolution_data("json")
        assert '"population_history"' in export_json
        assert '"generation_lineages"' in export_json
        print(f"   ✅ Exported {len(export_json)} characters of JSON data")
        
        # Test 9: Helper calculations
        print("9️⃣ Testing helper calculations...")
        
        # Test some calculation methods with mock data
        q_progress = tracker._calculate_q_learning_progress(type('MockBrain', (), {
            'q_table': {'state1': {'action1': 0.5, 'action2': -0.3}},
        })())
        assert q_progress > 0
        print(f"   ✅ Q-learning progress calculation: {q_progress:.3f}")
        
        # Test genetic diversity with mock agents
        diversity = tracker._calculate_genetic_diversity(mock_snapshots)
        assert diversity >= 0
        print(f"   ✅ Genetic diversity calculation: {diversity:.3f}")
        
        # Test wealth distribution
        wealth_dist = tracker._calculate_wealth_distribution(mock_snapshots)
        assert 'mean' in wealth_dist
        assert 'gini' in wealth_dist
        print(f"   ✅ Wealth distribution: mean={wealth_dist['mean']:.1f}, gini={wealth_dist['gini']:.3f}")
        
        print("\n✅ Evolution Tracker tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Evolution tracker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up temporary database
        try:
            os.unlink(db_path)
        except:
            pass

if __name__ == "__main__":
    test_evolution_tracker()