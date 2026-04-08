import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import pickle
import os

def train_and_save_model(data_path, model_path, symptoms_path):
    """
    Loads dataset, trains a Random Forest model, and saves the model and symptoms.
    """
    try:
        # Load the dataset
        print(f"Loading dataset from {data_path}...")
        df = pd.read_csv(data_path)
        
        # Check if prognosis column exists
        if 'prognosis' not in df.columns:
            raise ValueError("Dataset must contain a 'prognosis' column.")
            
        # Drop extraneous empty column caused by training data formatting
        if 'Unnamed: 133' in df.columns:
            df = df.drop('Unnamed: 133', axis=1)
            
        # Separate features (X) and labels (y)
        X = df.drop('prognosis', axis=1)
        y = df['prognosis']
        
        # Save the list of symptom columns to ensure feature order consistency during prediction
        symptoms = list(X.columns)
        print(f"Found {len(symptoms)} symptoms.")
        
        # Split data for evaluation (80% training, 20% testing)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Initialize and train the Random Forest Classifier with pruning and balancing
        print("Training Random Forest Classifier with hyperparameter tuning...")
        clf = RandomForestClassifier(
            n_estimators=200, 
            max_depth=50, 
            min_samples_split=5, 
            min_samples_leaf=2, 
            class_weight="balanced", 
            random_state=42
        )
        clf.fit(X_train, y_train)
        
        # Evaluate the model
        y_pred = clf.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Model trained successfully. Accuracy on test set: {accuracy * 100:.2f}%")
        
        # Ensure model directory exists
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # Save the trained model using pickle
        with open(model_path, 'wb') as f:
            pickle.dump(clf, f)
        print(f"Model saved to {model_path}")
        
        # Save the symptoms list to maintain consistent features for prediction
        with open(symptoms_path, 'wb') as f:
            pickle.dump(symptoms, f)
        print(f"Symptoms list saved to {symptoms_path}")
        
    except FileNotFoundError:
        print(f"Error: Dataset not found at {data_path}. Please place your CSV file there.")
    except Exception as e:
        print(f"An error occurred during training: {e}")

if __name__ == "__main__":
    # Define paths based on the required directory structure
    # BASE_DIR is the root of the Smart-CDSS project
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    DATA_PATH = os.path.join(BASE_DIR, 'dataset', 'training_data.csv')
    MODEL_PATH = os.path.join(BASE_DIR, 'model', 'disease_model.pkl')
    SYMPTOMS_PATH = os.path.join(BASE_DIR, 'model', 'symptoms.pkl')
    
    train_and_save_model(DATA_PATH, MODEL_PATH, SYMPTOMS_PATH)
