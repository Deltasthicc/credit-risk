import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

# === STEP 1: Load Data ===
df = pd.read_csv("C:/Users/Akshita/Desktop/project/agents/credit_scoring/data.csv")

feature_cols = [
    "credit_util_ratio",
    "eps_basic",
    "eps_diluted",
    "avg_monthly_income",
    "cash_and_equivalents",
    "high_utilization_flag"
]
X = df[feature_cols]
y = df["defaulted"]

# === STEP 2: Split Data ===
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# === STEP 3: Train Model ===
model = LogisticRegression()
model.fit(X_train, y_train)

# === STEP 4: Evaluate Model ===
y_pred = model.predict(X_test)
print("Classification Report:\n")
print(classification_report(y_test, y_pred))

# === STEP 5: Save Model and Feature Order ===
joblib.dump(model, "credit_scoring_model.joblib")
print("Model saved as credit_scoring_model.joblib")

with open("features.txt", "w") as f:
    f.write(",".join(feature_cols))
print("Feature order saved as features.txt")