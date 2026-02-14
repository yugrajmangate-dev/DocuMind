# Groq Chatbot

A simple command-line chatbot using Groq API with the `openai/gpt-oss-120b` model.

## 📋 Prerequisites

- Python 3.7 or higher
- A Groq API key (get one from [console.groq.com](https://console.groq.com/keys))

## 🚀 Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Open the `.env` file and replace `your_groq_api_key_here` with your actual Groq API key:

```env
GROQ_API_KEY=gsk_your_actual_api_key_here
```

### 3. Run the Chatbot

```bash
python chatbot.py
```

## 💡 Usage

Once the chatbot is running:

- **Chat**: Simply type your message and press Enter
- **Clear History**: Type `clear` to reset the conversation
- **Exit**: Type `quit`, `exit`, or `q` to end the session
- **Interrupt**: Press `Ctrl+C` to force quit

## 📁 Project Structure

```
.
├── chatbot.py          # Main chatbot script
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (API key)
└── README.md          # This file
```

## 🔧 Configuration

You can modify the following parameters in `chatbot.py`:

- `model`: Change the model (default: `openai/gpt-oss-120b`)
- `temperature`: Control randomness (0.0 to 2.0, default: 0.7)
- `max_tokens`: Maximum response length (default: 1024)

## 📝 Example

```
💬 You: Hello! What can you do?
🤖 Bot: Hello! I'm a chatbot powered by Groq...

💬 You: Tell me a joke
🤖 Bot: Sure! Here's one for you...
```

## ⚠️ Troubleshooting

- **API Key Error**: Make sure your `.env` file contains a valid Groq API key
- **Import Error**: Run `pip install -r requirements.txt` to install dependencies
- **Connection Error**: Check your internet connection

## 📄 License

This project is open source and available for educational purposes.
