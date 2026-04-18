from src.core.vector_store import vectorstore
from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import Config

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=Config.GOOGLE_API_KEY
)
