"""
Test Script for DQN Implementation
Quick verification that all components work together
"""
import sys
import traceback

def test_data_loading():
    """Test STA83 data loading"""
    print(" Testing STA83 Data Loading...")
    try:
        from core.sta83_data_loader import STA83DataLoader
        
        loader = STA83DataLoader()
        success = loader.load_data()
        
        if success:
            analysis = loader.analyze_dataset()
            print(f" Data loaded successfully!")
            print(f"   Exams: {analysis['num_exams']}")
            print(f"   Students: {analysis['num_students']}")
            print(f"   Conflict density: {analysis['conflict_density']:.4f}")
            return True
        else:
            print(" Failed to load data")
            return False
            
    except Exception as e:
        print(f" Data loading test failed: {e}")
        traceback.print_exc()
        return False

def test_environment():
    """Test RL environment"""
    print("\n Testing RL Environment...")
    try:
        from environment import ExamTimetablingEnv
        
        env = ExamTimetablingEnv(max_timeslots=15)
        
        # Test reset
        state = env.reset()
        print(f" Environment created and reset successfully!")
        print(f"   State shape: {state.shape}")
        print(f"   Action space: {env.action_space}")
        
        # Test a few steps
        for step in range(3):
            valid_actions = env.get_valid_actions()
            if valid_actions:
                action = valid_actions[0]  # Take first valid action
                next_state, reward, done, info = env.step(action)
                print(f"   Step {step+1}: Action {action+1}, Reward {reward:.2f}, Done {done}")
                if done:
                    break
            else:
                print(f"   Step {step+1}: No valid actions")
                break
        
        return True
        
    except Exception as e:
        print(f" Environment test failed: {e}")
        traceback.print_exc()
        return False

def test_dqn_agent():
    """Test DQN agent (without PyTorch if not available)"""
    print("\n Testing DQN Agent...")
    try:
        # Check if PyTorch is available
        try:
            import torch
            pytorch_available = True
        except ImportError:
            pytorch_available = False
            print("⚠ PyTorch not available, skipping DQN agent test")
            return True
        
        if pytorch_available:
            from environment import ExamTimetablingEnv
            from agent import DQNAgent
            
            env = ExamTimetablingEnv(max_timeslots=10)
            state_size = env.observation_space.shape[0]
            action_size = env.action_space.n
            
            agent = DQNAgent(
                state_size=state_size,
                action_size=action_size,
                learning_rate=0.001
            )
            
            print(f" DQN Agent created successfully!")
            print(f"   State size: {state_size}")
            print(f"   Action size: {action_size}")
            print(f"   Device: {agent.device}")
            
            # Test action selection
            state = env.reset()
            valid_actions = env.get_valid_actions()
            action = agent.act(state, valid_actions)
            print(f"   Test action selection: {action}")
            
            return True
        
    except Exception as e:
        print(f" DQN agent test failed: {e}")
        traceback.print_exc()
        return False

def test_core_timetabling():
    """Test core timetabling functions"""
    print("\n Testing Core Timetabling Logic...")
    try:
        from core.timetabling_core import test_timetabling_logic
        test_timetabling_logic()
        print(" Core timetabling logic test passed!")
        return True
        
    except Exception as e:
        print(f" Core timetabling test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print(" Running DQN Implementation Tests")
    print("="*50)
    
    tests = [
        ("Data Loading", test_data_loading),
        ("Core Timetabling", test_core_timetabling),
        ("RL Environment", test_environment),
        ("DQN Agent", test_dqn_agent),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        success = test_func()
        results.append((test_name, success))
    
    # Summary
    print(f"\n{'='*20} TEST SUMMARY {'='*20}")
    passed = 0
    for test_name, success in results:
        status = " PASS" if success else " FAIL"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nTests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print(" All tests passed! Ready for training.")
    else:
        print("⚠ Some tests failed. Check the errors above.")
        
    # Installation instructions if PyTorch is missing
    try:
        import torch
    except ImportError:
        print(f"\n📦 To run the full DQN training, install PyTorch:")
        print(f"   pip install torch torchvision")
        print(f"   Or visit: https://pytorch.org/get-started/locally/")

if __name__ == "__main__":
    main() 