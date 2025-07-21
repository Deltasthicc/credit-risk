import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report
import joblib
df = pd.read_csv("C:\\Users\\Akshita\\Desktop\\project\\agents\\explainability_agent\\credit_data.csv")

X = df.drop("Defaulted", axis=1)
y = df["Defaulted"]

# Define categorical and numerical columns
categorical_features = ["Industry_Sector", "Country"]
numerical_features = [col for col in X.columns if col not in categorical_features]

# Preprocessing pipeline
preprocessor = ColumnTransformer([
    ("num", StandardScaler(), numerical_features),
    ("cat", OneHotEncoder(drop='first', sparse_output=False), categorical_features)
])

# Define the model pipeline
model_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", LogisticRegression(solver='liblinear', random_state=42))
])

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Fit the model
model_pipeline.fit(X_train, y_train)

# Evaluate
y_pred = model_pipeline.predict(X_test)
print(classification_report(y_test, y_pred))

# Save the model
joblib.dump(model_pipeline, "credit_risk_model.pkl")
print(" Model saved as credit_risk_model.pkl")

# Save the full preprocessed DataFrame (used later for SHAP)
df.to_csv("credit_data_clean.csv", index=False)
print(" Data saved as credit_data_clean.csv")
