import pickle
import pandas as pd
import os

_model = None
_symptoms = None


def load_resources(model_path, symptoms_path):

    global _model, _symptoms

    try:

        if _model is None:
            with open(model_path, "rb") as f:
                _model = pickle.load(f)

        if _symptoms is None:
            with open(symptoms_path, "rb") as f:
                _symptoms = pickle.load(f)

        return True

    except Exception as e:
        print(f"Error loading model: {e}")
        return False


def predict_disease(user_symptoms, age=None, gender=None,
                    model_path=None, symptoms_path=None):

    global _model, _symptoms

    if model_path and symptoms_path:
        success = load_resources(model_path, symptoms_path)

        if not success:
            return {"error": "Failed to load model"}

    if _model is None or _symptoms is None:
        return {"error": "Model not initialized"}

    try:

        # Initialize feature vector
        input_data = {symptom: 0 for symptom in _symptoms}

        # Activate symptoms
        import re
        from difflib import get_close_matches

        # Create a list of symptom-only keys (excluding age/gender features) for fuzzy matching
        symptom_features = [s for s in _symptoms if not (s.startswith("age_") or s.startswith("gender_"))]

        for symptom in user_symptoms:

            # Normalize: strip, lower, and replace any sequence of spaces/underscores with a single underscore
            symptom = symptom.strip().lower()
            symptom = re.sub(r'[\s_]+', '_', symptom)

            if symptom in input_data:
                input_data[symptom] = 1
            else:
                # Fuzzy matching fallback
                matches = get_close_matches(symptom, symptom_features, n=1, cutoff=0.7)
                if matches:
                    matched_symptom = matches[0]
                    input_data[matched_symptom] = 1
                    print(f"Matched: '{symptom}' -> '{matched_symptom}'")
                else:
                    print(f"Warning: '{symptom}' not recognized")

        # Set age feature
        if age:

            age_key = f"age_{age.lower()}"

            if age_key in input_data:
                input_data[age_key] = 1

        # Set gender feature
        if gender:

            gender_key = f"gender_{gender.lower()}"

            if gender_key in input_data:
                input_data[gender_key] = 1

        # Convert to DataFrame
        input_df = pd.DataFrame([input_data])

        # Ensure column order matches training
        input_df = input_df[_symptoms]

        # Predict
        prediction = _model.predict(input_df)[0]

        probs = _model.predict_proba(input_df)[0]

        classes = _model.classes_

        results = []

        for i in range(len(classes)):
            results.append({
                "disease": classes[i],
                "probability": round(probs[i] * 100, 2)
            })

        results = sorted(results, key=lambda x: x["probability"], reverse=True)

        return {
            "prediction": results[0]["disease"],
            "top_predictions": results[:3]
        }

    except Exception as e:

        return {"error": str(e)}


if __name__ == "__main__":

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    MODEL_PATH = os.path.join(BASE_DIR, "model", "disease_model.pkl")

    SYMPTOMS_PATH = os.path.join(BASE_DIR, "model", "symptoms.pkl")

    sample_symptoms = [
        "itching",
        "skin_rash",
        "nodal_skin_eruptions"
    ]

    result = predict_disease(
        user_symptoms=sample_symptoms,
        age="adult",
        gender="male",
        model_path=MODEL_PATH,
        symptoms_path=SYMPTOMS_PATH
    )

    print(result)