"""
Genetic Operators for Permutation-based Exam Timetabling
Configures sampling, crossover, and mutation operators for pymoo
"""
import numpy as np
from pymoo.operators.sampling.rnd import PermutationRandomSampling
from pymoo.operators.crossover.ox import OrderCrossover
from pymoo.operators.mutation.inversion import InversionMutation
from pymoo.core.crossover import Crossover
from pymoo.core.mutation import Mutation
from pymoo.core.sampling import Sampling

class ValidPermutationSampling(Sampling):
    """
    Valid permutation sampling that ensures 0-indexed permutations for STA83
    """
    
    def _do(self, problem, n_samples, **kwargs):
        """Generate valid 0-indexed permutations for the problem"""
        # Generate valid permutations directly as numpy array
        X = np.zeros((n_samples, problem.n_var), dtype=int)
        
        for i in range(n_samples):
            # Generate a valid permutation of 0 to n_var-1
            X[i] = np.random.permutation(problem.n_var)
        
        return X

class STA83GeneticOperators:
    """
    Factory class for genetic operators specialized for exam timetabling permutations
    """
    
    @staticmethod
    def get_sampling():
        """Get valid permutation sampling operator"""
        return ValidPermutationSampling()
    
    @staticmethod
    def get_crossover(prob_crossover=0.9):
        """
        Get order crossover (OX) operator for permutations
        
        Args:
            prob_crossover: Probability of applying crossover
        """
        return OrderCrossover(prob=prob_crossover)
    
    @staticmethod
    def get_mutation(prob_mutation=0.1):
        """
        Get inversion mutation operator for permutations
        
        Args:
            prob_mutation: Probability of mutation per individual
                          Default is 0.1 for reasonable mutation rate
        """
        return InversionMutation(prob=prob_mutation)

class SwapMutation(Mutation):
    """
    Custom swap mutation for permutations - swaps two random positions
    Alternative to inversion mutation
    """
    
    def __init__(self, prob=None):
        super().__init__(prob)
    
    def _do(self, problem, X, **kwargs):
        """Apply swap mutation to population X"""
        
        # Determine mutation probability (default: 1/n_var)
        if self.prob is None:
            prob = 1.0 / problem.n_var
        else:
            prob = self.prob
        
        # Apply mutation
        for i in range(len(X)):
            if np.random.random() < prob:
                # Perform swap mutation
                x = X[i].copy()
                
                # Select two random positions
                pos1, pos2 = np.random.choice(len(x), 2, replace=False)
                
                # Swap elements
                x[pos1], x[pos2] = x[pos2], x[pos1]
                
                X[i] = x
        
        return X

def test_genetic_operators():
    """Test the genetic operators with sample permutations"""
    print("Testing Genetic Operators")
    print("="*40)
    
    # Set up test problem dimensions
    n_var = 10  # Smaller problem for testing
    n_pop = 5   # Small population
    
    # Test sampling
    print("\nTesting Valid Permutation Sampling")
    sampling = STA83GeneticOperators.get_sampling()
    
    # Create dummy problem for sampling
    class DummyProblem:
        def __init__(self):
            self.n_var = n_var
            self.xl = np.zeros(n_var)
            self.xu = np.ones(n_var) * (n_var - 1)
    
    dummy_problem = DummyProblem()
    
    # Generate sample population
    X = sampling(dummy_problem, n_pop)
    print(f"Generated population shape: {X.shape}")
    print(f"Sample permutations:")
    for i, perm in enumerate(X):
        print(f"  Individual {i}: {perm}")
    
    # Test crossover (simplified)
    print(f"\nTesting Order Crossover")
    crossover = STA83GeneticOperators.get_crossover()
    print(f"Order crossover operator created successfully")
    
    # Test inversion mutation (simplified)
    print(f"\nTesting Inversion Mutation")
    mutation = STA83GeneticOperators.get_mutation()
    print(f"Inversion mutation operator created successfully")
    
    # Test custom swap mutation (simplified)
    print(f"\nTesting Swap Mutation")
    swap_mutation = SwapMutation(prob=0.1)
    print(f"Swap mutation operator created successfully")
    
    # Validate permutation integrity
    print(f"\nValidating Permutation Integrity")
    
    def is_valid_permutation(perm, n):
        """Check if array is a valid permutation of 0 to n-1"""
        return (len(perm) == n and 
                set(perm) == set(range(n)) and 
                len(set(perm)) == n)
    
    # Check all generated solutions
    all_valid = True
    test_arrays = [X[0], X[1], X[2]]  # Just test some sample permutations
    names = ["Sample 1", "Sample 2", "Sample 3"]
    
    for name, arr in zip(names, test_arrays):
        valid = is_valid_permutation(arr.astype(int), n_var)
        print(f"  {name}: {'Valid' if valid else 'Invalid'} permutation")
        if not valid:
            all_valid = False
            print(f"    Contents: {arr}")
            print(f"    Expected: 0 to {n_var-1}")
    
    print(f"\nGenetic operators test completed!")
    print(f"All permutations valid: {'Yes' if all_valid else 'No'}")

if __name__ == "__main__":
    test_genetic_operators() 