import json, os
from functools import wraps
from pathlib import Path
from flask import Flask, g, jsonify, request
from itsdangerous import BadSignature, URLSafeTimedSerializer
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone
from pymongo.errors import DuplicateKeyError
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash

import classifier, llm
import db as mongo

FRONTEND = Path(__file__).resolve().parent.parent / "Frontend"
app = Flask(__name__, static_folder=str(FRONTEND), static_url_path="")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
signer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
mongo.init_indexes()


def auth(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        token = request.headers.get("Authorization", "").removeprefix("Bearer ")
        try:
            g.user_id = signer.loads(token, max_age=86400 * 7)["uid"]  # str(ObjectId)
        except BadSignature:
            return jsonify(error="Please log in again."), 401
        return fn(*a, **kw)
    return wrapper


def err(msg, code=400):
    return jsonify(error=msg), code


@app.errorhandler(Exception)
def handle_error(e):
    """Always answer with JSON so the UI can show the real error message."""
    if isinstance(e, HTTPException):
        return jsonify(error=e.description), e.code
    app.logger.exception(e)
    return jsonify(error=f"Server error: {e}"), 500


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.post("/api/register")
def register():
    d = request.get_json(force=True)
    u, p = (d.get("username") or "").strip(), d.get("password") or ""
    if len(u) < 3 or len(p) < 6:
        return err("Username needs 3+ characters and password 6+ characters.")
    try:
        res = mongo.users.insert_one({"username": u, "password_hash": generate_password_hash(p)})
    except DuplicateKeyError:
        return err("That username is taken.", 409)
    return jsonify(token=signer.dumps({"uid": str(res.inserted_id)}), username=u), 201


@app.post("/api/login")
def login():
    d = request.get_json(force=True)
    user = mongo.users.find_one({"username": (d.get("username") or "").strip()})
    if not user or not check_password_hash(user["password_hash"], d.get("password") or ""):
        return err("Wrong username or password.", 401)
    return jsonify(token=signer.dumps({"uid": str(user["_id"])}), username=user["username"])


@app.post("/api/classify")
@auth
def classify_route():
    code = (request.get_json(force=True).get("code") or "").strip()
    return jsonify(classifier.classify(code)) if code else err("Enter some code first.")


def _public(doc):
    doc["id"] = str(doc.pop("_id"))
    doc.pop("user_id", None)
    doc["created_at"] = doc["created_at"].isoformat()
    return doc


def _save(direction, language, source, result, analysis=None):
    doc = {"user_id": g.user_id, "direction": direction, "language": language, "source": source,
           "mermaid": result.get("mermaid"), "code": result.get("code"),
           "explanation": result.get("explanation", []), "summary": result.get("summary"),
           "logic_type": (analysis or {}).get("logic_type"), "confidence": (analysis or {}).get("confidence"),
           "created_at": datetime.now(timezone.utc).replace(tzinfo=None)}
    doc["_id"] = mongo.sessions.insert_one(doc).inserted_id
    return _public(doc)


@app.post("/api/code-to-flowchart")
@auth
def code_to_flowchart():
    d = request.get_json(force=True)
    code, lang = (d.get("code") or "").strip(), d.get("language", "python")
    if not code:
        return err("Enter some code first.")
    analysis = classifier.classify(code)  # ML result feeds the GenAI prompt
    try:
        result = llm.code_to_flowchart(code, lang, analysis)
    except llm.LLMError as e:
        return err(str(e), 502)
    return jsonify(_save("code_to_flow", lang, code, result, analysis))


@app.post("/api/flowchart-to-code")
@auth
def flowchart_to_code():
    d = request.get_json(force=True)
    flow, lang = (d.get("flowchart") or "").strip(), d.get("language", "python")
    if not flow:
        return err("Enter a flowchart first.")
    try:
        result = llm.flowchart_to_code(flow, lang)
    except llm.LLMError as e:
        return err(str(e), 502)
    analysis = classifier.classify(result.get("code", "")) if result.get("code") else None
    return jsonify(_save("flow_to_code", lang, flow, result, analysis))


@app.get("/api/sessions")
@auth
def sessions():
    rows = [_public(d) for d in mongo.sessions.find({"user_id": g.user_id}).sort("created_at", -1)]
    pipeline = [{"$match": {"user_id": g.user_id, "logic_type": {"$ne": None}}},
                {"$group": {"_id": "$logic_type", "n": {"$sum": 1}}}]
    stats = {r["_id"]: r["n"] for r in mongo.sessions.aggregate(pipeline)}
    return jsonify(sessions=rows, stats=stats)


@app.delete("/api/sessions/<sid>")
@auth
def delete_session(sid):
    try:
        res = mongo.sessions.delete_one({"_id": ObjectId(sid), "user_id": g.user_id})
    except InvalidId:
        return err("Invalid session id.")
    return ("", 204) if res.deleted_count else err("Session not found.", 404)


if __name__ == "__main__":
    app.run(debug=True, port=5000)