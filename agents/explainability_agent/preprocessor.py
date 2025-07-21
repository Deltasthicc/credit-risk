import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier

# === Load dataset ===
data = pd.read_csv("C:\\Users\\Akshita\\Desktop\\project\\agents\\explainability_agent\\credit_data.csv")  # Replace with your actual dataset

# === Define features and target ===
X = data.drop("Defaulted", axis=1)  # Replace 'target' with actual column name
y = data["Defaulted"]

# === Feature types ===

num_features = ["Revenue", "Net_Income", "Total_Assets", "Total_Liabilities", "Equity"]
cat_features = ["Industry_Sector", "Country"]

preprocessor = ColumnTransformer(transformers=[
    ("num", StandardScaler(), num_features),
    ("cat", OneHotEncoder(handle_unknown='ignore'), cat_features)
])

pipeline = Pipeline(steps=[
    ("columntransformer", preprocessor),
    ("randomforestclassifier", RandomForestClassifier(random_state=42))
])

# === Train-test split (optional but recommended) ===
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# === Fit pipeline ===
pipeline.fit(X_train, y_train)

from sklearn.model_selection import cross_val_score
print("CV Accuracy:", cross_val_score(pipeline, X, y, cv=5).mean())
# === Save final pipeline ===
joblib.dump(pipeline, "C:/Users/Akshita/Desktop/project/agents/explainability_agent/final_pipeline.pkl")
print("Final pipeline saved successfully.")
