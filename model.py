from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import pandas as pd

# Load your dataset
data = pd.read_csv("league_players.csv")

# Selecting relevant columns
data = data[['match_weighted_average(%)', 'match_result']]

# Check for missing values
print(data.isnull().sum())

# Split the data into features (X) and target variable (y)
X = data[['match_weighted_average(%)']]
y = data['match_result']

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Build the logistic regression model
model = LogisticRegression()
model.fit(X_train, y_train)

# Predictions
y_pred = model.predict(X_test)

# Evaluate the model
print("Accuracy:", accuracy_score(y_test, y_pred))
print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))
print("Classification Report:\n", classification_report(y_test, y_pred))