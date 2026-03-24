import pickle
import os
import random
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

def train_dummy_models():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    models_dir = os.path.join(base_dir, 'models')
    os.makedirs(models_dir, exist_ok=True)

    crops = ['Rice', 'Wheat', 'Maize', 'Cotton', 'Sugarcane', 'Millets', 'Pulses', 'Mustard', 'Barley', 'Jute']
    
    # 1. Synthetic Crop Recommendation Model
    print("Generating synthetic crop data...")
    X_crop = []
    y_crop = []
    for _ in range(800):
        # Soil: 0: Red Sandy Loam, 1: Black Cotton, 2: Coastal Alluvial, 3: Laterite
        soil = random.randint(0, 3)
        # Season: 0: Kharif, 1: Rabi, 2: Zaid
        season = random.randint(0, 2)
        # Water: 0: Low, 1: Medium, 2: High
        water = random.randint(0, 2)
        
        # Injecting Realistic AP Logic
        if soil == 1:
            crop = 'Cotton' if water > 0 else 'Millets'
        elif soil == 2 and water == 2:
            crop = 'Rice'
        elif soil == 2 and water == 1:
            crop = 'Sugarcane'
        elif soil == 3:
            crop = random.choice(['Pulses', 'Millets'])
        elif soil == 0:
            crop = random.choice(['Maize', 'Pulses']) if water < 2 else 'Rice'
        elif water == 1 and season == 1:
            crop = 'Wheat'
        else:
            crop = random.choice(crops)
            
        X_crop.append([soil, season, water])
        y_crop.append(crop)
        
    crop_clf = RandomForestClassifier(n_estimators=15, min_samples_split=4, random_state=42)
    crop_clf.fit(X_crop, y_crop)
    crop_classes = crop_clf.classes_
    
    with open(os.path.join(models_dir, 'crop_model.pkl'), 'wb') as f:
        pickle.dump(crop_clf, f)

    with open(os.path.join(models_dir, 'crop_classes.pkl'), 'wb') as f:
        pickle.dump(crop_classes, f)

    # 2. Synthetic Price Prediction Model
    print("Generating synthetic price data...")
    X_price = []
    y_price = []
    
    for _ in range(1200):
        crop_idx = random.randint(0, len(crops) - 1)
        # Ensure we have data for all months evenly
        month = random.randint(1, 12)
        
        base_price = (crop_idx + 1) * 20
        # Give each crop a unique phase shift so its peak price happens in a different month!
        # crop_idx goes from 0 to 9. We shift the sine wave by `crop_idx` months.
        seasonality = np.sin((month - crop_idx) * np.pi / 6) * 1500
        price = (base_price * 100) + seasonality + random.uniform(-50, 50)
        
        X_price.append([crop_idx, month])
        y_price.append(price)
        
    price_reg = RandomForestRegressor(n_estimators=20, random_state=42)
    price_reg.fit(X_price, y_price)
    
    with open(os.path.join(models_dir, 'price_model.pkl'), 'wb') as f:
        pickle.dump(price_reg, f)
        
    with open(os.path.join(models_dir, 'price_crops.pkl'), 'wb') as f:
        pickle.dump(crops, f)

    print("Synthetic models trained and saved to models/")

if __name__ == '__main__':
    train_dummy_models()
