import pickle
import pandas as pd
import os

# Global variables to hold the loaded model and symptoms list in memory
# Useful for API deployments (e.g., Flask) where we only want to load once
_model = None
_symptoms = None

def load_resources(model_path, symptoms_path):
    """
    Loads the trained model and symptom list from disk.
    This can be called once when the Flask API starts.
    """
    global _model, _symptoms
    try:
        if _model is None:
            with open(model_path, 'rb') as f:
                _model = pickle.load(f)
        if _symptoms is None:
            with open(symptoms_path, 'rb') as f:
                _symptoms = pickle.load(f)
        return True
    except FileNotFoundError as e:
        print(f"Error loading resources: {e}. Please ensure the model is trained first.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred while loading resources: {e}")
        return False

def predict_disease(user_symptoms, age=None, gender=None, model_path=None, symptoms_path=None):
    """
    Predicts the probable disease based on a list of symptoms, age, and gender.
    
    Args:
        user_symptoms (list): A list of symptom names present in the user.
        age (str): The age group (child, teenager, adult, senior).
        gender (str): The gender (male, female, other).
        model_path (str): Path to the trained model pickle file.
        symptoms_path (str): Path to the symptoms list pickle file.
        
    Returns:
        dict: A dictionary containing the predicted disease and top probabilities, or an error response.
    """
    global _model, _symptoms
    
    # Check and load resources if paths are provided
    if model_path and symptoms_path:
        success = load_resources(model_path, symptoms_path)
        if not success:
            return {"error": "Failed to load model or symptoms data."}
            
    # Ensure model and symptoms are available before predicting
    if _model is None or _symptoms is None:
        return {"error": "Model or symptoms data not loaded. Please initialize paths."}
        
    try:
        # 1. Create a dictionary initialized with 0 for all known symptoms
        input_data = {symptom: 0 for symptom in _symptoms}
        
        # 2. Set the value to 1 for symptoms provided by the user
        for symptom in user_symptoms:
            if symptom in input_data:
                input_data[symptom] = 1
            else:
                # Warning for symptoms not seen during training
                print(f"Warning: Symptom '{symptom}' is not recognized by the model and will be ignored.")
                
        # 3. Set the age feature if available
        if age:
            age_key = f"age_{age.lower()}"
            if age_key in input_data:
                input_data[age_key] = 1
                
        # 4. Set the gender feature if available
        if gender:
            gender_key = f"gender_{gender.lower()}"
            if gender_key in input_data:
                input_data[gender_key] = 1
                
        # 3. Convert the dictionary to a DataFrame to maintain feature order and structure
        input_df = pd.DataFrame([input_data])
        
        # 4. Ensure the column order matches exactly what the model was trained on
        input_df = input_df[_symptoms]
        
        # 5. Predict the disease
        prediction = _model.predict(input_df)
        
        # 6. Calculate prediction probabilities
        probabilities = _model.predict_proba(input_df)[0]
        classes = _model.classes_
        
        # Pair classes with probabilities and sort them
        prob_dict = {classes[i]: float(probabilities[i]) for i in range(len(classes))}
        sorted_probs = sorted(prob_dict.items(), key=lambda x: x[1], reverse=True)
        
        # Get top 3 predictions that have > 0 probability
        top_predictions = [{"disease": dp[0], "probability": round(dp[1] * 100, 2)} for dp in sorted_probs[:3] if dp[1] > 0]
        
        # Check if model's highest confidence is extremely low
        if not top_predictions or top_predictions[0]["probability"] < 15.0:
            return {"error": "Insufficient symptoms provided for an accurate diagnosis. The model's confidence is too low. Please add more specific symptoms so the AI can distinguish the exact condition."}
        
        # Return the predicted prognosis (disease) and probabilities
        return {
            "prediction": sorted_probs[0][0], # Ensure it matches top prob
            "top_predictions": top_predictions
        }
        
    except Exception as e:
        return {"error": f"An error occurred during prediction: {e}"}

if __name__ == "__main__":
    # Define paths based on the required directory structure
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MODEL_PATH = os.path.join(BASE_DIR, 'model', 'disease_model.pkl')
    SYMPTOMS_PATH = os.path.join(BASE_DIR, 'model', 'symptoms.pkl')
    
    # Example test code simulating an API request
    sample_symptoms = ['itching', 'skin_rash', 'nodal_skin_eruptions']
    
    print(f"Diagnosing based on sample symptoms: {sample_symptoms}")
    result = predict_disease(sample_symptoms, MODEL_PATH, SYMPTOMS_PATH)
    
    if isinstance(result, dict) and "error" in result:
        print(result["error"])
    else:
        print(f"Predicted Disease: {result['prediction']}")
        print(f"Top Probabilities: {result['top_predictions']}")
