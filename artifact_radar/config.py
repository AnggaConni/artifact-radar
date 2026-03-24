GEMINI_MODEL = "gemini-2.5-flash"
GENERATE_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

DEFAULT_MAX_CANDIDATES_PER_KEYWORD = 5
REQUEST_DELAY_SEC = 3.0
