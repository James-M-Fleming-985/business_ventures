"""Generated MVP tests run inside this server's environment, so it must be able to run them."""


def test_fastapi_testclient_works():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()

    @app.get("/ping")
    def ping():
        return {"ok": True}

    assert TestClient(app).get("/ping").json() == {"ok": True}
