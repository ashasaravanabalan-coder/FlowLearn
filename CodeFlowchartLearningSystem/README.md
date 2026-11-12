# FlowLearn: AI-Enhanced Code & Flowchart Learning System

## 1. Project Overview

FlowLearn is a full-stack educational web application that helps students understand program logic.

**Code to Flowchart:** paste code and get a flowchart, a step-by-step explanation and an algorithm summary.
**Flowchart to Code:** paste a flowchart (Mermaid syntax or plain steps) and get working code in the chosen language.
**Logic classification:** a Decision Tree model classifies code as Sequential, Conditional, Looping, Nested or Function-Based.
**Learning history:** every conversion is saved to the user's account, with a dashboard of past sessions and logic-type counts.

**How the modules connect**

1. The user submits code. The backend extracts numeric features and the Decision Tree predicts the logic type.
2. The ML result is added to the LLM prompt, so the AI knows what kind of code it is explaining.
3. The LLM returns a flowchart, explanation and summary. The backend saves them to MongoDB and the browser draws the flowchart.
4. In the reverse direction, the LLM generates code from a flowchart and the classifier labels the generated code.

No ML or AI output is hardcoded. The logic type comes from `model.joblib`; flowcharts, code and explanations come from a live LLM API call.

## 2. Technologies Used

Frontend - HTML, CSS, JavaScript, CodeMirror (editor), Mermaid (flowchart rendering) 
Backend - Python 3.10+, Flask
Database - MongoDB
Machine Learning - scikit-learn (Decision Tree), pandas, joblib, Jupyter 
Generative AI  LLM API: Google Gemini

## 3. Project Structure

```
CodeFlowchartLearningSystem/
├── Frontend/
│   ├── index.html          page layout
│   ├── style.css           styling
│   └── app.js              login, editor, API calls, flowchart drawing, history
├── Backend/
│   ├── app.py              Flask routes (auth, conversion, sessions)
│   ├── classifier.py       loads the model and predicts logic type
│   ├── llm.py              prompts, LLM API calls, response parsing
│   ├── db.py               MongoDB connection
│   ├── requirements.txt
├── ML/
│   ├── features.py         feature extraction (shared by training and backend)
│   ├── generate_dataset.py builds dataset.csv
│   ├── train_model.py      trains, evaluates and saves the model
│   ├── ML_Training.ipynb   notebook: preprocessing, training, evaluation
│   ├── dataset.csv
│   └── model.joblib        saved Decision Tree
├── README.md


## 4. Setup Instructions

**Prerequisites**

- Python 3.10 or newer
- MongoDB Community Server (or a free MongoDB Atlas cluster)
- A modern browser (Chrome, Edge or Firefox) with internet access, because CodeMirror and Mermaid load from a CDN
- One LLM API key (see section 8)

**Install dependencies**

Extract the ZIP, then open a terminal in the `CodeFlowchartLearningSystem` folder:

```
pip install -r Backend/requirements.txt
```

## 5. Database Setup (MongoDB)

1. Install and start MongoDB.
   - Windows: MongoDB Server runs as a service. Check `services.msc` for "MongoDB Server" with status Running.
   - macOS/Linux: run `mongod`, or start the service.
2. Check the connection with MongoDB Compass: connect to `mongodb://localhost:27017`.
3. No manual setup is needed. The app creates the database and indexes on first start.


For MongoDB Atlas, set `MONGO_URI` to your `mongodb+srv://...` string. Allow your IP under Network Access.

**Collections**

- `users`: `username` (unique), `password_hash` (passwords are never stored in plain text)
- `sessions`: `user_id`, `direction`, `language`, `source`, `mermaid`, `code`, `explanation`, `summary`, `logic_type`, `confidence`, `created_at`

## 6. Steps to Run the Backend

**Windows (PowerShell)**

```
cd Backend
copy run.ps1.example run.ps1
notepad run.ps1        # paste your API key, save, close
.\run.ps1
```

If PowerShell blocks the script, run `Set-ExecutionPolicy -Scope Process Bypass` once and try again.

**Or set variables manually (Windows PowerShell)**

```
cd Backend
$env:LLM_PROVIDER="gemini"
$env:GEMINI_API_KEY="your-key"
$env:MONGO_URI="mongodb://localhost:27017"
python app.py


When you see `Running on http://127.0.0.1:5000`, the server is ready. Keep the terminal open. Stop it with `Ctrl + C`.

The server runs with `debug=False`, so restart it after changing backend code.

## 7. Steps to Run the Frontend

The Flask backend serves the frontend files, so no separate frontend server is needed.

1. Start the backend (section 6).
2. Open **http://localhost:5000** in your browser.
3. Click **Create an account**, enter a username, password and confirm password, then register.
4. Paste code in **Code to flowchart** and click **Generate flowchart**.
5. Try **Flowchart to code** and the **History** tab.

Do not open `index.html` directly from the folder. The API calls need the backend URL. After editing frontend files, refresh with `Ctrl + Shift + R`.

## 8. GenAI / API Key Instructions

The app needs **one** LLM API key. Choose a provider with the `LLM_PROVIDER` variable.

| Provider | `LLM_PROVIDER` | Key variable | Model variable (default) | Get a key |
|---|---|---|---|---|
| Google Gemini | `gemini` | `GEMINI_API_KEY` | `GEMINI_MODEL` (`gemini-3.5-flash-lite`) | https://aistudio.google.com/apikey |
| Groq | `groq` | `GROQ_API_KEY` | `GROQ_MODEL` (`llama-3.3-70b-versatile`) | https://console.groq.com |
| Anthropic | `anthropic` | `ANTHROPIC_API_KEY` | `ANTHROPIC_MODEL` | https://console.anthropic.com |

- If `LLM_PROVIDER` is not set, the app uses whichever key it finds (Groq, then Gemini, then Anthropic).
- **Never commit or submit your API key.** Keep it in `run.ps1` or environment variables only, and delete `run.ps1` before zipping.
- The model asks the LLM for a fixed plain-text format (`===MERMAID===`, `===EXPLANATION===`, `===SUMMARY===`), which `llm.py` parses.

## 9. ML Model Details

- **Task:** classify code logic as Sequential, Conditional, Looping, Nested or Function-Based.
- **Algorithm:** Decision Tree (`DecisionTreeClassifier`, `max_depth=8`, `min_samples_leaf=3`).
- **Input features** (extracted by `ML/features.py`):
  - number of conditions (`if`, `elif`, `case`)
  - loop count (`for`, `while`)
  - function usage (`def`, `function`)
  - code length (non-empty lines)
  - operators used
  - complexity level (1 + conditions + loops + logical operators)
  - maximum nesting depth of control blocks
- **Dataset:** 1,500 snippets (300 per class), generated from randomised templates by `generate_dataset.py`. Features are computed from the code, not typed by hand.
- **Preprocessing:** missing-value check, label encoding, stratified 80/20 train/test split.
- **Evaluation:** accuracy, 5-fold cross-validation, classification report and confusion matrix.
- **Result:** about 100% test accuracy. This is high because the dataset is synthetic and labels come from the same templates that generated the code. Accuracy on real student code would be lower.
- **Saved model:** `ML/model.joblib`, loaded by the backend at startup.
- **Limitation:** the classifier is tuned for Python-style code.

**Retrain the model** (also removes any scikit-learn version warning):

```
cd ML
python generate_dataset.py
python train_model.py
```

Or open `ML_Training.ipynb` from inside the `ML` folder and choose Run All.

## 10. API Endpoints

| Endpoint | Purpose |
|---|---|
| `POST /api/register`, `POST /api/login` | Create an account, log in, receive a token |
| `POST /api/classify` | Classify code logic |
| `POST /api/code-to-flowchart` | Classify, generate flowchart, steps and summary, save session |
| `POST /api/flowchart-to-code` | Generate code from a flowchart, classify it, save session |
| `GET /api/sessions` | List history and logic-type counts |
| `DELETE /api/sessions/<id>` | Delete a session |

All endpoints except register and login need a `Bearer` token.

## 11. Troubleshooting

| Problem | Fix |
|---|---|
| `Could not open requirements file` | Run the command from inside `CodeFlowchartLearningSystem`, not a parent folder. |
| Server stops at start with a MongoDB timeout | MongoDB is not running. Start it and check `MONGO_URI`. |
| `GEMINI_API_KEY is not set` (or another provider) | Set the key in the same terminal before `python app.py`. |
| `Gemini API error 403` | Google denied access to that key's project. Create a key in a new project with a personal Google account, or switch to Groq. |
| `Gemini API error 404` | Model name unavailable. Set `GEMINI_MODEL` to a model your key lists. |
| `That username is taken.` | The account exists. Log in, or use another username. |
| Flowchart does not draw | The AI returned invalid Mermaid. Click Generate again. |
| `InconsistentVersionWarning` | Retrain the model with `python train_model.py` inside `ML`. |