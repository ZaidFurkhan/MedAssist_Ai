import os
import pickle
import pandas as pd
from ml.predict import predict_disease

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'model', 'disease_model.pkl')
SYMPTOMS_PATH = os.path.join(BASE_DIR, 'model', 'symptoms.pkl')

print("Testing with 1 symptom: itching")
print(predict_disease(['itching'], MODEL_PATH, SYMPTOMS_PATH))

print("Testing with 1 symptom: cough")
print(predict_disease(['cough'], MODEL_PATH, SYMPTOMS_PATH))

print("Testing with 1 symptom: skin_rash")
print(predict_disease(['skin_rash'], MODEL_PATH, SYMPTOMS_PATH))

print("Testing with 1 symptom: continuous_sneezing")
print(predict_disease(['continuous_sneezing'], MODEL_PATH, SYMPTOMS_PATH))

print("Testing with 2 symptoms: cough, high_fever")
print(predict_disease(['cough', 'high_fever'], MODEL_PATH, SYMPTOMS_PATH))

print("Testing with 2 symptoms: vomiting, headache")
print(predict_disease(['vomiting', 'headache'], MODEL_PATH, SYMPTOMS_PATH))
