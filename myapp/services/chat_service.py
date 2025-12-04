"""
Servicio de chat con IA (RAG con LangChain + Gemini).
Adaptado de utils/chatbot.py para Django.
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from google.api_core.exceptions import ResourceExhausted, PermissionDenied, ServiceUnavailable

from myapp.prompts.chat_prompts import get_chat_prompt_template


class ChatService:
    """
    Servicio para gestionar la conversación con el chatbot.
    Mantiene la lógica RAG original sin cambios.
    """
    
    def __init__(self):
        load_dotenv()
        self.llm = None
        self.retrieval_chain = None
    
    def _get_llm(self):
        """Inicializa el modelo de lenguaje Gemini."""
        if not self.llm:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    temperature=0.2,
                    max_output_tokens=2048,
                    convert_system_message_to_human=True
                )
            except (PermissionDenied, ResourceExhausted, ServiceUnavailable) as e:
                print(f"❌ Error al conectar con Gemini: {e}")
                return None
        
        return self.llm
    
    def create_retrieval_chain(self, vectordb):
        """
        Crea la cadena de recuperación + generación (RAG).
        
        Args:
            vectordb: Instancia de ChromaDB
        
        Returns:
            Cadena de retrieval o None si falla
        """
        llm = self._get_llm()
        if not llm:
            return None
        
        try:
            retriever = vectordb.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 15}
            )
            
            prompt = get_chat_prompt_template()
            chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
            retrieval_chain = create_retrieval_chain(retriever, chain)
            
            return retrieval_chain
        
        except Exception as e:
            print(f"❌ Error al crear retrieval chain: {e}")
            return None
    
    def get_retrieval_chain(self, vectordb, cached_chain=None):
        """
        Obtiene la cadena de retrieval, usando caché si está disponible.
        
        Args:
            vectordb: Instancia de ChromaDB
            cached_chain: Cadena en caché (opcional)
        
        Returns:
            Cadena de retrieval
        """
        if cached_chain:
            return cached_chain
        
        return self.create_retrieval_chain(vectordb)
    
    def get_response(self, question, chat_history, vectordb, retrieval_chain=None):
        """
        Genera una respuesta usando el contexto del vector DB.
        
        Args:
            question: Pregunta del usuario
            chat_history: Historial de conversación (lista de mensajes LangChain)
            vectordb: Instancia de ChromaDB
            retrieval_chain: Cadena en caché (opcional)
        
        Returns:
            Tupla (respuesta, contexto_documentos)
        """
        chain = self.get_retrieval_chain(vectordb, retrieval_chain)
        
        if not chain:
            return "No se pudo conectar con el modelo de IA.", []
        
        try:
            response = chain.invoke({
                "input": question,
                "chat_history": chat_history
            })
            return response["answer"], response.get("context", [])
        
        except Exception as e:
            print(f"❌ Error al generar respuesta: {e}")
            return f"Ocurrió un error al procesar tu consulta: {str(e)}", []
    
    def convert_to_langchain_messages(self, messages_data):
        """
        Convierte mensajes de Django (dicts) a mensajes de LangChain.
        
        Args:
            messages_data: Lista de diccionarios con 'role' y 'content'
        
        Returns:
            Lista de objetos HumanMessage/AIMessage
        """
        langchain_messages = []
        
        for msg in messages_data:
            if msg['role'] == 'human':
                langchain_messages.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'ai':
                langchain_messages.append(AIMessage(content=msg['content']))
        
        return langchain_messages
    
    def extract_source_info(self, context_docs):
        """
        Extrae información de las fuentes consultadas.
        
        Args:
            context_docs: Lista de documentos retornados por el retriever
        
        Returns:
            Diccionario con pdf_sources y web_sources
        """
        pdf_sources = {}
        web_sources = {}
        
        for doc in context_docs:
            metadata = doc.metadata
            source = metadata.get('source', 'Desconocido')
            
            if source.endswith('.pdf'):
                filename = os.path.basename(source)
                if filename not in pdf_sources:
                    pdf_sources[filename] = []
                if 'page' in metadata:
                    pdf_sources[filename].append(metadata['page'])
            else:
                if source not in web_sources:
                    web_sources[source] = []
                if 'titulo' in metadata:
                    web_sources[source].append(metadata['titulo'])
        
        # Limpiar duplicados en PDFs
        for filename in pdf_sources:
            pages = pdf_sources[filename]
            pdf_sources[filename] = sorted(
                set(map(str, pages)), 
                key=lambda x: int(x) if x.isdigit() else 0
            )
        
        # Limpiar duplicados en web
        for source in web_sources:
            web_sources[source] = list(set(web_sources[source]))
        
        return {
            'pdf_sources': pdf_sources,
            'web_sources': web_sources
        }
