import pandas as pd
import pickle
import os
from sklearn.metrics import accuracy_score, classification_report

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DATA_PATH = os.path.join(BASE_DIR, 'dataset', 'test_data.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'model', 'disease_model.pkl')
SYMPTOMS_PATH = os.path.join(BASE_DIR, 'model', 'symptoms.pkl')

def evaluate():
    print("Loading test dataset...")
    df = pd.read_csv(TEST_DATA_PATH)
    
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
        
    with open(SYMPTOMS_PATH, 'rb') as f:
        symptoms = pickle.load(f)
        
    print(f"Test data shape: {df.shape}")
    
    # Check if 'prognosis' exists
    if 'prognosis' not in df.columns:
        print("prognosis column missing")
        return
        
    X_test = df.drop('prognosis', axis=1)
    y_test = df['prognosis']
    
    # Check for missing columns
    missing_cols = set(symptoms) - set(X_test.columns)
    if missing_cols:
        print(f"Warning: {len(missing_cols)} symptoms missing in test data, filling with 0...")
        for col in missing_cols:
            X_test[col] = 0
            
    # Keep only the requested symptoms in the correct order
    X_test = X_test[symptoms]
    
    print("Generating predictions...")
    y_pred = model.predict(X_test)
    
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy on test_data.csv: {accuracy * 100:.2f}%")
    
    print("\nDetailed Report (Top 10 classes by frequency in test set):")
    # Just printing full classification report might be long, let's see.
    # print(classification_report(y_test, y_pred))

if __name__ == "__main__":
    evaluate()
