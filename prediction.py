import numpy as np
import torch
import torch.nn as nn
from itertools import product
import pickle
import os

# Model class (needed for loading)
class PostSaunaMLP(nn.Module):
	def __init__(self, input_size=6, hidden_size=64, output_size=3):
		super(PostSaunaMLP, self).__init__()
		self.fc1 = nn.Linear(input_size, hidden_size)
		self.fc2 = nn.Linear(hidden_size, hidden_size)
		self.fc3 = nn.Linear(hidden_size, output_size)
		self.relu = nn.ReLU()

	def forward(self, x):
		x = self.relu(self.fc1(x))
		x = self.relu(self.fc2(x))
		return self.fc3(x)

# Load function
def load_model_and_scalers(model_path='model.pth', scaler_X_path='scaler_X.pkl', scaler_y_path='scaler_y.pkl'):
	if not (os.path.exists(model_path) and os.path.exists(scaler_X_path) and os.path.exists(scaler_y_path)):
		raise FileNotFoundError("Saved model or scalers not found. Run train.py first.")
	model = PostSaunaMLP()
	model.load_state_dict(torch.load(model_path))
	model.eval()  # Set to evaluation mode
	with open(scaler_X_path, 'rb') as f:
		scaler_X = pickle.load(f)
	with open(scaler_y_path, 'rb') as f:
		scaler_y = pickle.load(f)
	print(f"Loaded model from {model_path} and scalers from {scaler_X_path}, {scaler_y_path}")
	return model, scaler_X, scaler_y

# Predict effects
def predict_effects(model, scaler_X, scaler_y, current_metrics, sauna_params):
	full_params = np.concatenate([current_metrics, sauna_params])
	params_scaled = scaler_X.transform(np.array([full_params]))
	pred_scaled = model(torch.tensor(params_scaled, dtype=torch.float32)).detach().numpy()
	pred = scaler_y.inverse_transform(pred_scaled)
	return pred[0]  # post_sleep, post_stress, post_readiness

# Tailor session
def tailor_sauna_session(model, scaler_X, scaler_y, current_metrics, user_needs='max_readiness', max_post_stress=5.0, min_post_sleep=80.0, min_post_readiness=85.0):
	def objective(sauna_params):
		pred = predict_effects(model, scaler_X, scaler_y, current_metrics, sauna_params)
		post_sleep, post_stress, post_readiness = pred
		penalty = 0
		if post_stress > max_post_stress:
			penalty += 1000 * (post_stress - max_post_stress)
		if post_sleep < min_post_sleep:
			penalty += 1000 * (min_post_sleep - post_sleep)
		if post_readiness < min_post_readiness:
			penalty += 1000 * (min_post_readiness - post_readiness)
		heat_load = sauna_params[0] + sauna_params[1]
		if heat_load > 120:
			penalty += 1000 * (heat_load - 120)
		return -post_readiness + penalty

	temp_range = np.arange(75, 96, 2)
	hum_range = np.arange(10, 36, 2.5)
	dur_range = np.arange(20, 91, 5)
	best_obj = np.inf
	best_params = None
	for temp, hum, dur in product(temp_range, hum_range, dur_range):
		sauna_params = np.array([temp, hum, dur])
		obj = objective(sauna_params)
		if obj < best_obj:
			best_obj = obj
			best_params = sauna_params
	pred = predict_effects(model, scaler_X, scaler_y, current_metrics, best_params)
	return tuple(best_params), pred[0], pred[1], pred[2]

# Main: Example inference
if __name__ == "__main__":
	model, scaler_X, scaler_y = load_model_and_scalers()
	# Mock data from OURA. User current state
	# current_metrics = [75, 7, 65]  # Sleep, Stress, Readiness
	current_metrics = [55, 9, 60]
	# current_metrics = [90, 2, 92]
	print(f"\nCurrent metrics: Sleep={current_metrics[0]}, Stress={current_metrics[1]}, Readiness={current_metrics[2]}")
	suggested_params, pred_post_sleep, pred_post_stress, pred_post_readiness = tailor_sauna_session(model, scaler_X, scaler_y, current_metrics)
	print(f"\nSuggested Session: Temp={suggested_params[0]:.1f}°C, Hum={suggested_params[1]:.1f}%, Dur={suggested_params[2]:.1f} min")
	print(f"Predicted outcomes: Sleep={pred_post_sleep:.1f}, Stress={pred_post_stress:.1f}, Readiness={pred_post_readiness:.1f}")
