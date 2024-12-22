from flask import Flask, request, jsonify, render_template
import speech_recognition as sr
import os
import language_tool_python
import re
from collections import Counter

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")  # Render the HTML page

@app.route('/summarize-audio', methods=['POST'])
def summarize_audio():
    if 'audioFile' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audioFile']
    file_path = os.path.join('uploads', audio_file.filename)
    audio_file.save(file_path)

    text = transcribe_audio(file_path)
    if not text:
        return jsonify({"error": "Failed to transcribe audio"}), 400

    summary_points = generate_summary(text, percentage=0.4)
    return jsonify({"summary": summary_points})


def generate_summary(transcript, percentage=0.3):
    """
    Generates a summary of the transcript by selecting a percentage of the most relevant sentences,
    and returns the summary as bullet points.

    Args:
        transcript (str): The input transcript text.
        percentage (float): The percentage of the text to be used in the summary (default is 30%).

    Returns:
        list: A list of summarized sentences formatted as bullet points.
    """
    cleaned_words = clean_text(transcript)
    word_frequency = calculate_word_frequency(cleaned_words)
    ranked_sentences = rank_sentences(transcript, word_frequency)
    
    # Determine the number of sentences to include in the summary
    num_sentences = max(1, int(len(ranked_sentences) * percentage))
    selected_sentences = ranked_sentences[:num_sentences]
    
    # Format the summary as bullet points
    summary_points = [f"- {sentence.strip()}" for sentence in selected_sentences]
    
    return summary_points

def clean_text(text):
    """
    Cleans the text by removing special characters and splitting into words.

    Args:
        text (str): The input text to clean.

    Returns:
        list: A list of cleaned words.
    """
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)  # Remove special characters
    return text.split()

def calculate_word_frequency(words):
    """
    Calculates word frequencies in the text.

    Args:
        words (list): A list of words.

    Returns:
        dict: A dictionary with word frequencies.
    """
    return Counter(words)

def rank_sentences(text, word_frequency):
    """
    Ranks sentences based on word frequency.

    Args:
        text (str): The original text.
        word_frequency (dict): Word frequency dictionary.

    Returns:
        list: A list of sentences ranked by relevance.
    """
    sentences = text.split('. ')
    sentence_scores = {}

    for sentence in sentences:
        for word in sentence.lower().split():
            if word in word_frequency:
                sentence_scores[sentence] = sentence_scores.get(sentence, 0) + word_frequency[word]
    
    # Sort sentences by score in descending order
    ranked_sentences = sorted(sentence_scores.keys(), key=lambda x: sentence_scores[x], reverse=True)
    return ranked_sentences



def transcribe_audio(file_path):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(file_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)  # Using Google's speech-to-text
            return text
    except Exception as e:
        print(f"Error during transcription: {e}")
        return None

import language_tool_python

def summarize_text(text):
    """
    Summarizes the input text, corrects grammatical errors, and presents it as bullet points.
    """
    # Split text into sentences
    sentences = text.split('. ')
    
    # If text is short, use all sentences; otherwise, pick key ones
    if len(sentences) <= 3:
        key_sentences = sentences
    else:
        # Select first, longest, and last sentences as key points
        longest_sentence = max(sentences, key=len)
        key_sentences = [sentences[0], longest_sentence, sentences[-1]]

    # Initialize grammar correction tool
    tool = language_tool_python.LanguageTool('en-US')
    corrected_sentences = [tool.correct(sentence.strip()) for sentence in key_sentences if sentence.strip()]

    # Format sentences as bullet points
    summary_points = [f"- {sentence}" for sentence in corrected_sentences]
    return summary_points


if __name__ == '__main__':
    app.run(debug=True)
