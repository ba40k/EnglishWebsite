# 🌟 English Learning Platform

A **stunning, modern** FastAPI-based English learning platform with AI-powered features via OpenRouter.

✨ **Beautiful UI** • 🤖 **AI-Powered** • 🎨 **Modern Design** • 📱 **Responsive**

---

## 🎨 Design Highlights

This platform features a **professional, modern design** with:
- 🌈 **Beautiful purple gradient theme** throughout
- ✨ **Smooth animations** on all interactions
- 💳 **Card-based layouts** with depth and shadows
- 🎯 **Intuitive navigation** with sticky header
- 📱 **Fully responsive** for all devices
- 🎪 **Interactive elements** that respond to user actions

See [DESIGN.md](DESIGN.md) for complete design documentation.

---

## ✨ Features

### 🎨 **Beautiful Modern Design**
- Stunning purple gradient theme
- Smooth animations and transitions
- Card-based responsive layout
- Professional UI/UX design
- Interactive hover effects

### 📚 **Core Features**
- 📝 **Articles** - Create and read English learning articles with comments
- 📚 **Collections** - Organize articles into themed collections
- 🧪 **Tests** - Take interactive multiple-choice tests
- 💬 **Comments** - Engage with the community

### 🤖 **AI-Powered Learning**
- **Auto-generated summaries** for every article
- **Vocabulary extraction** with definitions
- **Ask AI anything** - Interactive Q&A about articles
- **Detailed explanations** - AI feedback on test answers
- Powered by Google Gemini 2.5 Flash via OpenRouter

## Setup

### 1. Install Dependencies

```bash
pip install -r requirments.txt
```

### 2. Configure OpenRouter API Key

1. Get your API key from [OpenRouter](https://openrouter.ai/)
2. Edit the `.env` file in the project root:

```bash
OPENROUTER_API_KEY=your_actual_api_key_here
```

### 3. Run the Application

```bash
uvicorn app.main:app --reload
```

The app will be available at: **http://localhost:8000**

## AI Features Usage

### 1. Article AI Assistant
When you view an article, the AI will automatically generate:
- **Summary**: A brief 2-3 sentence summary of the article
- **Key Vocabulary**: Important words with definitions

### 2. Ask AI Questions
- On any article page, use the "Ask AI" feature
- Type any question about the article (vocabulary, grammar, meaning, etc.)
- Get instant AI-powered answers to help you understand
- Examples: "What does [word] mean?", "Can you explain this paragraph?", "What's the main idea?"

### 3. AI Test Explanations
- After completing a test, you'll see:
  - Your score and percentage
  - Detailed review of each question
  - AI-generated explanations for each answer
  - Why the correct answer is right
  - Common mistakes (if you got it wrong)

## Project Structure

```
EnglishWebsite/
├── app/
│   ├── main.py           # FastAPI application
│   ├── models.py         # Database models
│   ├── schemas.py        # Pydantic schemas
│   ├── crud.py           # Database operations
│   ├── ai_helper.py      # AI integration with OpenRouter
│   ├── templates/        # Jinja2 HTML templates
│   └── static/          # CSS and static files
├── .env                  # Environment variables (API key)
├── requirments.txt      # Python dependencies
└── README.md            # This file
```

## API Endpoints

### Articles
- `GET /` - Home page
- `GET /articles` - List all articles
- `GET /articles/create` - Create article form
- `POST /articles/create` - Submit new article
- `GET /articles/{id}` - View article (with AI summary & vocabulary)
- `POST /articles/{id}/ask-ai` - Ask AI a question about the article
- `POST /articles/{id}/comments` - Add comment

### Collections
- `GET /collections` - List collections
- `GET /collections/create` - Create collection form
- `POST /collections/create` - Submit new collection
- `GET /collections/{id}` - View collection

### Tests
- `GET /tests` - List all tests
- `GET /tests/create` - Create test form
- `POST /tests/create` - Submit new test
- `GET /tests/{id}` - Take test
- `POST /tests/{id}/submit` - Submit answers (with AI explanations)

## AI Model

The application uses **Google Gemini 2.5 Flash Lite** via OpenRouter for:
- Fast responses
- Cost-effective usage
- High-quality educational content generation

## Technologies

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Database ORM
- **Jinja2** - Template engine
- **OpenRouter** - AI API gateway (via requests library)
- **SQLite** - Database
- **Python 3.8+** compatible

## Development

To run in development mode with auto-reload:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Notes

- The database (`database.db`) is automatically created on first run
- AI features require a valid OpenRouter API key
- All AI requests are sent to OpenRouter's API
- The application uses Google's Gemini model for cost-effectiveness
