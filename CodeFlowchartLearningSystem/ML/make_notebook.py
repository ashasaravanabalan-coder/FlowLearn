import json
def md(s): return {"cell_type": "markdown", "metadata": {}, "source": s.splitlines(True)}
def code(s): return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": s.splitlines(True)}
cells = [
 md("# Programming Logic Classification (Decision Tree)\nPreprocessing, training and evaluation."),
 md("## 1. Build the dataset\nSnippets are generated from randomised templates; features are extracted by `features.py`."),
 code("import pandas as pd\nfrom generate_dataset import GENERATORS\nfrom features import extract_features, FEATURES\n\nrows = []\nfor label, gen in GENERATORS.items():\n    for _ in range(300):\n        c = gen()\n        rows.append({'code': c, **extract_features(c), 'label': label})\ndf = pd.DataFrame(rows).sample(frac=1, random_state=1).reset_index(drop=True)\ndf.to_csv('dataset.csv', index=False)\ndf.head()"),
 md("## 2. Preprocessing and encoding"),
 code("print(df.isna().sum().sum(), 'missing values')\nprint(df.label.value_counts())\nfrom sklearn.preprocessing import LabelEncoder\nle = LabelEncoder().fit(df.label)\ndf['label_encoded'] = le.transform(df.label)\ndf[FEATURES + ['label_encoded']].describe()"),
 md("## 3. Train the Decision Tree"),
 code("from sklearn.model_selection import train_test_split\nfrom sklearn.tree import DecisionTreeClassifier\nX, y = df[FEATURES], df['label']\nX_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)\nclf = DecisionTreeClassifier(max_depth=8, min_samples_leaf=3, random_state=42).fit(X_tr, y_tr)"),
 md("## 4. Evaluation"),
 code("from sklearn.metrics import accuracy_score, classification_report, ConfusionMatrixDisplay\nfrom sklearn.model_selection import cross_val_score\npred = clf.predict(X_te)\nprint('Accuracy:', accuracy_score(y_te, pred))\nprint('5-fold CV:', cross_val_score(clf, X, y, cv=5))\nprint(classification_report(y_te, pred))\nConfusionMatrixDisplay.from_predictions(y_te, pred, xticks_rotation=30)"),
 code("from sklearn.tree import plot_tree\nimport matplotlib.pyplot as plt\nplt.figure(figsize=(18, 8)); plot_tree(clf, feature_names=FEATURES, class_names=list(clf.classes_), filled=True, max_depth=3); plt.show()"),
 md("## 5. Save the model"),
 code("import joblib\njoblib.dump({'model': clf, 'features': FEATURES}, 'model.joblib')"),
]
nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}}, "nbformat": 4, "nbformat_minor": 5}
json.dump(nb, open("ML_Training.ipynb", "w"), indent=1)
