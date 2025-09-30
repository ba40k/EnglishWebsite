import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.5-flash-lite"


def _call_openrouter(messages, temperature=0.7):
    """Make a request to OpenRouter API using requests library."""
    response = requests.post(
        url=OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": MODEL,
            "messages": messages,
            "temperature": temperature,
        })
    )
    
    if response.status_code != 200:
        print(f"OpenRouter API Error: {response.status_code} - {response.text}")
        return None
    
    result = response.json()
    return result.get("choices", [{}])[0].get("message", {}).get("content", "")


def ask_about_article(article_title, article_body, question):
    """Ask AI a question about an article."""
    prompt = f"""You are an English learning assistant. A student is reading the following article and has a question.

Article Title: {article_title}
Article Content: {article_body}

Student's Question: {question}

Provide a helpful, educational answer that helps them understand the article better. Keep it concise and clear.
"""
    
    try:
        content = _call_openrouter([
            {
                "role": "user",
                "content": prompt
            }
        ])
        
        if not content:
            return "Sorry, I couldn't generate an answer at this time."
        
        return content
    except Exception as e:
        print(f"AI Error: {e}")
        return "Sorry, an error occurred while processing your question."


def explain_test_answers(test_title, questions_and_answers):
    """Generate explanations for test answers."""
    qa_text = "\n".join([
        f"Q{i+1}: {qa['question']}\n"
        f"Correct Answer: {qa['correct_answer']}\n"
        f"User Selected: {qa['user_answer']}\n"
        f"Result: {'✓ Correct' if qa['is_correct'] else '✗ Incorrect'}"
        for i, qa in enumerate(questions_and_answers)
    ])
    
    prompt = f"""You are an English teacher reviewing a student's test results. Provide brief, helpful explanations for each answer.

Test: {test_title}

{qa_text}

For each question, provide a concise explanation (1-2 sentences) focusing on:
- Why the correct answer is right
- Common mistakes (if user got it wrong)
- Key grammar/vocabulary points

Return ONLY a JSON array of explanations in this format:
[
  "Explanation for question 1...",
  "Explanation for question 2...",
  ...
]
"""
    
    try:
        content = _call_openrouter([
            {
                "role": "user",
                "content": prompt
            }
        ])
        
        if not content:
            return []
        
        start = content.find('[')
        end = content.rfind(']') + 1
        if start != -1 and end > start:
            content = content[start:end]
        
        explanations = json.loads(content)
        return explanations
    except Exception as e:
        print(f"AI Error: {e}")
        return []


def generate_article_summary(article_title, article_body):
    """Generate a summary and vocabulary list for an article."""
    prompt = f"""Analyze this English article and provide:
1. A brief summary (2-3 sentences)
2. Key vocabulary words with definitions (5-7 words)

Article Title: {article_title}
Article Content: {article_body}

Return ONLY a JSON object with this format:
{{
  "summary": "Summary text here...",
  "vocabulary": [
    {{"word": "word1", "definition": "definition here"}},
    {{"word": "word2", "definition": "definition here"}}
  ]
}}
"""
    
    try:
        content = _call_openrouter([
            {
                "role": "user",
                "content": prompt
            }
        ])
        
        if not content:
            return {"summary": "", "vocabulary": []}
        
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end > start:
            content = content[start:end]
        
        result = json.loads(content)
        return result
    except Exception as e:
        print(f"AI Error: {e}")
        return {"summary": "", "vocabulary": []}