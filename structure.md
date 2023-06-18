```
app/             # Source code of the application
   - api/          # Primary adapter (i.e. all-FastAPI related stuff)
   - domain/       # Business-logic — core
       - deps/       # Dependencies (interfaces) that business logic rely on

   - main.py       # Composition root (wiring all dependencies and starting the app)
```
