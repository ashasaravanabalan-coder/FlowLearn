"""Train, evaluate and save the Decision Tree logic classifier."""
import joblib, pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from features import FEATURES

df = pd.read_csv("dataset.csv")
X, y = df[FEATURES], df["label"]
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
clf = DecisionTreeClassifier(max_depth=8, min_samples_leaf=3, random_state=42).fit(X_tr, y_tr)
pred = clf.predict(X_te)
print("Accuracy:", round(accuracy_score(y_te, pred), 4))
print("5-fold CV:", cross_val_score(clf, X, y, cv=5).round(3))
print(classification_report(y_te, pred))
print(confusion_matrix(y_te, pred, labels=clf.classes_))
joblib.dump({"model": clf, "features": FEATURES}, "model.joblib")
print("Saved model.joblib")
