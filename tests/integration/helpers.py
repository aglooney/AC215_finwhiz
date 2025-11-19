from uuid import uuid4

from fastapi import FastAPI, File, UploadFile


class ResponseAdapter:
    """Wrap FastAPI TestClient responses to mimic the requests.Response API used in the app."""

    def __init__(self, response):
        self._response = response
        self.status_code = response.status_code

    def json(self):
        return self._response.json()

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise RuntimeError(self._response.text)

    @property
    def text(self):
        return self._response.text


def build_agent_stub():
    """Spin up a lightweight FastAPI app that mimics the agent service."""
    app = FastAPI()
    state = {"sessions": {}, "documents": {}}

    @app.post("/sessions/")
    def create_session(payload: dict):
        session_id = str(uuid4())
        state["sessions"][session_id] = []
        state["documents"][session_id] = {"w2": [], "1099": []}
        return {"id": session_id}

    @app.post("/sessions/{session_id}/messages")
    def append_message(session_id: str, payload: dict):
        state["sessions"].setdefault(session_id, []).append({"role": payload["role"], "content": payload["content"]})
        return {"status": "ok"}

    async def _handle_upload(session_id: str, file: UploadFile, doc_type: str):
        data = await file.read()
        info = {"filename": file.filename, "size": len(data)}
        state["documents"].setdefault(session_id, {"w2": [], "1099": []})
        state["documents"][session_id][doc_type].append(info)
        return {"session_id": session_id, "document_type": doc_type, **info}

    @app.post("/sessions/{session_id}/w2")
    async def upload_w2(session_id: str, file: UploadFile = File(...)):
        return await _handle_upload(session_id, file, "w2")

    @app.post("/sessions/{session_id}/1099")
    async def upload_1099(session_id: str, file: UploadFile = File(...)):
        return await _handle_upload(session_id, file, "1099")

    @app.get("/sessions/{session_id}/context")
    def get_context(session_id: str):
        docs = state["documents"].get(session_id, {"w2": [], "1099": []})
        w2_fields = {}
        if docs["w2"]:
            last = docs["w2"][-1]
            w2_fields = {"filename": last["filename"], "filesize": last["size"]}
        f1099_fields = {}
        if docs["1099"]:
            last = docs["1099"][-1]
            f1099_fields = {"filename": last["filename"], "filesize": last["size"]}
        return {
            "recent_messages": state["sessions"].get(session_id, []),
            "w2_fields": w2_fields,
            "form1099_fields": f1099_fields,
            "portfolio_fields": {},
        }

    return app, state
