# NeuralChat Implementation Doc

## 1. Project Summary

NeuralChat is a local LLM chatbot built with Streamlit for the UI, MongoDB for persistent storage, and Ollama for model inference. The app supports user registration and login, keeps chat history per user, and sends recent conversation context to the model so replies stay coherent across turns.

## 2. Architecture

The application follows a simple three-layer design:

- `app.py` initializes Streamlit, loads session defaults, and routes users to login or chat.
- `ui/auth.py` handles registration, login, and session state changes.
- `ui/chat.py` renders the chat interface, loads history, submits prompts, streams model responses, and handles stop/retry behavior.
- `db.py` provides MongoDB helpers for users, messages, and statistics.
- `ollama_client.py` wraps the Ollama REST API for both normal and streaming responses.
- `styles.py` injects the custom UI styling.

## 3. Authentication Flow

Authentication is handled with hashed passwords and MongoDB-backed user records.

1. A user registers with a username and password.
2. The password is hashed using SHA-256 before storage.
3. MongoDB enforces unique usernames through an index.
4. On login, the provided password is hashed again and compared with the stored hash.
5. When authentication succeeds, Streamlit session state is updated with `logged_in`, `username`, and page flags.

## 4. Chat Flow

The chat page works in a few stages:

1. The app loads the current user’s history from MongoDB.
2. Historical messages are rendered first so the conversation appears continuous.
3. When the user submits a prompt, it is stored in session state as `pending_prompt`.
4. The prompt is saved to MongoDB as a user message.
5. The last `OLLAMA_CONTEXT_TURNS` messages are sent to Ollama together with the new prompt.
6. The assistant reply is streamed back into the UI.
7. The final response is saved in MongoDB.

## 5. Stop / Partial Response Handling

The chat interface supports stopping generation mid-response.

- A stop button is rendered before streaming begins.
- While the stream is active, the code checks a stop flag frequently.
- If the user stops generation, the stream closes and the partial answer is preserved as a broken response.
- Partial assistant replies are stored with a distinct role so they are shown differently in the UI.
- Stopped replies are excluded from the next model prompt, so incomplete text is not reused as context.

## 6. Data Storage

MongoDB stores two main collections:

### Users

Stores the account identity and hashed credentials.

Fields:

- `username`
- `password_hash`
- `created_at`

### Messages

Stores every chat turn per user.

Fields:

- `username`
- `role`
- `content`
- `timestamp`

The timestamp is stored in UTC so the chat history can be displayed consistently.

## 7. Model Integration

Ollama is accessed through `requests` using the `/api/chat` endpoint.

- Non-streaming requests are available for basic response handling.
- Streaming requests are used in the chat UI so the assistant starts appearing immediately.
- The model name and endpoint are controlled from `config.py`.

## 8. Configuration

Important configuration values are centralized in `config.py`.

- `OLLAMA_URL` points to the local Ollama server.
- `OLLAMA_MODEL` selects the model name.
- `OLLAMA_TIMEOUT_SECONDS` defines the request timeout.
- `OLLAMA_CONTEXT_TURNS` controls how much history is sent with each prompt.

## 9. UI Behavior

The interface is fully Streamlit-based and uses custom layout blocks for a chat-style experience.

- The sidebar shows login status, stats, recent history, and sign out.
- The main pane renders the conversation in order.
- The input area uses a Streamlit form so Enter and the send button both submit reliably.
- Custom styling in `styles.py` provides the dark theme and message bubbles.

## 10. Setup And Run

1. Install Python dependencies with `pip install -r requirements.txt`.
2. Start MongoDB.
3. Start Ollama and pull the model with `ollama serve` and `ollama pull mistral`.
4. Launch the app with `streamlit run app.py`.

## 11. Implementation Notes

- The app is designed to work locally with no cloud dependency.
- Conversation history is restored per user on login.
- Context-aware prompts make the conversation feel continuous.
- Partial responses are intentionally kept separate so stopping generation does not corrupt later prompts.
