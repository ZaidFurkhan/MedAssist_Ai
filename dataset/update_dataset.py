import pandas as pd
import numpy as np
import os

def augment_dataset(file_path):
    print(f"Augmenting {file_path}...")
    df = pd.read_csv(file_path)
    
    # Drop existing synthetic columns if they somehow exist to prevent duplication
    cols_to_drop = ['age_child', 'age_teenager', 'age_adult', 'age_senior', 'gender_male', 'gender_female', 'gender_other']
    df = df.drop(columns=[col for col in cols_to_drop if col in df.columns], errors='ignore')

    # Generate random age groups
    # Probabilities leaning slightly towards adults and seniors for diseases
    age_groups = np.random.choice(
        ['age_child', 'age_teenager', 'age_adult', 'age_senior'], 
        size=len(df), 
        p=[0.1, 0.15, 0.45, 0.3]
    )
    
    # Generate random genders
    genders = np.random.choice(
        ['gender_male', 'gender_female', 'gender_other'], 
        size=len(df), 
        p=[0.48, 0.48, 0.04]
    )

    # Initialize all new columns to 0
    for col in cols_to_drop:
        df[col] = 0

    # Set 1 based on the random choice
    for idx, (age, gender) in enumerate(zip(age_groups, genders)):
        df.at[idx, age] = 1
        df.at[idx, gender] = 1

    # Ensure prognosis is the last column
    prognosis = df.pop('prognosis')
    df['prognosis'] = prognosis

    # Overwrite the original file
    df.to_csv(file_path, index=False)
    print(f"Successfully augmented {file_path} with age and gender columns.")

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    training_path = os.path.join(BASE_DIR, 'dataset', 'training_data.csv')
    test_path = os.path.join(BASE_DIR, 'dataset', 'test_data.csv')
    
    augment_dataset(training_path)
    # Augment test data as well if it exists
    if os.path.exists(test_path):
        augment_dataset(test_path)
