# RAG Frontend

A React frontend for a Retrieval-Augmented Generation (RAG) chat assistant.

## Overview

This app provides a chat interface to query indexed documents through a backend RAG API. It supports:

- Multi-chat conversation history
- Local persistence using `localStorage`
- Adjustable top-K retrieval results
- Optional source display for responses
- Document statistics fetched from the backend
- Example questions to help get started quickly

## How It Works

The frontend sends requests to a backend API at:

`http://localhost:8000/api/v1/rag`

The main endpoints used are:

- `POST /api/v1/rag/ask` — send a user query and receive a generated answer
- `GET /api/v1/rag/stats` — fetch document index statistics

The UI stores chats locally, so conversations remain after refreshing the page.

## Requirements

- Node.js and npm installed
- A running backend service at `http://localhost:8000` with the `/api/v1/rag` routes available

## Installation

1. Open a terminal in this folder.
2. Install dependencies:

```bash
npm install
```

## Run Locally

Start the frontend app:

```bash
npm start
```

Then open `http://localhost:3000` in your browser.

## Build for Production

```bash
npm run build
```

The production-ready files will be created in the `build` folder.

## App Features

- `New chat` button to start a new conversation
- Chat history sidebar with delete support
- Toggle to show or hide retrieved sources
- Top-K input to control retrieval breadth
- Loading indicator while awaiting answers
- Example prompts for quick testing

## Notes

- The frontend is built with Create React App and React 19.
- If the backend API is hosted elsewhere, update `API_BASE_URL` in `src/App.js` accordingly.
- Chat history is saved in browser `localStorage` under the `ragChats` key.

## Project Structure

- `src/App.js` — main UI and application logic
- `src/index.js` — React app entry point
- `src/index.css` — global styling

## License

MIT
