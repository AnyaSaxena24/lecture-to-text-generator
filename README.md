# Lecture to Text Generator & Study Assistant

An intelligent, full-stack application designed to transform audio and video lectures into rich learning materials. The system transcribes audio using **local OpenAI Whisper** (via Hugging Face Transformers) and automatically generates dynamic structured summaries, notes, interactive flashcards, and quizzes.

---

## 🚀 Key Features

- **Audio/Video Lecture Processing**: Support for uploading video and audio formats.
- **Local Whisper Transcription**: Automatic speech-to-text running fully locally on your machine.
- **Dynamic AI Study Aids**:
  - **Structured Summaries & Bullet Notes**: Core concepts distilled from the transcript.
  - **Interactive Flashcards**: Test yourself on key terminology and concepts.
  - **Self-Assessment Quizzes**: Auto-generated multiple-choice questions with instant feedback.
- **User Authentication**: Secure signup and login flow to save and manage your personal lecture catalog.
- **Interactive Dashboard**: Modern UI/UX built with TailwindCSS for easy navigation, filtering, and studying.
- **Local Database Mode**: Seamless database fallback using local JSON files so no external database connection is required.

---

## 🛠️ Technology Stack

- **Frontend**:
  - [Next.js](https://nextjs.org/) (App Router, TypeScript)
  - [TailwindCSS](https://tailwindcss.com/) (Styling & Modern UI)
- **Backend**:
  - [FastAPI](https://fastapi.tiangolo.com/) (Python REST API)
  - [PyTorch](https://pytorch.org/) & [Transformers](https://huggingface.co/docs/transformers/index) (Whisper transcription model)
- **Database**:
  - Local JSON database file storage with fallback capabilities. Supports MongoDB as well.

---

## ⚙️ Prerequisites

Before you start, make sure you have the following installed:
1. **Node.js** (v18+) & **npm**
2. **Python** (v3.10+)
3. **FFmpeg** (Required for audio/video conversion and Whisper processing)
   - *Windows*: Can be installed via `winget install Gyan.FFmpeg` or downloaded directly.
   - *macOS*: `brew install ffmpeg`
   - *Linux*: `sudo apt install ffmpeg`

---

## 🔧 Local Installation & Setup

### 1. Clone & Set Up Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables. Create/edit `backend/.env`:
   ```env
   # Database Configuration (leave empty to use local JSON file database fallback)
   MONGODB_URL=
   JWT_SECRET=supersecretkeychangeinproduction
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   
   # Models Configuration
   # Set to "small" or "tiny" for local CPU-friendly Whisper transcription
   WHISPER_MODEL=small
   # Set to "mock" for local offline generator that uses actual transcripts
   LLM_PROVIDER=mock
   ```
5. Run the FastAPI development server:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   The backend API documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

### 2. Set Up Frontend

1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Configure environment variables. Create/edit `frontend/.env.local`:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
4. Start the frontend development server:
   ```bash
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000) in your web browser.

---

## 📖 How to Use

1. **Sign Up/Login**: Create a user account on the dashboard.
2. **Upload Lecture**: Upload an audio or video file of your choice.
3. **Processing**: Wait for Whisper to transcribe the audio (CPU processing may take a minute or two depending on file length).
4. **Study**:
   - Read the generated transcript and dynamic notes.
   - Switch to **Flashcards** to review questions and answers.
   - Take the auto-generated **Quiz** to assess your understanding.
