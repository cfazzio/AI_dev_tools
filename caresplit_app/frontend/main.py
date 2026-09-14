"""CareSplit entry point: registers every page and starts the NiceGUI server."""

from nicegui import ui

from caresplit_frontend import pages  # noqa: F401  (registers @ui.page routes)

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="CareSplit", favicon="🩺", reload=False)
