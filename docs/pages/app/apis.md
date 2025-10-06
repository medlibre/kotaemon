## Kotaemon APIs

### Overview
- **Purpose**: Reference for integrating with Kotaemon via FastAPI routes and Gradio events.
- **Scope**: HTTP routes (login, favicon, app mount) and Gradio event-driven APIs (chat, indexing, settings, setup, resources).

### HTTP Routes (FastAPI)
These routes are minimal; most functionality is exposed via Gradio events rather than REST.

- **sso_app.py** (Gradio with SSO)
  - **GET** `/favicon.ico`: Returns the Gradio favicon.
  - Gradio app mounted at **/app** using SSO middleware.
  - Auth provider via envs:
    - `AUTHENTICATION_METHOD` in {`KEYCLOAK`, `GOOGLE`}.
    - If `KEYCLOAK`: `KEYCLOAK_SERVER_URL`, `KEYCLOAK_REALM`, `KEYCLOAK_CLIENT_ID`, `KEYCLOAK_CLIENT_SECRET`.
    - Else (Google): `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`.

- **sso_app_demo.py** (demo OAuth without gradiologin)
  - **GET** `/`: Redirects to `/app/`.
  - **GET** `/favicon.ico`: Returns the Gradio favicon.
  - **GET** `/logout`: Clears session and redirects to `/`.
  - **GET** `/login`: Initiates Google OAuth, redirects to `/auth`.
  - **GET** `/auth`: Completes OAuth; stores user in session; redirects to `/`.
  - Gradio app mounted at **/app**.

- **app.py** (local launch)
  - Launches the Gradio `Blocks` UI directly; no extra REST routes beyond Gradio.

Notes:
- Static assets are served via Gradio `allowed_paths`.
- No additional FastAPI routers are defined in this repo; functional APIs are Gradio event handlers.

---

### Gradio Event API
Kotaemon exposes functionality through Gradio events bound to Python functions. You can subscribe to public events to integrate or extend behavior.

- **Event bus**
  - Declare: `BaseApp.declare_event(name: str)`
  - Subscribe: `BaseApp.subscribe_event(name: str, definition: dict)`
    - **definition** keys commonly used: `fn`, `inputs`, `outputs`, `show_progress`, `concurrency_limit`, `js`.
  - Access declared events to chain: `BaseApp.get_event(name)`

- **Built-in public events**
  - `onSignIn`: Fired after user login.
  - `onSignOut`: Fired on logout.
  - `onFirstSetupComplete`: Fired after first-time setup completes.
  - `onFileIndex{indexId}Changed`: Fired when files/groups change for a given index.

---

### Authentication
- LoginPage (if user management enabled)
  - Public events: `onSignIn`.
  - Handlers:
    - `login(username, password, request)` → `(user_id, usn_out, pwd_out)`.
    - Toggles visibility of login inputs on sign-in/out.

---

### Settings API
- SettingsPage
  - Public events: `onSignOut`.
  - Handlers:
    - `load_setting(user_id)` → `[settings_state, ...components]`.
    - `save_setting(user_id, *component_values)` → `settings_state`.
    - `change_reasoning_mode(value)` → visibility updates.
    - `change_password(user_id, password, password_confirm)`.
  - Subscribes to `onSignIn` to populate user settings.

---

### Chat API
- ChatPage
  - Submit:
    - `submit_msg(chat_input, chat_history, user_id, settings, conv_id, conv_name, first_selector_choices, request)`
      - Resolves file tags/URLs, manages conversation creation, returns UI/state updates.
  - Streamed reasoning:
    - `chat_fn(conversation_id, chat_history, settings, reasoning_type, llm_type, use_mind_map, use_citation, language, chat_state, command_state, user_id, *selecteds)`
      - Streams updated chat, info panel HTML, plot, and state.
  - Persistence:
    - `persist_data_source(convo_id, user_id, retrieval_msg, plot_data, retrieval_hist, plot_hist, messages, state, *selecteds)`
  - Utilities:
    - `suggest_chat_conv(settings, language, chat_history, use_suggestion)`
    - `check_and_suggest_name_conv(chat_history)`
    - `on_set_public_conversation(is_public, convo_id)`
  - Subscribes: `onSignIn` (reload history), `onSignOut` (clear state).

---

### File Index API (per index)
- FileIndexPage
  - Public events: `onFileIndex{indexId}Changed`.
  - Upload & Indexing:
    - `index_fn(files, urls, reindex, settings, user_id)` → streams per-file status; returns list of new IDs.
    - `index_fn_file_with_default_loaders(files, reindex, settings, user_id)` → `[ids]`.
    - `index_fn_url_with_default_loaders(urls, reindex, settings, user_id, request)` → `[ids]`.
  - Listing & Groups:
    - `list_file(user_id, name_pattern)` → `(list, DataFrame)`.
    - `list_file_names(file_list_state)` → `Dropdown.choices`.
    - `list_group(user_id, file_list_state)` → `(list, DataFrame)`.
    - `save_group(group_id, group_name, group_files, user_id)` → `group_id`.
    - `delete_group(group_id)`.
  - Item ops:
    - `file_selected(file_id)`; `delete_event(file_id)`; `download_single_file(...)`; `download_all_files()`.
- FileSelector (chat filtering)
  - `load_files(selector_value, user_id)` → `(selector update, options JSON)`.
  - `get_selected_ids(components)` → `list[str]`.
  - Subscribes: `onFileIndex{indexId}Changed`, `onSignIn`, `onSignOut`.

---

### Resources Tab (admin-only visibility)
- ResourcesTab toggles the `Users` tab visibility based on role on `onSignIn`/`onSignOut`.

---

### First-time Setup API
- SetupPage
  - Public events: `onFirstSetupComplete`.
  - `update_model(cohere_api_key, openai_api_key, google_api_key, ollama_model_name, ollama_emb_model_name, provider)` → streams setup logs; configures models and tests connectivity.
  - `update_default_settings(provider, settings_state)` → `settings_state`.
  - `switch_options_view(provider)` → visibility updates.

---

### Integration Snippets
- Launch locally (no SSO):
```python
from ktem.main import App
app = App()
demo = app.make()
demo.queue().launch(
    favicon_path=app._favicon,
    allowed_paths=["libs/ktem/ktem/assets"],
)
```

- Mount in FastAPI with SSO (OIDC/Google):
```python
from fastapi import FastAPI
import gradiologin as grlogin
from ktem.main import App

app = FastAPI()
demo = App().make()
# configure grlogin.register(...) per your provider
grlogin.mount_gradio_app(app, demo, "/app", allowed_paths=["libs/ktem/ktem/assets"])
```

- Subscribe to a public event:
```python
def greet(user_id):
    import gradio as gr
    return gr.update(value=f"Hi {user_id or 'guest'}!")

app.subscribe_event("onSignIn", {
    "fn": greet,
    "inputs": [app.user_id],
    "outputs": [some_markdown],
    "show_progress": "hidden",
})
```

### Environment Variables (selected)
- **SSO**: `AUTHENTICATION_METHOD`, `KEYCLOAK_SERVER_URL`, `KEYCLOAK_REALM`, `KEYCLOAK_CLIENT_ID`, `KEYCLOAK_CLIENT_SECRET`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`.
- **Gradio**: `GRADIO_TEMP_DIR` (defaults to `<KH_APP_DATA_DIR>/gradio_tmp`).
- **Demo/Features**: `KH_DEMO_MODE`, `KH_SSO_ENABLED`, `KH_ENABLE_FIRST_SETUP`.
- **Ollama**: `KH_OLLAMA_URL`.

### Notes
- This repo intentionally favors event-driven Gradio APIs over REST endpoints. For REST, consider wrapping these handlers behind your own FastAPI routes.
