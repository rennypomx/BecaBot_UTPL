"""
Servicio de gestión de documentos PDF.
Adaptado de utils/save_docs.py para Django.
"""

import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile


class DocumentService:
    """
    Servicio para gestionar documentos PDF subidos por usuarios.
    """
    
    def __init__(self, docs_dir="docs"):
        self.docs_dir = docs_dir
        self._ensure_docs_directory()
    
    def _ensure_docs_directory(self):
        """Crea el directorio de documentos si no existe."""
        if not os.path.exists(self.docs_dir):
            os.makedirs(self.docs_dir)
            print(f"✓ Carpeta '{self.docs_dir}' creada.")
    
    def get_existing_documents(self):
        """
        Obtiene la lista de documentos ya existentes.
        
        Returns:
            Lista de nombres de archivos
        """
        if not os.path.exists(self.docs_dir):
            return []
        
        return [
            f for f in os.listdir(self.docs_dir) 
            if f.lower().endswith('.pdf')
        ]
    
    def save_uploaded_files(self, uploaded_files):
        """
        Guarda archivos PDF subidos en la carpeta docs.
        
        Args:
            uploaded_files: Lista de archivos de Django (request.FILES)
        
        Returns:
            Diccionario con:
                - saved_files: Lista de nombres guardados
                - skipped_files: Lista de archivos que ya existían
                - errors: Lista de errores
        """
        existing_docs = self.get_existing_documents()
        saved_files = []
        skipped_files = []
        errors = []
        
        for uploaded_file in uploaded_files:
            filename = uploaded_file.name
            
            # Verificar si ya existe
            if filename in existing_docs:
                skipped_files.append(filename)
                continue
            
            # Guardar archivo
            try:
                file_path = os.path.join(self.docs_dir, filename)
                
                with open(file_path, 'wb') as f:
                    for chunk in uploaded_file.chunks():
                        f.write(chunk)
                
                saved_files.append(filename)
                print(f"✓ Archivo guardado: {filename}")
            
            except Exception as e:
                error_msg = f"Error al guardar {filename}: {str(e)}"
                errors.append(error_msg)
                print(f"❌ {error_msg}")
        
        return {
            'saved_files': saved_files,
            'skipped_files': skipped_files,
            'errors': errors
        }
    
    def delete_document(self, filename):
        """
        Elimina un documento de la carpeta docs.
        
        Args:
            filename: Nombre del archivo a eliminar
        
        Returns:
            Tupla (success: bool, message: str)
        """
        file_path = os.path.join(self.docs_dir, filename)
        
        if not os.path.exists(file_path):
            return False, f"El archivo {filename} no existe."
        
        try:
            os.remove(file_path)
            print(f"✓ Archivo eliminado: {filename}")
            return True, f"Archivo {filename} eliminado correctamente."
        
        except Exception as e:
            error_msg = f"Error al eliminar {filename}: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def get_document_info(self):
        """
        Obtiene información sobre los documentos existentes.
        
        Returns:
            Diccionario con información de documentos
        """
        docs = self.get_existing_documents()
        
        doc_info = []
        total_size = 0
        
        for doc_name in docs:
            file_path = os.path.join(self.docs_dir, doc_name)
            try:
                size = os.path.getsize(file_path)
                total_size += size
                
                doc_info.append({
                    'name': doc_name,
                    'size': size,
                    'size_mb': round(size / (1024 * 1024), 2)
                })
            except Exception as e:
                print(f"⚠️ Error al obtener info de {doc_name}: {e}")
        
        return {
            'documents': doc_info,
            'total_count': len(docs),
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        }
