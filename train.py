import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score
import joblib

df = pd.read_csv('mydata.csv')

X = df.drop(['gameId', 'blueWins'], axis=1)
y = df['blueWins']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Naive Bayes
classifier = GaussianNB()

classifier.fit(X_train, y_train)

# Save model
model_file = 'naive_bayes_model.joblib'
joblib.dump(classifier, model_file)

y_pred = classifier.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)
print(f'Accuracy: {accuracy * 100:.2f}%')
