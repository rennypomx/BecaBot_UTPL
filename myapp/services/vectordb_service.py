"""
Servicio de gestión de base de datos vectorial (ChromaDB).
Adaptado de utils/prepare_vectordb.py para Django.
"""

import os
import json
import warnings
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document
import chromadb

# Configuración del entorno
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
warnings.filterwarnings("ignore", message=".*torch.classes.*")
warnings.filterwarnings("ignore", message=".*telemetry.*")


class VectorDBService:
    """
    Servicio para gestión de la base de datos vectorial.
    Mantiene la lógica original sin cambios, adaptada a Django.
    """
    
    def __init__(self, persist_dir="Vector_DB - Documents"):
        load_dotenv()
        self.persist_dir = persist_dir
        self.embedding = self._get_embedding_model()
    
    def _get_embedding_model(self):
        """Configura el modelo de embeddings."""
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={
                "device": "cpu",
                "trust_remote_code": True
            },
            encode_kwargs={"normalize_embeddings": True}
        )
    
    def extract_pdf_text(self, pdf_filenames, docs_dir="docs"):
        """
        Extrae texto de archivos PDF.
        
        Args:
            pdf_filenames: Lista de nombres de archivos PDF
            docs_dir: Directorio donde están los PDFs
        
        Returns:
            Lista de documentos extraídos
        """
        docs = []
        
        if not os.path.exists(docs_dir):
            print(f"⚠️ La carpeta '{docs_dir}' no existe.")
            return docs
        
        for pdf in pdf_filenames:
            pdf_path = os.path.join(docs_dir, pdf)
            try:
                docs.extend(PyPDFLoader(pdf_path).load())
                print(f"✓ Texto extraído de {pdf}")
            except Exception as e:
                print(f"⚠️ Error al procesar {pdf}: {e}")
        
        return docs
    
    def extract_json_text(self, json_path="knowledge_base/corpus_utpl.json"):
        """
        Extrae texto del archivo JSON de becas scrapeadas.
        Mantiene la lógica original exacta.
        
        Args:
            json_path: Ruta al archivo JSON
        
        Returns:
            Lista de documentos LangChain
        """
        docs = []
        
        if not os.path.exists(json_path):
            print(f"⚠️ No se encontró el archivo JSON en {json_path}")
            return docs
        
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            print(f"📂 Procesando {len(data)} becas del archivo JSON...")
            
            for item in data:
                titulo = item.get("titulo", "Beca sin título")
                url = item.get("url", "")
                nivel = item.get("nivel", "General")
                tipos = ", ".join(item.get("tipos", []))
                modalidades = ", ".join(item.get("modalidades", []))
                
                contenido_raw = item.get("contenido", {})
                contenido_texto = ""
                
                if isinstance(contenido_raw, dict):
                    for clave, valor in contenido_raw.items():
                        valor_limpio = str(valor).replace('\n', ' ').strip()
                        contenido_texto += f"- {clave}: {valor_limpio}\n"
                else:
                    contenido_texto = str(contenido_raw)
                
                page_content = f"""
                TÍTULO DE LA BECA: {titulo}
                NIVEL ACADÉMICO: {nivel}
                TIPO: {tipos}
                MODALIDAD: {modalidades}
                ENLACE: {url}

                DETALLES, REQUISITOS Y BENEFICIOS:
                {contenido_texto}
                """
                
                doc = Document(
                    page_content=page_content,
                    metadata={
                        "source": "corpus_utpl.json",
                        "titulo": titulo,
                        "url": url,
                        "nivel": nivel,
                        "tipo": tipos
                    }
                )
                docs.append(doc)
            
            print(f"✓ Se cargaron {len(docs)} documentos desde el JSON.")
        
        except Exception as e:
            print(f"❌ Error al leer el JSON: {e}")
        
        return docs
    
    def get_text_chunks(self, docs):
        """
        Divide documentos en fragmentos.
        
        Args:
            docs: Lista de documentos
        
        Returns:
            Lista de fragmentos
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=300,
            separators=["\n\n", "\nTÍTULO DE LA BECA:", "\n", " ", ""]
        )
        return text_splitter.split_documents(docs)
    
    def load_existing_vectorstore(self):
        """
        Carga una base vectorial existente desde disco.
        
        Returns:
            Instancia de Chroma o None si falla
        """
        if not os.path.exists(self.persist_dir):
            return None
        
        try:
            settings = chromadb.config.Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                chroma_telemetry_impl="none"
            )
            client = chromadb.PersistentClient(
                path=self.persist_dir, 
                settings=settings
            )
            vectordb = Chroma(
                client=client,
                embedding_function=self.embedding
            )
            print("✓ Base vectorial cargada desde disco.")
            return vectordb
        
        except Exception as e:
            print(f"⚠️ Error al cargar base existente: {e}")
            return None
    
    def create_vectorstore(self, pdf_filenames, json_path="knowledge_base/corpus_utpl.json"):
        """
        Crea una nueva base vectorial desde cero.
        
        Args:
            pdf_filenames: Lista de nombres de PDFs
            json_path: Ruta al JSON de becas
        
        Returns:
            Instancia de Chroma o None si falla
        """
        print("🔄 Regenerando base vectorial...")
        
        # Cargar documentos
        docs_pdf = self.extract_pdf_text(pdf_filenames)
        docs_json = self.extract_json_text(json_path)
        all_docs = docs_pdf + docs_json
        
        if not all_docs:
            print("⚠️ No hay documentos para procesar.")
            return None
        
        # Dividir en chunks
        chunks = self.get_text_chunks(all_docs)
        print(f"📊 Total de fragmentos generados: {len(chunks)}")
        
        # Crear Vector Store
        try:
            settings = chromadb.config.Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                chroma_telemetry_impl="none"
            )
            client = chromadb.PersistentClient(
                path=self.persist_dir, 
                settings=settings
            )
            vectordb = Chroma.from_documents(
                documents=chunks,
                embedding=self.embedding,
                client=client
            )
            print("✓ Base vectorial creada y guardada.")
            return vectordb
        
        except Exception as e:
            print(f"❌ Error al crear la base vectorial: {e}")
            return None
    
    def get_vectorstore(self, pdf_filenames, force_regenerate=False):
        """
        Obtiene o crea la base vectorial.
        
        Args:
            pdf_filenames: Lista de nombres de PDFs
            force_regenerate: Si True, regenera desde cero
        
        Returns:
            Instancia de Chroma
        """
        if not force_regenerate:
            vectordb = self.load_existing_vectorstore()
            if vectordb:
                return vectordb
        
        return self.create_vectorstore(pdf_filenames)
