#!/usr/bin/env python3
"""
Test the fixed RL algorithms
"""
import sys
import os

# Add the current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

def test_dqn_fixed():
    """Test the fixed DQN algorithm"""
    print("🤖 Testing Fixed DQN Algorithm...")
    
    try:
        from app.algorithms_2.RL.DQN_optimizer import run_dqn_optimizer
        from app.algorithms_2.Data_Loading import activities_dict, groups_dict, spaces_dict, lecturers_dict, slots
        
        # Run with very minimal parameters for quick test
        print("Running DQN with minimal parameters...")
        best_schedule, metrics = run_dqn_optimizer(
            activities_dict=activities_dict,
            groups_dict=groups_dict,
            spaces_dict=spaces_dict,
            lecturers_dict=lecturers_dict,
            slots=slots,
            learning_rate=0.001,
            episodes=20,  # Small for testing
            epsilon=0.2
        )
        
        # Count assigned activities
        assigned_count = 0
        if best_schedule:
            for slot, space_dict in best_schedule.items():
                for space, activity in space_dict.items():
                    if activity is not None:
                        assigned_count += 1
        
        print(f"📊 DQN Result: {assigned_count} activities assigned")
        print(f"📈 Success rate: {assigned_count}/{len(activities_dict)} = {assigned_count/len(activities_dict)*100:.1f}%")
        
        return assigned_count > 0
        
    except Exception as e:
        print(f"❌ DQN test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sarsa_fixed():
    """Test the fixed SARSA algorithm"""
    print("\n🎯 Testing Fixed SARSA Algorithm...")
    
    try:
        from app.algorithms_2.RL.SARSA_optimizer import run_sarsa_optimizer
        from app.algorithms_2.Data_Loading import activities_dict, groups_dict, spaces_dict, lecturers_dict, slots
        
        # Run with very minimal parameters for quick test
        print("Running SARSA with minimal parameters...")
        best_schedule, metrics = run_sarsa_optimizer(
            activities_dict=activities_dict,
            groups_dict=groups_dict,
            spaces_dict=spaces_dict,
            lecturers_dict=lecturers_dict,
            slots=slots,
            learning_rate=0.001,
            episodes=20,  # Small for testing
            epsilon=0.2
        )
        
        # Count assigned activities
        assigned_count = 0
        if best_schedule:
            for slot, space_dict in best_schedule.items():
                for space, activity in space_dict.items():
                    if activity is not None:
                        assigned_count += 1
        
        print(f"📊 SARSA Result: {assigned_count} activities assigned")
        print(f"📈 Success rate: {assigned_count}/{len(activities_dict)} = {assigned_count/len(activities_dict)*100:.1f}%")
        
        return assigned_count > 0
        
    except Exception as e:
        print(f"❌ SARSA test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_implicit_q_fixed():
    """Test the fixed Implicit Q-Learning algorithm"""
    print("\n🧠 Testing Fixed Implicit Q-Learning Algorithm...")
    
    try:
        from app.algorithms_2.RL.ImplicitQlearning_optimizer import run_implicit_qlearning_optimizer
        from app.algorithms_2.Data_Loading import activities_dict, groups_dict, spaces_dict, lecturers_dict, slots
        
        # Run with very minimal parameters for quick test
        print("Running Implicit Q-Learning with minimal parameters...")
        best_schedule, metrics = run_implicit_qlearning_optimizer(
            activities_dict=activities_dict,
            groups_dict=groups_dict,
            spaces_dict=spaces_dict,
            lecturers_dict=lecturers_dict,
            slots=slots,
            episodes=20,  # Small for testing
            epsilon=0.2
        )
        
        # Count assigned activities
        assigned_count = 0
        if best_schedule:
            for slot, space_dict in best_schedule.items():
                for space, activity in space_dict.items():
                    if activity is not None:
                        assigned_count += 1
        
        print(f"📊 Implicit Q-Learning Result: {assigned_count} activities assigned")
        print(f"📈 Success rate: {assigned_count}/{len(activities_dict)} = {assigned_count/len(activities_dict)*100:.1f}%")
        
        return assigned_count > 0
        
    except Exception as e:
        print(f"❌ Implicit Q-Learning test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🚀 Testing Fixed RL Algorithms")
    print("=" * 50)
    
    # Test each algorithm
    dqn_ok = test_dqn_fixed()
    sarsa_ok = test_sarsa_fixed()
    implicit_q_ok = test_implicit_q_fixed()
    
    # Summary
    print("\n📊 Test Summary:")
    print("=" * 30)
    print(f"DQN Algorithm: {'✅ WORKING' if dqn_ok else '❌ FAILED'}")
    print(f"SARSA Algorithm: {'✅ WORKING' if sarsa_ok else '❌ FAILED'}")
    print(f"Implicit Q-Learning: {'✅ WORKING' if implicit_q_ok else '❌ FAILED'}")
    
    working_count = sum([dqn_ok, sarsa_ok, implicit_q_ok])
    print(f"\n🎯 Overall Result: {working_count}/3 algorithms working")
    
    if working_count == 3:
        print("🎉 All RL algorithms are now working correctly!")
    elif working_count > 0:
        print("✅ Some RL algorithms are working - partial success!")
    else:
        print("❌ All RL algorithms are still failing.")

if __name__ == "__main__":
    main() 