import os
import pickle
import numpy as np
import datetime

# Load models and classes globally so they are only loaded once when the server starts.
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')

try:
    with open(os.path.join(MODELS_DIR, 'crop_model.pkl'), 'rb') as f:
        crop_model = pickle.load(f)
    with open(os.path.join(MODELS_DIR, 'crop_classes.pkl'), 'rb') as f:
        crop_classes = pickle.load(f)
        
    with open(os.path.join(MODELS_DIR, 'price_model.pkl'), 'rb') as f:
        price_model = pickle.load(f)
    with open(os.path.join(MODELS_DIR, 'price_crops.pkl'), 'rb') as f:
        price_crops = pickle.load(f)
        
except FileNotFoundError:
    print("WARNING: Model files not found. Please run 'python utils/train_models.py' first.")
    crop_model, crop_classes, price_model, price_crops = None, None, None, None

def recommend_crop(soil, season, water):
    """
    Predict top 3 crops based on inputs.
    """
    if crop_model is None:
        return [("Model not trained", 0)]
        
    # Input shape for the synthetic model: [[Soil, Season, Water]]
    features = np.array([[soil, season, water]])
    
    # Get probabilities for all classes
    probabilities = crop_model.predict_proba(features)[0]
    
    # Get indices of top 3 classes
    top_3_indices = np.argsort(probabilities)[::-1][:3]
    
    results = []
    for idx in top_3_indices:
        # Format: (Crop Name, Confidence Percentage)
        results.append((crop_classes[idx], round(probabilities[idx] * 100, 2)))
        
    return results

def predict_price_trend(crop_name):
    """
    Predict the price trend for the selected crop for the next 6 months.
    """
    if price_model is None or crop_name not in price_crops:
        return {'labels': [], 'prices': [], 'best_month': 'N/A', 'expected_price': 0}
        
    # Convert prediction to list to find the best month
    import numpy as np # already imported
    if isinstance(price_crops, np.ndarray):
        crop_idx = list(price_crops).index(crop_name)
    else:
        crop_idx = price_crops.index(crop_name)
    
    current_month = datetime.datetime.now().month
    
    months_to_predict = [(current_month + i - 1) % 12 + 1 for i in range(1, 7)]
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    trend_labels = [month_names[m-1] for m in months_to_predict]
    
    prices = []
    for month in months_to_predict:
        features = np.array([[crop_idx, month]])
        predicted_price = price_model.predict(features)[0]
        prices.append(round(predicted_price, 2))
        
    # Find the best month to sell
    max_price = max(prices)
    best_month_idx = prices.index(max_price)
    best_month = trend_labels[best_month_idx]
        
    return {
        'labels': trend_labels,
        'prices': prices,
        'best_month': best_month,
        'expected_price': max_price
    }
