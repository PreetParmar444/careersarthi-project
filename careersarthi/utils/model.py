from google.adk.models import Gemini
from google.genai import types

# Centralised model instance with retry options configured.
# This prevents 429 Resource Exhausted crashes due to the 5 RPM free tier rate limit of gemini-2.5-flash.
gemini_model = Gemini(
    model="gemini-3.5-flash",
    retry_options=types.HttpRetryOptions(
        attempts=6,
        initial_delay=3.0,
        max_delay=30.0,
        exp_base=2.0,
    )
)
