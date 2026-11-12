def main() -> None:
    import uvicorn

    from agent_runtime.config import get_settings

    settings = get_settings()
    uvicorn.run(
        "agent_runtime.api.app:create_app",
        factory=True,
        host=settings.api_host,
        port=settings.api_port,
    )
