import uvicorn

# Для разработки из-под виртуального окружения.
if __name__ == "__main__":
    uvicorn.run(
        "adapters.inbound.api.app.app:create_app",
        factory=True,
        reload=True,
        reload_dirs=["src"],
    )
