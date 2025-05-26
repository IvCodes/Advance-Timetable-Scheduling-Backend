# Hybrid NSGA-II + DQN Algorithm for STA83 Exam Timetabling

## Overview

The Hybrid NSGA-II + DQN algorithm combines the strengths of two powerful optimization approaches:

1. **NSGA-II (Non-dominated Sorting Genetic Algorithm II)**: A multi-objective evolutionary algorithm that excels at exploring the solution space and finding diverse Pareto-optimal solutions.

2. **DQN (Deep Q-Network)**: A reinforcement learning algorithm that can learn intelligent policies for solution construction and refinement.

## Algorithm Design

### Hybrid Architecture

The hybrid algorithm follows a **post-NSGA-II refinement** approach:

1. **Phase 1: NSGA-II Optimization**
   - Runs standard NSGA-II to generate a diverse set of candidate solutions
   - Uses permutation encoding with greedy decoding
   - Optimizes two objectives: minimize timeslots and minimize proximity penalty

2. **Phase 2: DQN Refinement** (Optional)
   - Selects top solutions from NSGA-II Pareto front
   - Applies trained DQN agent to attempt solution improvement
   - Evaluates refined solutions and keeps improvements

### Key Components

#### DQNRefinementAgent
- Specialized DQN agent configured for solution refinement
- Lower exploration rate (epsilon) for focused improvement
- Smaller replay buffer optimized for refinement tasks
- Can load pre-trained models for immediate use

#### HybridNSGA2DQN
- Main hybrid algorithm coordinator
- Configurable parameters for both NSGA-II and DQN phases
- Automatic model detection and loading
- Comprehensive result tracking and statistics

#### HybridNSGA2DQNRunner
- High-level interface for running hybrid optimization
- Integrates with existing algorithm runner framework
- Supports multiple run modes (quick, standard, full)

## Usage

### Basic Usage

```python
from core.sta83_data_loader import STA83DataLoader
from algorithms.hybrid_nsga2_dqn import HybridNSGA2DQNRunner

# Load data
data_loader = STA83DataLoader(crs_file='data/sta-f-83.crs', stu_file='data/sta-f-83.stu')
data_loader.load_data()

# Create and run hybrid algorithm
runner = HybridNSGA2DQNRunner(data_loader)
results = runner.run_hybrid(
    pop_size=50,
    generations=25,
    dqn_model_path='path/to/trained_model.pth',  # Optional
    seed=42
)
```

### Using Algorithm Runner

```python
from algorithm_runner import AlgorithmRunner

runner = AlgorithmRunner()

# Run hybrid algorithm with different modes
success, message = runner.run_hybrid('quick')    # Fast test
success, message = runner.run_hybrid('standard') # Balanced run
success, message = runner.run_hybrid('full')     # Comprehensive run
```

### Command Line Usage

```bash
# Run the algorithm runner and select hybrid algorithm
python algorithm_runner.py

# Or test the hybrid algorithm directly
python test_hybrid.py
```

## Configuration

### Run Modes

The hybrid algorithm supports three run modes:

| Mode | Population Size | Generations | Description |
|------|----------------|-------------|-------------|
| Quick | 20 | 10 | Fast test run with minimal parameters |
| Standard | 50 | 25 | Balanced run with moderate parameters |
| Full | 100 | 50 | Comprehensive run with full parameters |

### NSGA-II Parameters

- **Population Size**: Number of individuals in each generation
- **Generations**: Number of evolutionary generations
- **Crossover**: Order crossover with 90% probability
- **Mutation**: Inversion mutation with 10% probability
- **Selection**: Tournament selection with crowding distance

### DQN Refinement Parameters

- **Refine Frequency**: How often to apply refinement (default: every 10 generations)
- **Refine Top N**: Number of top solutions to refine (default: 5)
- **Max Refinement Steps**: Maximum steps per refinement attempt (default: 10)
- **Learning Rate**: 0.0001 (lower than training for stability)
- **Exploration**: 0.1 start, 0.01 end (low exploration for refinement)

## Dependencies

### Required
- numpy
- pymoo (for NSGA-II)
- Core STA83 modules (data_loader, problem_fixed, genetic_operators)

### Optional (for DQN refinement)
- PyTorch
- RL modules (environment, agent)

**Note**: The algorithm gracefully degrades to NSGA-II-only mode if PyTorch is not available.

## Results and Output

### Result Structure

```python
{
    'nsga2_results': <pymoo_result>,           # Original NSGA-II results
    'final_pareto_front': <numpy_array>,      # Final objective values
    'final_solutions': <numpy_array>,         # Final solution permutations
    'execution_time': <float>,                # Total runtime in seconds
    'refinement_stats': [                     # DQN refinement statistics
        {
            'solution_index': <int>,
            'original_objective': [<float>, <float>],
            'refined_objective': [<float>, <float>],
            'improvement': <bool>
        }
    ],
    'algorithm': 'Hybrid NSGA-II + DQN'
}
```

### Performance Metrics

The algorithm tracks several performance metrics:

- **Pareto Front Size**: Number of non-dominated solutions found
- **Best Timeslots**: Minimum number of timeslots in any solution
- **Best Penalty**: Minimum proximity penalty in any solution
- **DQN Improvements**: Number of solutions improved by DQN refinement
- **Execution Time**: Total runtime including both phases

## Integration with Existing Framework

The hybrid algorithm is fully integrated with the existing STA83 framework:

### Algorithm Runner Integration
- Added to all run modes (quick, standard, full)
- Included in single algorithm and all algorithms runs
- Automatic DQN model detection and loading
- Consistent result reporting format

### Data Compatibility
- Uses same STA83DataLoader as other algorithms
- Compatible with existing problem formulation
- Same permutation encoding and evaluation functions

### Result Compatibility
- Results can be compared with other algorithms
- Same objective space (timeslots, proximity penalty)
- Compatible with existing analysis and visualization tools

## Advanced Features

### Automatic Model Detection
The algorithm automatically searches for trained DQN models in common locations:
- `results/dqn_final_results/trained_dqn_model.pth`
- `results/dqn_sta83_results_*/trained_dqn_model.pth`
- `results/*/trained_dqn_model.pth`

### Graceful Degradation
- Falls back to NSGA-II-only if PyTorch unavailable
- Continues if DQN model loading fails
- Provides clear status messages about DQN availability

### Flexible Refinement Strategy
- Configurable refinement frequency and intensity
- Multiple solution improvement criteria
- Detailed refinement statistics and reporting

## Testing

### Basic Test
```bash
python test_hybrid.py
```

### Integration Test
```bash
python algorithm_runner.py
# Select option 1 (Single Algorithm)
# Select option 5 (Hybrid NSGA-II+DQN)
# Select desired run mode
```

## Future Enhancements

### Potential Improvements

1. **Online Refinement**: Apply DQN refinement during NSGA-II evolution rather than post-processing
2. **Adaptive Refinement**: Dynamically adjust refinement parameters based on solution quality
3. **Multi-Objective DQN**: Train DQN specifically for multi-objective refinement
4. **Solution Seeding**: Use DQN to generate initial population for NSGA-II
5. **Hybrid Operators**: Integrate DQN-learned operators into NSGA-II crossover/mutation

### Research Opportunities

1. **Comparative Analysis**: Systematic comparison with pure NSGA-II and pure DQN
2. **Parameter Sensitivity**: Study impact of refinement parameters on performance
3. **Scalability**: Test on larger exam timetabling instances
4. **Transfer Learning**: Apply trained models to different timetabling problems

## References

This implementation is based on the research framework described in the STA83 exam timetabling project, combining:

- NSGA-II multi-objective optimization
- Deep Q-Network reinforcement learning
- Hybrid evolutionary-RL approaches for combinatorial optimization

The algorithm represents a novel approach to exam timetabling that leverages the complementary strengths of population-based search and learned solution construction policies. 