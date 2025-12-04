"""
Servicio para gestión de archivos JSON y PDF.
Proporciona funcionalidades CRUD y utilidades para manejo de archivos.
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from django.db.models import QuerySet
from myapp.models import JSONCorpus, PDFDocument, FileVersion
from pypdf import PdfReader


class FileManagerService:
    """
    Servicio centralizado para gestión de archivos JSON y PDF.
    Implementa lógica de negocio y operaciones sobre archivos.
    """
    
    # ========================================================================
    # GESTIÓN DE CORPUS JSON
    # ========================================================================
    
    @staticmethod
    def create_json_corpus(
        name: str,
        file: UploadedFile,
        corpus_type: str = 'general',
        description: str = '',
        version: str = '',
        created_by: str = '',
        validate_json: bool = True
    ) -> Tuple[Optional[JSONCorpus], Optional[str]]:
        """
        Crea un nuevo corpus JSON.
        
        Args:
            name: Nombre identificador del corpus
            file: Archivo JSON subido
            corpus_type: Tipo de corpus
            description: Descripción del contenido
            version: Versión del corpus
            created_by: Usuario creador
            validate_json: Si True, valida que sea JSON válido
        
        Returns:
            Tupla (corpus_creado, mensaje_error)
        """
        try:
            # Validar que sea JSON válido
            if validate_json:
                try:
                    json_content = json.load(file)
                    records_count = len(json_content) if isinstance(json_content, list) else 1
                except json.JSONDecodeError as e:
                    return None, f"Archivo JSON inválido: {str(e)}"
            else:
                records_count = 0
            
            # Resetear puntero del archivo
            file.seek(0)
            
            # Crear corpus
            corpus = JSONCorpus.objects.create(
                name=name,
                corpus_type=corpus_type,
                description=description,
                file=file,
                version=version,
                records_count=records_count,
                created_by=created_by
            )
            
            return corpus, None
            
        except Exception as e:
            return None, f"Error al crear corpus: {str(e)}"
    
    @staticmethod
    def update_json_corpus(
        corpus_id: int,
        new_file: Optional[UploadedFile] = None,
        create_backup: bool = True,
        **update_fields
    ) -> Tuple[Optional[JSONCorpus], Optional[str]]:
        """
        Actualiza un corpus JSON existente.
        
        Args:
            corpus_id: ID del corpus a actualizar
            new_file: Nuevo archivo (opcional)
            create_backup: Si True, crea versión de respaldo
            **update_fields: Campos a actualizar (name, description, etc)
        
        Returns:
            Tupla (corpus_actualizado, mensaje_error)
        """
        try:
            corpus = JSONCorpus.objects.get(id=corpus_id)
            
            # Crear backup si hay nuevo archivo
            if new_file and create_backup:
                FileManagerService._create_version_backup(
                    content_type='json_corpus',
                    object_id=corpus.id,
                    old_file=corpus.file,
                    version=corpus.version or '1.0',
                    description=f"Versión anterior antes de actualización"
                )
            
            # Actualizar archivo
            if new_file:
                # Eliminar archivo antiguo
                if corpus.file:
                    old_path = corpus.file.path
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                # Validar nuevo JSON
                try:
                    json_content = json.load(new_file)
                    records_count = len(json_content) if isinstance(json_content, list) else 1
                    new_file.seek(0)
                    corpus.records_count = records_count
                except json.JSONDecodeError as e:
                    return None, f"Nuevo archivo JSON inválido: {str(e)}"
                
                corpus.file = new_file
            
            # Actualizar otros campos
            for field, value in update_fields.items():
                if hasattr(corpus, field):
                    setattr(corpus, field, value)
            
            corpus.save()
            return corpus, None
            
        except JSONCorpus.DoesNotExist:
            return None, f"Corpus con ID {corpus_id} no encontrado"
        except Exception as e:
            return None, f"Error al actualizar corpus: {str(e)}"
    
    @staticmethod
    def get_active_corpus(corpus_type: Optional[str] = None) -> QuerySet:
        """
        Obtiene corpus activos, opcionalmente filtrados por tipo.
        
        Args:
            corpus_type: Tipo de corpus a filtrar (opcional)
        
        Returns:
            QuerySet de corpus activos
        """
        queryset = JSONCorpus.objects.filter(is_active=True)
        if corpus_type:
            queryset = queryset.filter(corpus_type=corpus_type)
        return queryset
    
    @staticmethod
    def load_json_content(corpus: JSONCorpus) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Carga y parsea el contenido de un corpus JSON.
        
        Args:
            corpus: Instancia de JSONCorpus
        
        Returns:
            Tupla (contenido_json, mensaje_error)
        """
        try:
            with corpus.file.open('r', encoding='utf-8') as f:
                content = json.load(f)
            return content, None
        except Exception as e:
            return None, f"Error al cargar JSON: {str(e)}"
    
    # ========================================================================
    # GESTIÓN DE DOCUMENTOS PDF
    # ========================================================================
    
    @staticmethod
    def create_pdf_document(
        title: str,
        file: UploadedFile,
        document_type: str = 'report',
        description: str = '',
        version: str = '',
        status: str = 'draft',
        tags: str = '',
        is_public: bool = False,
        created_by: str = '',
        extract_metadata: bool = True
    ) -> Tuple[Optional[PDFDocument], Optional[str]]:
        """
        Crea un nuevo documento PDF.
        
        Args:
            title: Título del documento
            file: Archivo PDF subido
            document_type: Tipo de documento
            description: Descripción
            version: Versión
            status: Estado del documento
            tags: Etiquetas separadas por comas
            is_public: ¿Es público?
            created_by: Usuario creador
            extract_metadata: Si True, extrae metadatos del PDF
        
        Returns:
            Tupla (documento_creado, mensaje_error)
        """
        try:
            page_count = 0
            
            # Extraer metadatos del PDF
            if extract_metadata:
                try:
                    file.seek(0)
                    pdf_reader = PdfReader(file)
                    page_count = len(pdf_reader.pages)
                    file.seek(0)
                except Exception as e:
                    print(f"⚠️ No se pudo extraer metadatos del PDF: {e}")
            
            # Crear documento
            document = PDFDocument.objects.create(
                title=title,
                document_type=document_type,
                description=description,
                file=file,
                version=version,
                status=status,
                tags=tags,
                is_public=is_public,
                page_count=page_count,
                created_by=created_by
            )
            
            return document, None
            
        except Exception as e:
            return None, f"Error al crear documento PDF: {str(e)}"
    
    @staticmethod
    def update_pdf_document(
        document_id: int,
        new_file: Optional[UploadedFile] = None,
        create_backup: bool = True,
        **update_fields
    ) -> Tuple[Optional[PDFDocument], Optional[str]]:
        """
        Actualiza un documento PDF existente.
        
        Args:
            document_id: ID del documento a actualizar
            new_file: Nuevo archivo (opcional)
            create_backup: Si True, crea versión de respaldo
            **update_fields: Campos a actualizar
        
        Returns:
            Tupla (documento_actualizado, mensaje_error)
        """
        try:
            document = PDFDocument.objects.get(id=document_id)
            
            # Crear backup si hay nuevo archivo
            if new_file and create_backup:
                FileManagerService._create_version_backup(
                    content_type='pdf_document',
                    object_id=document.id,
                    old_file=document.file,
                    version=document.version or '1.0',
                    description=f"Versión anterior antes de actualización"
                )
            
            # Actualizar archivo
            if new_file:
                # Eliminar archivo antiguo
                if document.file:
                    old_path = document.file.path
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                # Extraer metadatos del nuevo PDF
                try:
                    pdf_reader = PdfReader(new_file)
                    page_count = len(pdf_reader.pages)
                    new_file.seek(0)
                    document.page_count = page_count
                except Exception:
                    pass
                
                document.file = new_file
            
            # Actualizar otros campos
            for field, value in update_fields.items():
                if hasattr(document, field):
                    setattr(document, field, value)
            
            document.save()
            return document, None
            
        except PDFDocument.DoesNotExist:
            return None, f"Documento con ID {document_id} no encontrado"
        except Exception as e:
            return None, f"Error al actualizar documento: {str(e)}"
    
    @staticmethod
    def get_public_documents() -> QuerySet:
        """Obtiene documentos públicos."""
        return PDFDocument.objects.filter(is_public=True, status='published')
    
    @staticmethod
    def search_documents(query: str) -> QuerySet:
        """
        Busca documentos por título, descripción o tags.
        
        Args:
            query: Texto de búsqueda
        
        Returns:
            QuerySet de documentos que coinciden
        """
        from django.db.models import Q
        return PDFDocument.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__icontains=query)
        )
    
    # ========================================================================
    # VERSIONADO DE ARCHIVOS
    # ========================================================================
    
    @staticmethod
    def _create_version_backup(
        content_type: str,
        object_id: int,
        old_file,
        version: str,
        description: str = ''
    ) -> Optional[FileVersion]:
        """
        Crea una versión de respaldo de un archivo.
        Método privado para uso interno.
        """
        try:
            # Leer contenido del archivo antiguo
            old_file.seek(0)
            content = old_file.read()
            old_file.seek(0)
            
            # Crear archivo de respaldo
            filename = os.path.basename(old_file.name)
            backup_file = ContentFile(content, name=filename)
            
            # Crear registro de versión
            file_version = FileVersion.objects.create(
                content_type=content_type,
                object_id=object_id,
                version_number=version,
                file_backup=backup_file,
                change_description=description
            )
            
            return file_version
            
        except Exception as e:
            print(f"⚠️ Error al crear backup: {e}")
            return None
    
    @staticmethod
    def get_file_versions(content_type: str, object_id: int) -> QuerySet:
        """
        Obtiene todas las versiones de un archivo.
        
        Args:
            content_type: Tipo de contenido ('json_corpus' o 'pdf_document')
            object_id: ID del objeto
        
        Returns:
            QuerySet de versiones ordenadas por fecha
        """
        return FileVersion.objects.filter(
            content_type=content_type,
            object_id=object_id
        ).order_by('-created_at')
    
    @staticmethod
    def restore_version(
        version_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Restaura una versión anterior de un archivo.
        
        Args:
            version_id: ID de la versión a restaurar
        
        Returns:
            Tupla (éxito, mensaje_error)
        """
        try:
            version = FileVersion.objects.get(id=version_id)
            
            # Determinar tipo de objeto
            if version.content_type == 'json_corpus':
                corpus = JSONCorpus.objects.get(id=version.object_id)
                
                # Crear backup del archivo actual antes de restaurar
                FileManagerService._create_version_backup(
                    content_type='json_corpus',
                    object_id=corpus.id,
                    old_file=corpus.file,
                    version=corpus.version or 'current',
                    description='Backup automático antes de restaurar versión'
                )
                
                # Restaurar archivo
                version.file_backup.seek(0)
                content = version.file_backup.read()
                corpus.file.save(
                    os.path.basename(version.file_backup.name),
                    ContentFile(content),
                    save=True
                )
                
            elif version.content_type == 'pdf_document':
                document = PDFDocument.objects.get(id=version.object_id)
                
                # Crear backup del archivo actual
                FileManagerService._create_version_backup(
                    content_type='pdf_document',
                    object_id=document.id,
                    old_file=document.file,
                    version=document.version or 'current',
                    description='Backup automático antes de restaurar versión'
                )
                
                # Restaurar archivo
                version.file_backup.seek(0)
                content = version.file_backup.read()
                document.file.save(
                    os.path.basename(version.file_backup.name),
                    ContentFile(content),
                    save=True
                )
            
            return True, None
            
        except (FileVersion.DoesNotExist, JSONCorpus.DoesNotExist, PDFDocument.DoesNotExist):
            return False, "Versión u objeto no encontrado"
        except Exception as e:
            return False, f"Error al restaurar versión: {str(e)}"
    
    # ========================================================================
    # UTILIDADES
    # ========================================================================
    
    @staticmethod
    def get_storage_stats() -> Dict:
        """
        Obtiene estadísticas de almacenamiento.
        
        Returns:
            Diccionario con estadísticas de uso de archivos
        """
        from django.db.models import Sum
        
        json_stats = JSONCorpus.objects.aggregate(
            total_size=Sum('file_size'),
            count=models.Count('id')
        )
        
        pdf_stats = PDFDocument.objects.aggregate(
            total_size=Sum('file_size'),
            count=models.Count('id')
        )
        
        return {
            'json_corpus': {
                'count': json_stats['count'] or 0,
                'total_size_bytes': json_stats['total_size'] or 0,
                'total_size_mb': round((json_stats['total_size'] or 0) / (1024 * 1024), 2)
            },
            'pdf_documents': {
                'count': pdf_stats['count'] or 0,
                'total_size_bytes': pdf_stats['total_size'] or 0,
                'total_size_mb': round((pdf_stats['total_size'] or 0) / (1024 * 1024), 2)
            },
            'total': {
                'count': (json_stats['count'] or 0) + (pdf_stats['count'] or 0),
                'total_size_mb': round(
                    ((json_stats['total_size'] or 0) + (pdf_stats['total_size'] or 0)) / (1024 * 1024),
                    2
                )
            }
        }
