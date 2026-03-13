import pandas as pd
import os

train_path = r'c:\Users\anasf\OneDrive\Desktop\Smart-CDSS\dataset\training_data.csv'
test_path = r'c:\Users\anasf\OneDrive\Desktop\Smart-CDSS\dataset\test_data.csv'

def evaluate_dataset(path, name):
    if not os.path.exists(path):
        print(f"{name} not found at {path}")
        return
        
    print(f"--- Evaluating {name} ---")
    df = pd.read_csv(path)
    
    print(f"Shape: {df.shape}")
    
    null_counts = df.isnull().sum()
    total_nulls = null_counts.sum()
    print(f"Total Missing Values: {total_nulls}")
    if total_nulls > 0:
        print(null_counts[null_counts > 0])
        
    target_col = df.columns[-1]
    print(f"Target Column: '{target_col}'")
    
    if df[target_col].dtype == 'object':
        class_dist = df[target_col].value_counts()
        print(f"Number of classes: {len(class_dist)}")
        print("Class Distribution:")
        print(class_dist.head(10)) # Print top 10
        if len(class_dist) > 10:
            print(f"... and {len(class_dist) - 10} more classes.")
    print("\n")

evaluate_dataset(train_path, "Training Data")
evaluate_dataset(test_path, "Test Data")
