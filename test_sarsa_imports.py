#!/usr/bin/env python3
"""
Test script to check SARSA imports
"""

print("Testing SARSA imports...")

try:
    print("1. Testing PyTorch import...")
    import torch
    print(f"   ✅ PyTorch version: {torch.__version__}")
    
    print("2. Testing SARSA environment import...")
    from app.exams.rl.sarsa_environment import ExamTimetablingSARSAEnv
    print("   ✅ SARSA Environment import successful!")
    
    print("3. Testing SARSA agent import...")
    from app.exams.rl.sarsa_agent import SARSAAgent
    print("   ✅ SARSA Agent import successful!")
    
    print("4. Testing environment creation...")
    env = ExamTimetablingSARSAEnv(max_timeslots=18)
    print(f"   ✅ Environment created successfully!")
    print(f"   📊 State size: {env.observation_space.shape[0]}")
    print(f"   🎯 Action size: {env.action_space.n}")
    
    print("\n🎉 All SARSA imports and basic functionality working!")
    
except ImportError as e:
    print(f"   ❌ ImportError: {e}")
    print("   This explains why SARSA is showing 'PyTorch required' error")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc() 