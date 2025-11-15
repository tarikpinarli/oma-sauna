# 🧖 Sauna Session Optimizer

An AI-powered sauna recommendation system that uses machine learning to predict and optimize post-sauna wellness outcomes based on your current physical state.

## 📋 Overview

This project uses a PyTorch neural network to predict how different sauna parameters (temperature, humidity, duration) will affect your wellness metrics (sleep quality, stress levels, readiness). The system then recommends optimal sauna settings tailored to your current condition.

## 🏗️ Architecture

```
┌─────────────────┐
│  Data Generator │ → Synthetic sauna session data
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ SQLite Database │ → Stores training data
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Model Training │ → PyTorch MLP (6→64→64→3)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Recommendation  │ → Optimization engine
│     Engine      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Supabase DB    │ → Stores recommendations
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Figma Frontend │ → User interface
└─────────────────┘
```

## 📂 Project Structure

```
sauna-optimizer/
├── data_generator.py          # Generates synthetic training data
├── train_model.py             # Trains the neural network
├── recommendation_engine.py   # Generates personalized recommendations
├── model.pth                  # Trained model weights
├── scaler_X.pkl              # Input feature scaler
├── scaler_y.pkl              # Output target scaler
├── database.db               # Training data storage
├── recommendation.db         # Recommendations storage
└── README.md                 # This file
```

## 🚀 Getting Started

### Prerequisites

```bash
pip install numpy pandas torch scikit-learn
```

### 1. Generate Training Data

```bash
python data_generator.py
```

This creates a SQLite database with 2,000 synthetic sauna sessions. The data generator simulates:
- Pre-sauna wellness metrics (sleep, stress, readiness)
- Sauna parameters (temperature, humidity, duration)
- Post-sauna wellness outcomes

### 2. Train the Model

```bash
python train_model.py
```

The training script:
- Loads data from `database.db`
- Trains a 3-layer MLP with 64 hidden units
- Uses 80/20 train/test split
- Trains for 500 epochs
- Saves model and scalers for inference

**Model Architecture:**
- Input: 6 features (pre-sleep, pre-stress, pre-readiness, avg_temp, avg_hum, duration)
- Hidden: 64 → 64 neurons with ReLU activation
- Output: 3 targets (post-sleep, post-stress, post-readiness)

### 3. Generate Recommendations

```bash
python recommendation_engine.py
```

The recommendation engine:
- Loads the trained model
- Takes current wellness metrics as input
- Searches optimal sauna parameters using grid search
- Applies constraints (max stress, min sleep/readiness)
- Saves recommendations to `recommendation.db`

## 🎯 How It Works

### Input Features
- **Pre-Sleep Score** (0-100): Current sleep quality
- **Pre-Stress Level** (0-10): Current stress level
- **Pre-Readiness Score** (0-100): Overall readiness/recovery
- **Temperature** (70-100°C): Sauna temperature
- **Humidity** (10-40%): Sauna humidity
- **Duration** (15-120 min): Session length

### Output Predictions
- **Post-Sleep Score**: Expected sleep quality after sauna
- **Post-Stress Level**: Expected stress level after sauna
- **Post-Readiness Score**: Expected readiness after sauna

### Optimization Strategy

The system uses constrained optimization to find the best sauna parameters:

1. **Grid Search**: Tests combinations of temp/humidity/duration
2. **Objective Function**: Maximizes post-readiness
3. **Constraints**:
   - Post-stress < 5.0
   - Post-sleep > 80.0
   - Post-readiness > 85.0
   - Heat load (temp + humidity) < 120

## 📊 Model Performance

Typical test set performance (MSE):
- Sleep Score: ~2-5 points
- Stress Level: ~0.5-1.0 points
- Readiness Score: ~2-5 points

## 🔗 Integration with Figma Frontend

The system integrates with a Figma-based frontend through Supabase:

1. **Frontend** displays user's current wellness state
2. **Backend** (this project) generates recommendations
3. **Recommendations** stored in Supabase database
4. **Figma** fetches and displays personalized sauna suggestions

### Current Implementation
- Uses hardcoded person state for testing
- Outputs recommendations to SQLite database
- Ready for Supabase integration

## 🎨 Data Generation Philosophy

The synthetic data generator creates realistic patterns:
- **Stress-dependent**: High stress requires gentler sessions
- **Readiness-dependent**: Low readiness limits duration tolerance
- **Sleep-dependent**: Sleep quality affects heat tolerance
- **Non-linear effects**: Optimal parameters vary by individual state

## 🔧 Configuration

### Model Hyperparameters
```python
hidden_size = 64        # Hidden layer size
num_epochs = 500        # Training epochs
batch_size = 16         # Batch size
learning_rate = 0.001   # Adam optimizer LR
```

### Recommendation Constraints
```python
max_post_stress = 5.0          # Maximum acceptable stress
min_post_sleep = 80.0          # Minimum target sleep score
min_post_readiness = 85.0      # Minimum target readiness
max_heat_load = 120            # Maximum temp + humidity
```

### Search Ranges
```python
temperature: 75-95°C (step: 2°C)
humidity: 10-35% (step: 2.5%)
duration: 20-90 min (step: 5 min)
```

## 🔮 Future Enhancements

- [ ] Real user data collection
- [ ] Integration with wearable devices (Oura Ring, Whoop, etc.)
- [ ] Real-time Supabase synchronization
- [ ] Multi-objective optimization
- [ ] User feedback loop for model improvement
- [ ] Session history tracking
- [ ] Progressive recommendations based on user experience
- [ ] A/B testing framework

## 📝 Example Usage

```python
from recommendation_engine import load_model_and_scalers, tailor_sauna_session

# Load model
model, scaler_X, scaler_y = load_model_and_scalers()

# Current state (sleep=75, stress=7, readiness=65)
current_metrics = [75, 7, 65]

# Get recommendation
suggested_params, post_sleep, post_stress, post_readiness = tailor_sauna_session(
    model, scaler_X, scaler_y, current_metrics
)

print(f"Recommended: {suggested_params[0]}°C, {suggested_params[1]}% humidity, {suggested_params[2]} min")
print(f"Expected outcomes: Sleep={post_sleep:.1f}, Stress={post_stress:.1f}, Readiness={post_readiness:.1f}")
```


---

**Built with:** PyTorch • NumPy • Pandas • scikit-learn • SQLite • Supabase • Figma
