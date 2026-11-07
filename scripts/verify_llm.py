"""Verifica que Gemini responde con la API key del archivo .env."""
import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

llm = ChatGoogleGenerativeAI(model=os.getenv("LLM_MODEL", "gemini-3.6-flash"))
respuesta = llm.invoke("Responde solo: 'Hola desde Gemini'")
print(respuesta.text)
