import pandas as pd
import os
import pickle

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score


def train_and_save_model(data_path, model_path, symptoms_path):

    try:

        print(f"Loading dataset from {data_path}...")
        df = pd.read_csv(data_path)

        # 1. Basic Cleaning
        # Remove unnamed column if exists
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
        
        # Remove duplicated column if it exists before normalization
        df = df.drop(columns=["fluid_overload.1"], errors="ignore")

        # 2. Robust Column Normalization
        import re
        def normalize_col(col):
            if col == 'prognosis': return col
            # Strip, lower, then replace any sequence of spaces/underscores with a single underscore
            s = col.strip().lower()
            s = re.sub(r'[\s_]+', '_', s)
            return s
            
        df.columns = [normalize_col(c) for c in df.columns]

        # 3. Handle Duplicate Columns (after normalization, some might merge)
        df = df.loc[:, ~df.columns.duplicated()]

        # Remove duplicate rows
        df.drop_duplicates(inplace=True)

        if "prognosis" not in df.columns:
            raise ValueError("Dataset must contain 'prognosis' column")

        # Split features and labels
        X = df.drop("prognosis", axis=1)
        y = df["prognosis"]

        symptoms = list(X.columns)

        print(f"Total features used: {len(symptoms)}")

        # Stratified split improves medical dataset training
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.2,
            stratify=y,
            random_state=42
        )

        print("Tuning Random Forest hyperparameters...")
        # Define a simplified grid for faster training while still improving accuracy
        param_grid = {
            'n_estimators': [100, 200, 300],
            'max_depth': [20, 50, None],
            'min_samples_split': [2, 5],
            'class_weight': ['balanced', 'balanced_subsample']
        }

        from sklearn.model_selection import GridSearchCV
        from sklearn.calibration import CalibratedClassifierCV
        from sklearn.metrics import classification_report

        rf_base = RandomForestClassifier(random_state=42)
        grid_search = GridSearchCV(
            estimator=rf_base,
            param_grid=param_grid,
            cv=3,
            n_jobs=-1,
            scoring='accuracy'
        )
        grid_search.fit(X_train, y_train)
        
        best_rf = grid_search.best_estimator_
        print(f"Best Parameters: {grid_search.best_params_}")

        print("Applying probability calibration...")
        # Calibrate the best RF model
        # Using sigmoid/isotonic for better probability estimates
        calibrated_clf = CalibratedClassifierCV(best_rf, method='sigmoid', cv=3)
        calibrated_clf.fit(X_train, y_train)

        # Evaluate
        y_pred = calibrated_clf.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"Model Accuracy (Calibrated): {accuracy * 100:.2f}%")
        print("\nFull Classification Report:")
        print(classification_report(y_test, y_pred))

        # Create model folder
        os.makedirs(os.path.dirname(model_path), exist_ok=True)

        # Save the calibrated model
        with open(model_path, "wb") as f:
            pickle.dump(calibrated_clf, f)

        print(f"Model saved -> {model_path}")

        # Save symptoms
        with open(symptoms_path, "wb") as f:
            pickle.dump(symptoms, f)

        print(f"Symptoms list saved -> {symptoms_path}")

    except Exception as e:
        print(f"Training error: {e}")


if __name__ == "__main__":

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    DATA_PATH = os.path.join(BASE_DIR, "dataset", "training_data.csv")

    MODEL_PATH = os.path.join(BASE_DIR, "model", "disease_model.pkl")

    SYMPTOMS_PATH = os.path.join(BASE_DIR, "model", "symptoms.pkl")

    train_and_save_model(DATA_PATH, MODEL_PATH, SYMPTOMS_PATH)