import pandas as pd
import pickle
import os

from sklearn.metrics import accuracy_score, classification_report

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEST_DATA_PATH = os.path.join(BASE_DIR, "dataset", "test_data.csv")
MODEL_PATH = os.path.join(BASE_DIR, "model", "disease_model.pkl")
SYMPTOMS_PATH = os.path.join(BASE_DIR, "model", "symptoms.pkl")


def evaluate():

    print("Loading test dataset...")
    df = pd.read_csv(TEST_DATA_PATH)

    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)

    with open(SYMPTOMS_PATH, "rb") as f:
        symptoms = pickle.load(f)

    print(f"Test data shape: {df.shape}")

    if "prognosis" not in df.columns:
        print("Error: prognosis column missing")
        return

    X_test = df.drop("prognosis", axis=1)
    y_test = df["prognosis"]

    # Normalize column names to match model expectations
    import re
    def normalize_col(col):
        s = col.strip().lower()
        s = re.sub(r'[\s_]+', '_', s)
        return s
    X_test.columns = [normalize_col(c) for c in X_test.columns]

    # Fix missing columns
    missing_cols = set(symptoms) - set(X_test.columns)

    if missing_cols:
        print(f"Warning: {len(missing_cols)} symptoms missing in test data, filling with 0")

        for col in missing_cols:
            X_test[col] = 0

    # Ensure correct order
    X_test = X_test[symptoms]

    print("Generating predictions...")

    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)

    print(f"\nAccuracy: {accuracy * 100:.2f}%")

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    # ---- TOP 3 ACCURACY ----

    probs = model.predict_proba(X_test)

    classes = model.classes_

    top3_correct = 0

    for i in range(len(y_test)):

        prob_row = probs[i]

        top3_idx = prob_row.argsort()[-3:]

        top3_labels = [classes[j] for j in top3_idx]

        if y_test.iloc[i] in top3_labels:
            top3_correct += 1

    top3_accuracy = top3_correct / len(y_test)

    print(f"\nTop-3 Accuracy: {top3_accuracy * 100:.2f}%")

    print("\nEvaluation completed.")


if __name__ == "__main__":
    evaluate()