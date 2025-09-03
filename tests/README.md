# Society Simulation Testing Framework

This comprehensive testing framework ensures the Society simulation runs correctly, performs well, and handles edge cases gracefully.

## 📁 Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest configuration and fixtures
├── README.md                   # This documentation
├── unit/                       # Unit tests for individual components
│   ├── components/            # ECS component tests
│   ├── systems/               # System logic tests
│   ├── ai/                    # Agent AI tests
│   └── critical/              # Critical issue tests
├── integration/               # Integration tests for full scenarios
├── stress/                    # Stress tests for performance/scaling
├── benchmarks/                # Performance benchmarks
└── fixtures/                  # Test data factories and utilities

```

## 🚀 Quick Start

### Install Test Dependencies
```bash
# Install all test dependencies
python run_tests.py --install

# Or manually
pip install -r requirements-test.txt
```

### Run All Tests
```bash
# Run complete test suite
python run_tests.py

# Run with verbose output
python run_tests.py --verbose
```

### Run Specific Test Types
```bash
# Unit tests only
python run_tests.py --unit

# Integration tests only
python run_tests.py --integration

# Stress tests only
python run_tests.py --stress

# Performance benchmarks only
python run_tests.py --benchmarks

# Critical issue tests only
python run_tests.py --critical
```

## 🧪 Test Categories

### Unit Tests (`tests/unit/`)
Test individual components in isolation:

- **ECS Components** (`tests/unit/components/`)
  - BehaviorComponent
  - EconomicComponent
  - SocialComponent
  - And all other ECS components

- **Systems** (`tests/unit/systems/`)
  - BehaviorSystem (decision making)
  - EconomicSystem (trade, work, investment)
  - SocialSystem (relationships, reputation)
  - AgriculturalSystem (farming cycles)
  - ReproductionSystem (agent birth/death)

- **Agent AI** (`tests/unit/ai/`)
  - AgentBrain (hybrid decision making)
  - Q-learning algorithms
  - Neural network integration
  - Memory systems

- **Critical Issues** (`tests/unit/critical/`)
  - Memory leak detection
  - Dead agent cleanup
  - Resource reference management
  - Performance bottlenecks

### Integration Tests (`tests/integration/`)
Test complete simulation workflows:

- **Simulation Lifecycle**
  - World initialization
  - Agent creation and setup
  - Multi-system interactions
  - Long-running stability

- **Economic Interactions**
  - Agent-workplace relationships
  - Trade between agents
  - Investment systems
  - Resource flow

- **Social Dynamics**
  - Relationship formation
  - Trust and affinity changes
  - Social reputation effects
  - Conflict resolution

### Stress Tests (`tests/stress/`)
Test performance under extreme conditions:

- **Population Scaling**
  - 10, 50, 100, 500+ agent performance
  - Memory usage scaling
  - Update time scaling
  - Resource contention

- **Long-running Stability**
  - 1000+ simulation steps
  - Memory leak detection
  - Performance degradation
  - Population dynamics

- **Resource Scarcity**
  - Economic collapse scenarios
  - Food shortage effects
  - High unemployment stress
  - Social breakdown conditions

### Benchmark Tests (`tests/benchmarks/`)
Performance measurement and regression detection:

- **FPS Target Benchmarks**
  - 30+ FPS maintenance
  - Update time measurements
  - System performance profiling

- **Memory Usage Benchmarks**
  - Memory per agent calculations
  - Growth rate monitoring
  - Cleanup efficiency

- **Scalability Benchmarks**
  - Population size vs performance
  - System count vs performance
  - Resource usage efficiency

## 📊 Test Metrics & Coverage

### Coverage Requirements
- **Minimum Coverage**: 80% for all modules
- **Critical Systems**: 90%+ coverage required
- **New Code**: 100% coverage for new features

### Performance Thresholds
- **Update Time**: <33ms per frame (30 FPS target)
- **Memory Usage**: <5MB per agent
- **Population Scaling**: Linear performance up to 100 agents
- **Memory Growth**: <1MB per 100 simulation steps

### Critical Test Scenarios
Based on the simulation analysis, these scenarios are tested:

1. **Memory Leak Prevention**
   - Social memory unbounded growth
   - Dead agent reference cleanup
   - Experience replay buffer limits

2. **Economic Balance**
   - Reward system normalization
   - Resource chain validation
   - Market dynamics testing

3. **Agent Lifecycle**
   - Birth/death mechanics
   - Energy starvation effects
   - Age-related mortality

4. **Performance Optimization**
   - Spatial indexing efficiency
   - System update throttling
   - State caching effectiveness

## 🛠️ Test Configuration

### Pytest Configuration (`pytest.ini`)
- **Test Discovery**: Automatic test file detection
- **Coverage Settings**: HTML, XML, and terminal reports
- **Markers**: Unit, integration, stress, benchmark, critical
- **Timeouts**: 300 seconds for stress tests
- **Warnings**: Filtered for clean output

### Fixtures and Factories (`tests/conftest.py`, `tests/fixtures/`)
- **Mock Pygame**: Headless testing support
- **Test Genomes**: Predictable agent genetics
- **Test Agents**: Configurable agent properties
- **World Builders**: Custom simulation scenarios
- **Memory Tracking**: Leak detection utilities

## 📈 Continuous Integration

### GitHub Actions Workflow (`.github/workflows/tests.yml`)
- **Multi-Python Support**: Tests on Python 3.8-3.11
- **Automated Testing**: On every push and PR
- **Daily Stress Tests**: Scheduled stress testing
- **Coverage Reporting**: Codecov integration
- **Benchmark Tracking**: Performance regression detection

### Local CI Commands
```bash
# Full CI simulation
python run_tests.py --verbose

# Quick validation
python run_tests.py --unit --integration --critical

# Performance check
python run_tests.py --benchmarks --no-benchmarks
```

## 🎯 Test Data and Scenarios

### Predefined Scenarios (`tests/fixtures/data_factories.py`)
- **Economic Crisis**: High unemployment, resource scarcity
- **Population Boom**: Rapid growth, resource abundance
- **Social Conflict**: Corruption vs honesty dynamics
- **Aging Population**: Few young workers, many elderly
- **Resource Abundance**: Optimal conditions testing

### Custom Scenario Creation
```python
from tests.fixtures.data_factories import TestDataBuilder

# Create custom scenario
scenario = (TestDataBuilder()
    .add_agents(50, energy=75, money=25)
    .add_farms(10, yield_amount=8)
    .add_workplaces(5, capacity=10)
    .build_balanced())
```

## 🐛 Debugging Failed Tests

### Common Issues and Solutions

1. **Memory Leaks**
   ```bash
   # Run critical tests with memory profiling
   python -m pytest tests/unit/critical/ -v --tb=short
   ```

2. **Performance Regressions**
   ```bash
   # Compare benchmarks
   python run_tests.py --benchmarks --verbose
   ```

3. **Integration Failures**
   ```bash
   # Run with full traceback
   python -m pytest tests/integration/ -v --tb=long
   ```

### Test Report Analysis
After running tests, check:
- `tests/TEST_REPORT.md` - Human-readable summary
- `tests/test_report.json` - Machine-readable results
- `tests/coverage_html/index.html` - Coverage visualization

## 📋 Test Development Guidelines

### Writing New Tests
1. **Use Appropriate Fixtures**: Leverage existing test data factories
2. **Test Edge Cases**: Include boundary conditions and error cases
3. **Mock External Dependencies**: Keep tests isolated
4. **Assert Meaningfully**: Clear, specific assertions
5. **Document Intent**: Comment complex test scenarios

### Test Organization
- **One Concept Per Test**: Single responsibility principle
- **Descriptive Names**: Clear test function names
- **Proper Markers**: Use `@pytest.mark.unit`, etc.
- **Setup/Teardown**: Minimal, focused fixture usage

### Performance Testing
- **Baseline Measurements**: Establish performance baselines
- **Realistic Data**: Use representative test scenarios
- **Resource Cleanup**: Prevent test interference
- **Statistical Significance**: Multiple runs for benchmarks

## 🚨 Known Test Limitations

1. **Pygame Dependency**: Requires headless display setup for CI
2. **Random Behavior**: Some tests may have variability due to simulation randomness
3. **System-Dependent Performance**: Benchmarks vary by hardware
4. **Memory Testing**: Garbage collection timing affects memory tests

## 📞 Support and Contributing

### Running Tests Locally
1. Clone the repository
2. Install test dependencies: `python run_tests.py --install`
3. Run tests: `python run_tests.py`
4. Check coverage: Open `tests/coverage_html/index.html`

### Contributing New Tests
1. Follow existing test patterns
2. Add appropriate fixtures for new scenarios
3. Update this documentation for new test categories
4. Ensure CI passes with new tests

### Reporting Issues
If tests fail unexpectedly:
1. Check `tests/TEST_REPORT.md` for details
2. Run specific failing test with `-v` flag
3. Include test output and system information in bug reports
4. Verify test environment setup is correct

---

This testing framework ensures the Society simulation is robust, performant, and maintainable. Regular testing helps catch regressions early and validates new features work correctly under various conditions.