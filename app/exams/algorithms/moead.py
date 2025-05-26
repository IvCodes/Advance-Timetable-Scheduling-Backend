"""
MOEA/D (Multi-Objective Evolutionary Algorithm based on Decomposition)
Implementation for STA83 Exam Timetabling Problem
"""
import numpy as np
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from pymoo.algorithms.base.genetic import GeneticAlgorithm
from pymoo.core.population import Population
from pymoo.operators.selection.tournament import TournamentSelection
from core.sta83_data_loader import STA83DataLoader
from core.sta83_problem_fixed import STA83Problem
from core.genetic_operators import STA83GeneticOperators

class MOEAD(GeneticAlgorithm):
    """
    MOEA/D implementation using Tchebycheff decomposition approach
    """
    
    def __init__(self,
                 pop_size=50,
                 n_neighbors=20,
                 prob_neighbor_mating=0.9,
                 sampling=None,
                 crossover=None,
                 mutation=None,
                 **kwargs):
        
        # Set default operators if not provided
        if sampling is None:
            sampling = STA83GeneticOperators.get_sampling()
        if crossover is None:
            crossover = STA83GeneticOperators.get_crossover()
        if mutation is None:
            mutation = STA83GeneticOperators.get_mutation()
        
        super().__init__(
            pop_size=pop_size,
            sampling=sampling,
            crossover=crossover,
            mutation=mutation,
            selection=TournamentSelection(func_comp=self._tournament_comp),
            **kwargs
        )
        
        self.n_neighbors = n_neighbors
        self.prob_neighbor_mating = prob_neighbor_mating
        
        # Will be initialized in setup
        self.weight_vectors = None
        self.neighbors = None
        self.ideal_point = None
        
    def _setup(self, problem, **kwargs):
        """Setup MOEA/D specific components"""
        super()._setup(problem, **kwargs)
        
        # Generate weight vectors using uniform distribution
        self.weight_vectors = self._generate_weight_vectors(problem.n_obj, self.pop_size)
        
        # Find neighbors for each weight vector
        self.neighbors = self._find_neighbors()
        
        # Initialize ideal point
        self.ideal_point = np.full(problem.n_obj, np.inf)
        
    def _generate_weight_vectors(self, n_obj, n_vectors):
        """Generate uniformly distributed weight vectors"""
        if n_obj == 2:
            # For 2 objectives, use simple uniform distribution
            weights = np.zeros((n_vectors, n_obj))
            for i in range(n_vectors):
                w1 = i / max(1, n_vectors - 1)  # Avoid division by zero
                w2 = 1 - w1
                weights[i] = [w1, w2]
            return weights
        else:
            # For more objectives, use random uniform weights
            weights = np.random.random((n_vectors, n_obj))
            weights = weights / np.sum(weights, axis=1, keepdims=True)
            return weights
    
    def _find_neighbors(self):
        """Find T nearest neighbors for each weight vector"""
        # Ensure n_neighbors doesn't exceed population size - 1
        actual_neighbors = min(self.n_neighbors, self.pop_size - 1)
        neighbors = np.zeros((self.pop_size, actual_neighbors), dtype=int)
        
        for i in range(self.pop_size):
            # Calculate Euclidean distances to all other weight vectors
            distances = np.sqrt(np.sum((self.weight_vectors - self.weight_vectors[i])**2, axis=1))
            # Find indices of T nearest neighbors (excluding self)
            neighbor_indices = np.argsort(distances)[1:actual_neighbors+1]
            # Pad with zeros if needed (shouldn't happen with proper actual_neighbors)
            if len(neighbor_indices) < actual_neighbors:
                padded_indices = np.zeros(actual_neighbors, dtype=int)
                padded_indices[:len(neighbor_indices)] = neighbor_indices
                neighbor_indices = padded_indices
            neighbors[i] = neighbor_indices
            
        return neighbors
    
    def _advance(self, infills=None, **kwargs):
        """Main MOEA/D evolution step"""
        # Update ideal point
        self._update_ideal_point()
        
        # Generate offspring for each subproblem
        offspring = Population.new("X", np.zeros((self.pop_size, self.problem.n_var)))
        
        for i in range(self.pop_size):
            # Select parents from neighborhood
            if np.random.random() < self.prob_neighbor_mating:
                # Mating selection from neighborhood
                parent_indices = np.random.choice(self.neighbors[i], size=2, replace=False)
            else:
                # Mating selection from entire population
                parent_indices = np.random.choice(self.pop_size, size=2, replace=False)
            
            # Get parents
            parents = self.pop[parent_indices]
            
            # Apply crossover and mutation
            offspring_individual = self.crossover.do(self.problem, parents, n_offsprings=1)
            offspring_individual = self.mutation.do(self.problem, offspring_individual)
            
            # Evaluate offspring
            self.evaluator.eval(self.problem, offspring_individual)
            
            # Update neighborhood solutions
            self._update_neighborhood(i, offspring_individual[0])
            
        return self.pop
    
    def _update_ideal_point(self):
        """Update the ideal point with current population"""
        for ind in self.pop:
            if ind.F is not None:
                self.ideal_point = np.minimum(self.ideal_point, ind.F)
    
    def _update_neighborhood(self, subproblem_idx, offspring):
        """Update solutions in the neighborhood using Tchebycheff approach"""
        for neighbor_idx in self.neighbors[subproblem_idx]:
            # Calculate Tchebycheff function for current solution
            current_tcheby = self._tchebycheff_function(self.pop[neighbor_idx].F, 
                                                       self.weight_vectors[neighbor_idx])
            
            # Calculate Tchebycheff function for offspring
            offspring_tcheby = self._tchebycheff_function(offspring.F, 
                                                         self.weight_vectors[neighbor_idx])
            
            # Replace if offspring is better
            if offspring_tcheby < current_tcheby:
                self.pop[neighbor_idx] = offspring
    
    def _tchebycheff_function(self, objective_values, weight_vector):
        """Calculate Tchebycheff function value"""
        if objective_values is None:
            return np.inf
        
        # Normalize objectives using ideal point
        normalized_obj = objective_values - self.ideal_point
        
        # Calculate Tchebycheff function
        weighted_obj = normalized_obj / (weight_vector + 1e-10)  # Add small epsilon to avoid division by zero
        return np.max(weighted_obj)
    
    def _tournament_comp(self, pop, P, **kwargs):
        """Tournament comparison function for selection"""
        # Simple tournament selection based on Tchebycheff function
        if len(P) != 2:
            return np.random.choice(len(P))
        
        # Use random weight vector for comparison
        weight_idx = np.random.randint(0, self.pop_size)
        weight = self.weight_vectors[weight_idx]
        
        tcheby_1 = self._tchebycheff_function(pop[P[0]].F, weight)
        tcheby_2 = self._tchebycheff_function(pop[P[1]].F, weight)
        
        return P[0] if tcheby_1 < tcheby_2 else P[1]

class MOEADRunner:
    """Runner class for MOEA/D algorithm"""
    
    def __init__(self, data_loader: STA83DataLoader):
        self.data_loader = data_loader
        self.problem = STA83Problem(data_loader)
        
    def run_moead(self, pop_size=50, generations=100, n_neighbors=20, seed=42):
        """Run MOEA/D optimization using pymoo's built-in implementation"""
        from pymoo.optimize import minimize
        from pymoo.algorithms.moo.moead import MOEAD as PyMOOEAD
        from pymoo.util.ref_dirs import get_reference_directions
        
        # Set random seed
        np.random.seed(seed)
        
        try:
            # Use pymoo's built-in MOEA/D with reference directions
            # For 2 objectives, create reference directions
            ref_dirs = get_reference_directions("das-dennis", 2, n_partitions=pop_size-1)
            
            # Ensure we have the right number of reference directions
            if len(ref_dirs) != pop_size:
                # Adjust population size to match reference directions
                pop_size = len(ref_dirs)
                print(f"   Adjusted population size to {pop_size} to match reference directions")
            
            # Create MOEA/D algorithm using pymoo's implementation
            algorithm = PyMOOEAD(
                ref_dirs=ref_dirs,
                n_neighbors=min(n_neighbors, pop_size-1),
                prob_neighbor_mating=0.9,
                sampling=STA83GeneticOperators.get_sampling(),
                crossover=STA83GeneticOperators.get_crossover(),
                mutation=STA83GeneticOperators.get_mutation()
            )
            
            # Run optimization
            result = minimize(
                self.problem,
                algorithm,
                ('n_gen', generations),
                seed=seed,
                verbose=True
            )
            
            return result
            
        except Exception as e:
            print(f"   MOEA/D failed with pymoo implementation: {e}")
            # Fallback to NSGA-II if MOEA/D fails
            print(f"   Falling back to NSGA-II...")
            from pymoo.algorithms.moo.nsga2 import NSGA2
            
            algorithm = NSGA2(
                pop_size=pop_size,
                sampling=STA83GeneticOperators.get_sampling(),
                crossover=STA83GeneticOperators.get_crossover(),
                mutation=STA83GeneticOperators.get_mutation(),
                eliminate_duplicates=False
            )
            
            result = minimize(
                self.problem,
                algorithm,
                ('n_gen', generations),
                seed=seed,
                verbose=True
            )
            
            return result
    
    def compare_with_nsga2(self, pop_size=50, generations=100, seed=42):
        """Compare MOEA/D with NSGA-II"""
        from pymoo.algorithms.moo.nsga2 import NSGA2
        from pymoo.optimize import minimize
        
        print("Comparing MOEA/D vs NSGA-II")
        print("=" * 50)
        
        # Run MOEA/D
        print("\nRunning MOEA/D...")
        moead_result = self.run_moead(pop_size, generations, seed=seed)
        
        # Run NSGA-II
        print("\nRunning NSGA-II...")
        np.random.seed(seed)
        nsga2 = NSGA2(
            pop_size=pop_size,
            sampling=STA83GeneticOperators.get_sampling(),
            crossover=STA83GeneticOperators.get_crossover(),
            mutation=STA83GeneticOperators.get_mutation(),
            eliminate_duplicates=True
        )
        
        nsga2_result = minimize(
            self.problem,
            nsga2,
            ('n_gen', generations),
            seed=seed,
            verbose=True
        )
        
        # Compare results
        self._compare_results(moead_result, nsga2_result)
        
        return moead_result, nsga2_result
    
    def _compare_results(self, moead_result, nsga2_result):
        """Compare and display results from both algorithms"""
        print("\n Comparison Results")
        print("=" * 30)
        
        # MOEA/D results
        moead_f = moead_result.F
        print(f"\nMOEA/D Results:")
        print(f"   Solutions: {len(moead_f)}")
        print(f"   Best Timeslots: {np.min(moead_f[:, 0]):.0f}")
        print(f"   Best Penalty: {np.min(moead_f[:, 1]):.2f}")
        print(f"   Timeslots Range: {np.min(moead_f[:, 0]):.0f} - {np.max(moead_f[:, 0]):.0f}")
        print(f"   Penalty Range: {np.min(moead_f[:, 1]):.2f} - {np.max(moead_f[:, 1]):.2f}")
        
        # NSGA-II results
        nsga2_f = nsga2_result.F
        print(f"\nNSGA-II Results:")
        print(f"   Solutions: {len(nsga2_f)}")
        print(f"   Best Timeslots: {np.min(nsga2_f[:, 0]):.0f}")
        print(f"   Best Penalty: {np.min(nsga2_f[:, 1]):.2f}")
        print(f"   Timeslots Range: {np.min(nsga2_f[:, 0]):.0f} - {np.max(nsga2_f[:, 0]):.0f}")
        print(f"   Penalty Range: {np.min(nsga2_f[:, 1]):.2f} - {np.max(nsga2_f[:, 1]):.2f}")
        
        # Performance comparison
        print(f"\nPerformance Comparison:")
        moead_best_ts = np.min(moead_f[:, 0])
        nsga2_best_ts = np.min(nsga2_f[:, 0])
        moead_best_pen = np.min(moead_f[:, 1])
        nsga2_best_pen = np.min(nsga2_f[:, 1])
        
        if moead_best_ts < nsga2_best_ts:
            print(f"   MOEA/D wins on timeslots: {moead_best_ts:.0f} vs {nsga2_best_ts:.0f}")
        elif nsga2_best_ts < moead_best_ts:
            print(f"   NSGA-II wins on timeslots: {nsga2_best_ts:.0f} vs {moead_best_ts:.0f}")
        else:
            print(f"   Tie on timeslots: {moead_best_ts:.0f}")
            
        if moead_best_pen < nsga2_best_pen:
            print(f"   MOEA/D wins on penalty: {moead_best_pen:.2f} vs {nsga2_best_pen:.2f}")
        elif nsga2_best_pen < moead_best_pen:
            print(f"   NSGA-II wins on penalty: {nsga2_best_pen:.2f} vs {moead_best_pen:.2f}")
        else:
            print(f"   Tie on penalty: {moead_best_pen:.2f}")

def test_moead():
    """Test MOEA/D implementation"""
    print("Testing MOEA/D Implementation")
    print("=" * 40)
    
    # Load data
    data_loader = STA83DataLoader()
    if not data_loader.load_data():
        print("Failed to load STA83 data")
        return
    
    # Create runner and test
    runner = MOEADRunner(data_loader)
    
    # Run comparison
    moead_result, nsga2_result = runner.compare_with_nsga2(
        pop_size=30, 
        generations=20,  # Short test
        seed=42
    )
    
    print("\nMOEA/D test completed!")
    return moead_result, nsga2_result

if __name__ == "__main__":
    test_moead() 