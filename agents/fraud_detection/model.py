import os
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report

# --- Load data ---
csv_path = "C:\\Users\\Akshita\\Desktop\\project\\agents\\fraud_detection\\fraud_detection_dataset.csv"
df = pd.read_csv(csv_path)

# --- Drop RecordID if present ---
if 'RecordID' in df.columns:
    df = df.drop(columns=['RecordID'])

# --- Features & Target ---
X = df.drop("Is_Fraud", axis=1)
y = df["Is_Fraud"]

# --- Identify column types ---
numeric_features = ["Revenue", "Net_Income", "Total_Assets", "Total_Liabilities", "Equity"]
categorical_features = ["Industry_Sector", "Country"]

# --- Preprocessing ---
preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numeric_features),
        ("cat", OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ]
)

# --- Pipeline ---
pipeline = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("classifier", RandomForestClassifier(n_estimators=100, random_state=42))
])

# --- Train/test split ---
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# --- Train model ---
pipeline.fit(X_train, y_train)

# --- Evaluate ---
y_pred = pipeline.predict(X_test)
print("\n Classification Report:")
print(classification_report(y_test, y_pred))

# --- Save model ---
model_path = "agents/fraud_detection/fraud_model.joblib"
joblib.dump(pipeline, model_path)
print(f"\n Model saved at: {model_path}")
