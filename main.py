from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
import models, database
import requests
import re
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pydantic import BaseModel, Field
app = FastAPI(title="O&M Account Management Portal")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

headers = {
    "Authorization": "Bearer HC3AW5E-6B84YVK-NNAERWR-AX8TWGY",
    "Content-Type": "application/json"
}

# Configuration
ANYTHING_LLM_URL = "https://nastily-saddled-probe.ngrok-free.dev/api/generate"
API_KEY = "HC3AW5E-6B84YVK-NNAERWR-AX8TWGY"

LOCAL_EXPRESS_CACHE = {
    "hotline": "The emergency IT support hotline is 555-0199.",
    "portal link": "The self-service unfreeze portal is located at http://construction.om.portal/unfreeze"
}

if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
#  'create_all' is  used to build  tables
models.Base.metadata.create_all(bind=database.engine)


# --- 1. CREATE: Add new O&M personnel  ---
@app.post("/accounts/", tags=["Personnel Management"])
def create_account(employee_id: str, name: str, dept: str, db: Session = Depends(database.get_db)):
    # Check if ID already exists
    db_user = db.query(models.OMAccount).filter(models.OMAccount.employee_id == employee_id).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Employee ID already registered")

    new_user = models.OMAccount(
        employee_id=employee_id,
        full_name=name,
        department=dept,
        password="default_password_123"
    )
    db.add(new_user)
    db.commit()
    return {"message": f"Account for {name} created successfully"}


# --- 2. READ: Query/Search for accounts  ---
@app.get("/accounts/", tags=["Personnel Management"])
def query_accounts(dept: str = None, db: Session = Depends(database.get_db)):
    query = db.query(models.OMAccount)
    if dept:
        query = query.filter(models.OMAccount.department == dept)
    return query.all()


# --- 3. UPDATE: Modify personnel details  ---
@app.put("/accounts/{emp_id}", tags=["Personnel Management"])
def update_account(emp_id: str, new_name: str, db: Session = Depends(database.get_db)):
    user = db.query(models.OMAccount).filter(models.OMAccount.employee_id == emp_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Personnel not found")
    user.full_name = new_name
    db.commit()
    return {"message": "Account details updated"}


# --- 4. DELETE: Freeze/Deactivate account  ---
@app.delete("/accounts/{emp_id}", tags=["Personnel Management"])
def freeze_account(emp_id: str, db: Session = Depends(database.get_db)):
    user = db.query(models.OMAccount).filter(models.OMAccount.employee_id == emp_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Personnel not found")
    user.is_active = False
    db.commit()
    return {"message": f"Account {emp_id} has been frozen"}


# --- 5. ISSUE RECORDING: The "Smart Loop" Foundation  ---
@app.post("/record-issue/", tags=["Smart Feedback Loop"])
def log_unanswered_query(query: str, db: Session = Depends(database.get_db)):
    new_issue = models.IssueRecord(user_query=query, is_unanswered=True)
    db.add(new_issue)
    db.commit()
    return {"status": "Issue recorded for human O&M intervention"}

# view recorded issues
@app.get("/issues/", tags=["Smart Feedback Loop"])
def get_recorded_issues(db: Session = Depends(database.get_db)):
    return db.query(models.IssueRecord).order_by(models.IssueRecord.id.desc()).all()

# AI ASK
ANYTHING_LLM_API_KEY =  "HC3AW5E-6B84YVK-NNAERWR-AX8TWGY".strip().replace(" ", "") # Paste your generated key
ANYTHING_LLM_URL = "https://nastily-saddled-probe.ngrok-free.dev/api/generate"
ANYTHING_LLM_BASE_URL = "http://localhost:8888/api/v1"
WORKSPACE_SLUG = "oandm"

class PortalQueryModel(BaseModel):
    user_query: str

def call_anything_llm_api(query: str) -> str:
    url = f"http://localhost:8888/api/v1/workspace/{WORKSPACE_SLUG}/chat"
    headers = {
        "Authorization": f"Bearer {ANYTHING_LLM_API_KEY}",
        "X-Api-Key": ANYTHING_LLM_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "message": query,
        "mode": "query"
    }

    try:
        print(f"🔵 FastAPI is attempting to hit workspace chat: {url}")
        try:
            response = requests.post(ANYTHING_LLM_URL, json=payload, headers=headers)
            if response.status_code == 200:
                res_data = response.json()
                ai_answer = res_data.get("textResponse") or res_data.get("text") or ""
                return ai_answer.strip()
            else:
                return None
        except Exception as e:
            return None

    except Exception as e:
            print(f"🔴 Chat API execution failed: {e}")
            return "I do not know. System connection error."

def ask_ai(question: str):
    """Sends a question to AnythingLLM and returns the AI response."""
    headers = {
        "Authorization": f"Bearer {ANYTHING_LLM_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "message": question,
        "mode": "query"  # 'query' ensures it uses O&M PDFs
    }

    try:
        response = requests.post(ANYTHING_LLM_URL, json=payload, headers=headers)
        clean_answer = response.json().get("textResponse", "").strip()
        return clean_answer
    except Exception as e:
        return f"Error connecting to AI: {str(e)}"

def sync_to_ai_knowledge_base(question, solution):
    """
    Automatically updates the AnythingLLM knowledge base with the human-provided solution.
    """
    url = f"{ANYTHING_LLM_BASE_URL}/workspace/{WORKSPACE_SLUG}/update-embeddings"
    headers = {
        "Authorization": f"Bearer {ANYTHING_LLM_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "textContent": f"Question: {question} \nSolution: {solution}",
        "metadata": {"source": "human_intervention"}
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error syncing to AI: {e}")
        return False

class PortalQuery(BaseModel):
    user_question: str = Field(..., validation_alias="user_query")

def record_unanswered_issue_in_db(db: Session, user_query: str):
    """
    Saves the unaswered question to the local SQLite database so O&M personnel can review it during manual intervention.
    """
    new_issue = models.IssueRecord(
        user_query=user_query,
        is_unanswered=True,
        human_solution=None  # Left blank until a human resolves it later
    )
    db.add(new_issue)
    db.commit()
    db.refresh(new_issue)
    print(f"--> [Guardrail Logged] Issue added to SQLite with ID: {new_issue.id}")

class QueryRequest(BaseModel):
    user_query: str


def fetch_context_from_workspace(user_query: str) -> str:
    retrieval_url = f"http://127.0.0.1:8888/api/v1/workspace/oandm/query"

    headers = {
        "Authorization": f"Bearer {ANYTHING_LLM_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {"text": user_query}

    try:
        response = requests.post(retrieval_url, json=payload, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()
            context_chunks = data.get("context", [])
            return "\n\n".join([c.get("text", "") for c in context_chunks])
        else:
            return ""
    except Exception as e:
        print(f"Retrieval error: {e}")
        return ""


@app.post("/query-portal/")
def intelligent_query_router(payload: PortalQueryModel, db: Session = Depends(get_db)):
    user_query = payload.user_query.strip()
    context_data = fetch_context_from_workspace(user_query)
    augmented_prompt = f"Context from O&M Manual: {context_data}\n\nQuestion: {user_query}"

    ollama_payload = {
        "model": "llama3.2",
        "prompt": augmented_prompt,
        "stream": False
    }
    ollama_url = "https://nastily-saddled-probe.ngrok-free.dev//api/generate"
    try:
        response = requests.post(ollama_url, json=ollama_payload, timeout=60)
        if response.status_code == 200:
            ai_answer = response.json().get("response", "No response generated.")
            return {"status": "Success", "answer": ai_answer}
        else:
            return {"status": "Error", "answer": f"Ollama returned {response.status_code}"}
    except Exception as e:
        return {"status": "Error", "answer": str(e)}
    # Step 4: Return result

@app.get("/issues/")
@app.get("/issues/")
def get_unanswered_issues(db: Session = Depends(get_db)):
    return db.query(models.IssueRecord).filter(models.IssueRecord.is_unanswered == True).order_by(models.IssueRecord.id.desc()).all()
@app.put("/resolve-issue/{issue_id}")
def resolve_issue(issue_id: int, human_answer: str, db: Session = Depends(get_db)):
    issue = db.query(models.IssueRecord).filter(models.IssueRecord.id == issue_id).first()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue Record missing from schema.")

    issue.human_solution = human_answer
    issue.is_answered = True
    db.commit()
    sync_url = f"{ANYTHING_LLM_BASE_URL}/workspaces/{WORKSPACE_SLUG}/update-embeddings"
    headers = {
        "Authorization": f"Bearer {ANYTHING_LLM_API_KEY}",
        "Content-Type": "application/json"
    }
    sync_payload = {
        "adds": [
            {
                "textContent": f"Question: {issue.user_query} \nAnswer: {human_answer}",
                "metadata": {"source": "manual_intervention_hub", "issue_id": str(issue_id)}
            }
        ],
        "deletes": []
    }

    try:
        sync_res = requests.post(sync_url, json=sync_payload, headers=headers, timeout=15)
        if sync_res.status_code == 200:
            return {"status": "Success", "detail": "Knowledge base loop synced cleanly."}
        else:
            return {"status": "Partial Success", "detail": "Local DB resolved, Vector cache updated manually."}
    except Exception as e:
        return {"status": "Partial Success", "detail": f"Database updated locally, sync connection timed out: {e}"}
@app.post("/sync-knowledge/")
def sync_knowledge_base_folder():
    """
    Scans the local trainData/ folder and programmatically uploads
    and embeds all files into the active AnythingLLM workspace.
    """
    folder_path = "./trainData"

    if not os.path.exists(folder_path):
        raise HTTPException(status_code=404, detail="Local trainData folder not found.")

    uploaded_documents = []
    unified_headers = {
        "Authorization": f"Bearer {ANYTHING_LLM_API_KEY}",
        "Content-Type": "application/json"
    }
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)

        if os.path.isfile(file_path):
            print(f"--> Initializing upload pipeline for: {file_name}")
            upload_url = f"{ANYTHING_LLM_BASE_URL}/documents/upload"

            upload_headers = {"Authorization": f"Bearer {ANYTHING_LLM_API_KEY}"}

            with open(file_path, "rb") as f:
                files = {"file": (file_name, f, "application/octet-stream")}
                try:
                    upload_response = requests.post(upload_url, headers=upload_headers, files=files, timeout=30)
                    if upload_response.status_code != 200:
                        print(f"Failed to process storage layer for {file_name} - {upload_response.text}")
                        continue

                    response_json = upload_response.json()
                    documents_list = response_json.get("documents", [])

                    if documents_list:
                        doc_location = documents_list[0].get("location")
                        if doc_location:
                            uploaded_documents.append(doc_location)
                            print(f"--> Staged location reference: {doc_location}")

                except requests.exceptions.RequestException as e:
                    print(f"Network error handling document allocation: {e}")
                    continue

    if not uploaded_documents:
        return {"status": "Complete", "message": "No new valid files found to sync."}

    sync_url = f"{ANYTHING_LLM_BASE_URL}/workspaces/{WORKSPACE_SLUG}/update-embeddings"

    sync_payload = {
        "adds": uploaded_documents,
        "deletes": []
    }

    try:
        sync_response = requests.post(sync_url, json=sync_payload, headers=unified_headers, timeout=60)

        if sync_response.status_code == 200:
            return {
                "status": "Success",
                "synchronized_files": os.listdir(folder_path),
                "message": f"Successfully injected and vectorized {len(uploaded_documents)} multi-source files."
            }
        else:
            print(f"Sync Rejection Details: {sync_response.status_code} - {sync_response.text}")
            raise HTTPException(status_code=500,
                                detail="Vector tracking sync assignment rejected by AnythingLLM backend.")

    except requests.exceptions.RequestException:
        raise HTTPException(status_code=500,
                            detail="Connection timeout during multi-source vector embedding generation.")
    
@app.post("/force-deep-sync/")
def force_deep_sync_pipeline():
    """
    Automated Modular Data Pipeline.
    Cleans authorization layers, loops through local 'trainData' disk files,
    and programmatically updates workspace vector mappings.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    folder_path = os.path.join(current_dir, "trainData")

    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
        return {"status": "Directory Created", "detail": f"Initialized folder structure at: {folder_path}"}

    file_list = os.listdir(folder_path)
    if len(file_list) == 0:
        raise HTTPException(status_code=400,
                            detail="The directory 'trainData' is empty. Place your text/log files inside.")

    documents_to_pin = []
    base_url_clean = ANYTHING_LLM_BASE_URL.rstrip('/')
    upload_url = f"{base_url_clean}/document/upload"

    upload_headers = {
        "Authorization": f"Bearer {ANYTHING_LLM_API_KEY}"
    }

    print(f"--> Debugging Handshake. Token Length: {len(ANYTHING_LLM_API_KEY)} characters.")
    print(f"--> Targeting API Gateway URL: {upload_url}")

    for file_name in file_list:
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):
            try:
                with open(file_path, "rb") as file_bytes:
                    # Packaging the payload dynamically to prevent stream drops
                    files_payload = {
                        "file": (file_name, file_bytes, "text/plain")
                    }

                    res = requests.post(
                        upload_url,
                        headers=upload_headers,
                        files=files_payload,
                        timeout=30
                    )

                    print(f"--> File: '{file_name}' | Response Status Code: {res.status_code}")

                    if res.status_code == 200:
                        doc_location = res.json().get("documents", [{}])[0].get("location")
                        if doc_location:
                            documents_to_pin.append(doc_location)
                            print(f"--> Upload Accepted: {doc_location}")
                    else:
                        # Will capture raw server insights to terminal console
                        print(f"--> Storage Rejection Response: {res.text}")

            except Exception as e:
                print(f"--> Hardware IO stream loop break: {e}")
                continue

    if not documents_to_pin:
        raise HTTPException(
            status_code=401,
            detail=f"Token handshake rejected by AnythingLLM storage manager. Raw status caught during loop. Check terminal code logs."
        )

    print(f"--> Initializing embedding synchronization for workspace slug: '{WORKSPACE_SLUG}'...")
    sync_url = f"{base_url_clean}/workspace/{WORKSPACE_SLUG}/update-embeddings"
    sync_payload = {
        "adds": documents_to_pin,
        "deletes": []
    }

    try:
        sync_res = requests.post(
            sync_url,
            json=sync_payload,
            headers={"Authorization": f"Bearer {ANYTHING_LLM_API_KEY}", "Content-Type": "application/json"},
            timeout=120
        )
        if sync_res.status_code == 200:
            response_data = sync_res.json()

            documents_list = response_data.get("documents", [])

            if documents_list:
                server_side_location = documents_list[0].get("location")

                if server_side_location:
                    documents_to_pin.append(server_side_location)
                    print(f"--> Ingestion Map Linked: {server_side_location}")
                    return {"status": "Success", "detail": "Knowledge Base Synchronized Successfully"}
        else:
            raise HTTPException(status_code=500, detail=f"Embedding synchronization failed: {sync_res.text}")
    except requests.exceptions.RequestException as err:
        raise HTTPException(status_code=504,
                            detail=f"The vector process encountered a hardware timeout on your CPU: {err}")


