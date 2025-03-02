from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

options = webdriver.ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

def get_website_text(url):
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    return soup.body.get_text(separator="\n", strip=True)

def count_words(text):
    cleaned_text = text.replace('\n', ' ')
    words = cleaned_text.split()

    return len(words)

async def process_legal_text(tag_text, emoji_setting, length):
    load_dotenv(".env")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("API key not found. Ensure the .env file is correctly loaded.")
    client = AsyncOpenAI(api_key=api_key)
    
    # Set the emoji flag
    emoji = emoji_setting
    word_count = count_words(tag_text)
    tokens = word_count * length / 100.0 * 1.3
    tokens = tokens * 1.5 if emoji_setting else tokens
    tokens = int(tokens)
    target_length = int(round(word_count * length /100.0 * 0.5 / 100.0)*100)

    #tokens = word_in_original * length_tracker_percent * 1.3 * 1.5 if emoji

    if emoji:
        emoji_tracker = "Include at least 1 emoji per section for better readability and engagement. Every section title and summary must contain an emoji."
    else:
        emoji_tracker = "Do not include any emojis."

    prompt = f"""
Use markdown2 notation, but replace all ### headings with #### (this must be followed exactly). Only use heading level four and above.

Make this legal document easy to understand for ADHD & Dyslexic users.
Use plain language with short, simple words.
{emoji_tracker}

IMPORTANT: When quoting text from the legal document, copy the exact words without any modifications. Do NOT paraphrase or alter any quoted text. Every quoted section must match the source text exactly. The quote must be in its own line and the [] must be on the following line.


Begin with a QUICK SUMMARY before providing detailed information.
Both the QUICK SUMMARY and the detailed breakdown must include exact quotes from the document, with references in square brackets (e.g., 
"The dog ate the food" 
[Chapter 5]
). Do not fabricate page numbers; if unavailable, use the section name.
Ensure the final response is at least {target_length} words long.

Example Format (For Any Legal Document):
(If an exact page number is unavailable, use [SECTION NAME] instead.)

QUICK SUMMARY:
This document explains important legal information in a simple way.
It highlights the key points so you don’t have to read everything.
This is not legally binding. AI-generated summaries may contain errors.
Use at your own discretion.
Below is a detailed breakdown.

KEY DETAILS:

Obligations & Responsibilities
Brief summary
"exact quote"
[SECTION NAME, Page X]

Your Rights
Brief summary 
"exact quote"
[SECTION NAME, Page X]

Financial Terms
Brief summary
"exact quote"
[SECTION NAME, Page X]

Dispute Resolution
Brief summary
"exact quote"
[SECTION NAME, Page X]
"""

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system", 
                "content": "You are an AI that makes legal documents easy to understand for ADHD and Dyslexic users. Follow all formatting instructions exactly. When including quotations, ensure they are exactly as they appear in the source text. Also, include at least one emoji per section as specified."
            },
            {"role": "user", "content": f"{prompt}\n\n📜 **Legal Text:**\n{tag_text}"}
        ],
        response_format={"type": "text"},
        temperature=0,
        max_tokens=tokens,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response.choices[0].message.content