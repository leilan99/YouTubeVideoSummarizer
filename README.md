# YouTube Video Summarizer

This project is a Flask-based web service that accepts YouTube URLs, extracts video transcripts, and generates concise summaries using the OpenAI API. It supports both manually created and auto-generated transcripts in multiple languages, falling back to the best available option.

## Features

- Accepts YouTube video URLs via a REST API
- Automatically extracts transcripts using `youtube_transcript_api`
- Uses OpenAI's GPT model to generate summaries
- Handles errors with descriptive messages and logs
- CORS-enabled for integration with any frontend

---

## Setup

### Prerequisites

- Python 3.8+
- An OpenAI API key
- [YouTube Transcript API](https://pypi.org/project/youtube-transcript-api/)
- [OpenAI Python SDK](https://pypi.org/project/openai/)
- `dotenv` for managing environment variables

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/youtube-summarizer.git
   cd youtube-summarizer
