# Deep Q-Network (DQN) for STA83 Exam Timetabling

This folder contains the DQN implementation for solving the STA83 exam timetabling problem using reinforcement learning.

## Files Overview

### Core Implementation
- `environment.py` - RL environment for sequential exam timetabling
- `agent.py` - DQN agent with neural networks and experience replay
- `train.py` - Main training script with optimized hyperparameters
- `test.py` - Test script to verify implementation works

### Utilities
- `monitor.py` - Monitor training progress in real-time
- `demo.py` - Educational demonstration of DQN learning process

## Quick Start

### 1. Test Implementation
```bash
python rl/test.py
```
Verifies that all components work correctly.

### 2. Train DQN Agent
```bash
python rl/train.py
```
Trains the DQN agent with optimized hyperparameters. Results saved to timestamped directory.

### 3. Monitor Training (Optional)
```bash
python rl/monitor.py live
```
Monitor training progress in real-time during long training runs.

### 4. See Learning Demo
```bash
python rl/demo.py
```
Watch a short demonstration of how the DQN agent learns.

## Training Configuration

The training script uses optimized hyperparameters:
- **Environment**: 28 timeslots (prevents "no valid actions")
- **Learning Rate**: 0.0003 (stable learning)
- **Buffer Size**: 20,000 (diverse experience replay)
- **Batch Size**: 64 (stable gradients)
- **Target Update**: Every 50 steps
- **Early Stopping**: At 80% rolling success rate

## Expected Results

- **Training Time**: 4-6 minutes to reach 80%+ success rate
- **Solution Quality**: 15-20 timeslots typically
- **Success Rate**: 80-100% on evaluation
- **Inference Speed**: <1 second per solution

## Dependencies

- PyTorch (for neural networks)
- NumPy (for numerical operations)
- Matplotlib (for plotting results)
- Gym (for RL environment interface)

## Integration

The DQN agent integrates with the core timetabling system:
- Uses `core.sta83_data_loader` for data loading
- Uses `core.timetabling_core` for conflict detection
- Outputs same format as NSGA-II for comparison 