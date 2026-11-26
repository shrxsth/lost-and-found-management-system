# Campus Lost and Found

A small Python web app for reporting lost and found belongings on a campus. It lets people submit reports, browse and search reports, find possible matches, and mark items as returned.

## Run it

1. Install Python 3 if needed.
2. Open a terminal in this folder.
3. Run `py app.py` on Windows, or `python app.py` on macOS/Linux.
4. The app opens at <http://127.0.0.1:8000>.
5. Stop it with Ctrl+C in the terminal.

The app uses only Python's standard library; no packages need to be installed.

## Data and privacy

Reports are saved in `items.json` next to `app.py`. That file is ignored by Git so personal contact details and real reports stay on the computer and are not included in this repository. The app creates the file when the first report is saved.

This is a local school project. It has no sign-in or access controls and stores contact information as plain text, so it should not be put on a public server or used with real reports without adding appropriate privacy and security features.
