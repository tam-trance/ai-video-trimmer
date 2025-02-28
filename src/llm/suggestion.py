import json
import os

from dotenv import load_dotenv
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()

def get_llm_suggestion(raw_transcription):
    """
    Uses Gemini model via LangChain to filter out redundant or duplicate transcription segments.
    """
    # Define the expected output schema
    response_schemas = [
        ResponseSchema(
            name="filtered_transcription",
            description=(
                "A list of transcription segments to keep, in chronological order. "
                "Each segment is an object with 'start' (number, seconds), 'end' (number, seconds), and 'text' (string)."
            ),
        )
    ]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()

    # Build a detailed prompt with explicit instructions
    prompt = (
        "You are given a raw JSON transcription of a video as an array of objects. "
        "Each object has three keys: 'start' (a number indicating the start time in seconds), "
        "'end' (a number indicating the end time in seconds), and 'text' (a string with the transcribed speech).\n\n"
        "Your task is to remove any segments that are redundant, duplicate, or mistaken. "
        "Specifically, if two or more segments have the same or nearly identical 'text' (ignoring minor differences such as punctuation or trailing ellipses), "
        "only keep the segment with the highest start time (i.e. the last occurrence) and remove all earlier duplicates. "
        "The final output should be a JSON object with a single key 'filtered_transcription' that contains an array of the remaining segments, "
        "Observe that sometimes the segments may be rephrased, so consider this a duplication and always consider the last occurrence."
        'example of input: { "start": 6.84, "end": 9.8, "text": "In my previous video, I\'ve reached..." }, { "start": 12.24, "end": 15.08, "text": "In my previous video, I\'ve reached many comments." }, { "start": 15.84, "end": 24.17, "text": "In my previous video I\'ve received many comments asking why use an LLM to scrape if we can just use normal selenium, beautiful soup, or puppeteer." }, in this example you would only retain the last object.'
        "in chronological order.\n\n"
        "Follow exactly the format instructions provided below:\n\n"
        f"{format_instructions}\n\n"
        "Here is the raw transcription JSON:\n"
        f"{json.dumps(raw_transcription, indent=2)}"
    )

    # Initialize Gemini model via LangChain
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-pro-exp-02-05", temperature=0, api_key=os.getenv("GOOGLE_API_KEY"))
    
    try:
        # Get response from Gemini
        response = llm.invoke(prompt)
        parsed_output = output_parser.parse(response.content)
        return parsed_output
    except Exception as e:
        print(f"Error processing transcription: {e}")
        return {"filtered_transcription": raw_transcription}  # Return original data as fallback
