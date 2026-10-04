# 🍽️ FoodScope AI

FoodScope AI is an AI-powered nutrition analyzer that identifies food from a photo and estimates its calories, protein, carbohydrates, fat, and fiber — then lets you chat with an AI assistant about your meal.

## ✨ Features

- 📸 **Scan or upload** a photo of your food (live camera or file upload)
- 🤖 **AI-powered analysis** using Google's Gemini vision models
- 📊 **Nutrition breakdown** — calories, protein, carbs, fat, and fiber
- 💬 **AI chatbot** — ask follow-up questions about your meal
- 📝 **Conversation summary** — get a quick recap of your chat
- 📲 **WhatsApp sharing** — send your meal summary directly to WhatsApp
- 📱 **Mobile-friendly UI** — clean, responsive design

## 🛠️ Tech Stack

- **Frontend/Backend:** [Streamlit](https://streamlit.io/)
- **AI Model:** Google Gemini API (`google-genai`)
- **Image Processing:** Pillow (PIL)
- **Language:** Python

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- A Google Gemini API key ([get one here](https://aistudio.google.com/apikey))

### Installation

1. Clone this repository
```bash
   git clone https://github.com/[YOUR_USERNAME]/FoodScope-AI.git
   cd FoodScope-AI
```

2. Create and activate a virtual environment
```bash
   python -m venv venv
   venv\Scripts\Activate      # Windows
   source venv/bin/activate   # macOS/Linux
```

3. Install dependencies
```bash
   pip install -r requirements.txt
```

4. Add your Gemini API key

   Create a file at `.streamlit/secrets.toml`:
```toml
   GEMINI_API_KEY = "your_api_key_here"
```

5. Run the app
```bash
   streamlit run app.py
```

## 📸 Screenshots

*(Add a screenshot or two here once your app looks final — see instructions below)*

## 📂 Project Structure