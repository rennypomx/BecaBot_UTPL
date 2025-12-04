"""
Modelos de Django para BecaBot UTPL.
Almacena conversaciones, documentos y archivos del sistema.
"""

from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator
import os


class ChatMessage(models.Model):
    """
    Modelo para almacenar mensajes del chat.
    Permite persistir el historial de conversaciones.
    """
    ROLE_CHOICES = [
        ('human', 'Usuario'),
        ('ai', 'BecaBot'),
    ]
    
    session_key = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Identificador de sesión del usuario"
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        help_text="Rol del mensaje (humano o IA)"
    )
    content = models.TextField(
        help_text="Contenido del mensaje"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="Fecha y hora del mensaje"
    )
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "Mensaje de Chat"
        verbose_name_plural = "Mensajes de Chat"
        indexes = [
            models.Index(fields=['session_key', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_role_display()}: {self.content[:50]}..."


class UploadedDocument(models.Model):
    """
    Modelo para rastrear documentos PDF subidos por usuarios.
    DEPRECADO: Usar PDFDocument para nuevos desarrollos.
    """
    session_key = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Identificador de sesión del usuario"
    )
    filename = models.CharField(
        max_length=255,
        help_text="Nombre del archivo"
    )
    file_path = models.CharField(
        max_length=500,
        help_text="Ruta del archivo en el sistema"
    )
    uploaded_at = models.DateTimeField(
        default=timezone.now,
        help_text="Fecha y hora de subida"
    )
    processed = models.BooleanField(
        default=False,
        help_text="Indica si el documento fue procesado en la base vectorial"
    )
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Documento Subido (Legacy)"
        verbose_name_plural = "Documentos Subidos (Legacy)"
        unique_together = ['session_key', 'filename']
    
    def __str__(self):
        return f"{self.filename} - {self.session_key[:8]}"


class ScrapingLog(models.Model):
    """
    Modelo para registrar ejecuciones del web scraper.
    """
    executed_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="Fecha y hora de ejecución"
    )
    success = models.BooleanField(
        default=False,
        help_text="Indica si el scraping fue exitoso"
    )
    num_becas = models.IntegerField(
        default=0,
        help_text="Número de becas extraídas"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Mensaje de error si falló"
    )
    
    class Meta:
        ordering = ['-executed_at']
        verbose_name = "Log de Scraping"
        verbose_name_plural = "Logs de Scraping"
    
    def __str__(self):
        status = "Exitoso" if self.success else "Fallido"
        return f"{status} - {self.executed_at.strftime('%Y-%m-%d %H:%M')}"


# ============================================================================
# NUEVOS MODELOS PARA GESTIÓN DE ARCHIVOS JSON Y PDF
# ============================================================================

class JSONCorpus(models.Model):
    """
    Modelo para almacenar archivos JSON con corpus de datos procesados.
    Almacena el archivo físico y permite versionado.
    """
    
    CORPUS_TYPES = [
        ('becas', 'Corpus de Becas'),
        ('faqs', 'Preguntas Frecuentes'),
        ('general', 'Datos Generales'),
        ('custom', 'Personalizado'),
    ]
    
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Nombre identificador del corpus (ej: 'becas_utpl_2024')"
    )
    corpus_type = models.CharField(
        max_length=20,
        choices=CORPUS_TYPES,
        default='general',
        help_text="Tipo de corpus de datos"
    )
    description = models.TextField(
        blank=True,
        help_text="Descripción del contenido del corpus"
    )
    file = models.FileField(
        upload_to='corpus_json/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['json'])],
        help_text="Archivo JSON con el corpus de datos"
    )
    version = models.CharField(
        max_length=50,
        blank=True,
        help_text="Versión del corpus (ej: 1.0, 2024-Q1)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indica si este corpus está activo para uso"
    )
    records_count = models.IntegerField(
        default=0,
        help_text="Número de registros en el corpus"
    )
    file_size = models.BigIntegerField(
        default=0,
        help_text="Tamaño del archivo en bytes"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text="Fecha de creación"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Última actualización"
    )
    created_by = models.CharField(
        max_length=100,
        blank=True,
        help_text="Usuario que creó el corpus"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Corpus JSON"
        verbose_name_plural = "Corpus JSON"
        indexes = [
            models.Index(fields=['corpus_type', 'is_active']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        status = "✓" if self.is_active else "✗"
        return f"{status} {self.name} ({self.get_corpus_type_display()})"
    
    def save(self, *args, **kwargs):
        """Guarda metadatos automáticamente."""
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    def get_file_size_mb(self):
        """Retorna el tamaño del archivo en MB."""
        return round(self.file_size / (1024 * 1024), 2)
    
    def delete(self, *args, **kwargs):
        """Elimina el archivo físico al borrar el registro."""
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)


class PDFDocument(models.Model):
    """
    Modelo para almacenar archivos PDF (reportes, documentación, etc).
    Permite categorización y versionado de documentos.
    """
    
    DOCUMENT_TYPES = [
        ('report', 'Reporte'),
        ('guide', 'Guía'),
        ('manual', 'Manual'),
        ('regulations', 'Reglamento'),
        ('form', 'Formulario'),
        ('other', 'Otro'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('published', 'Publicado'),
        ('archived', 'Archivado'),
    ]
    
    title = models.CharField(
        max_length=250,
        help_text="Título del documento"
    )
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPES,
        default='report',
        help_text="Tipo de documento"
    )
    description = models.TextField(
        blank=True,
        help_text="Descripción del contenido"
    )
    file = models.FileField(
        upload_to='documents_pdf/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        help_text="Archivo PDF"
    )
    version = models.CharField(
        max_length=50,
        blank=True,
        help_text="Versión del documento"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text="Estado del documento"
    )
    tags = models.CharField(
        max_length=500,
        blank=True,
        help_text="Etiquetas separadas por comas (ej: becas,postgrado,2024)"
    )
    is_public = models.BooleanField(
        default=False,
        help_text="¿Documento público para descarga?"
    )
    file_size = models.BigIntegerField(
        default=0,
        help_text="Tamaño del archivo en bytes"
    )
    page_count = models.IntegerField(
        default=0,
        blank=True,
        help_text="Número de páginas del PDF"
    )
    processed_for_vectordb = models.BooleanField(
        default=False,
        help_text="¿Procesado en la base de datos vectorial?"
    )
    
    # Relación opcional con corpus JSON
    related_corpus = models.ForeignKey(
        JSONCorpus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_pdfs',
        help_text="Corpus JSON relacionado (opcional)"
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text="Fecha de creación"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Última actualización"
    )
    created_by = models.CharField(
        max_length=100,
        blank=True,
        help_text="Usuario que subió el documento"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Documento PDF"
        verbose_name_plural = "Documentos PDF"
        indexes = [
            models.Index(fields=['document_type', 'status']),
            models.Index(fields=['is_public']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        """Guarda metadatos automáticamente."""
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    def get_file_size_mb(self):
        """Retorna el tamaño del archivo en MB."""
        return round(self.file_size / (1024 * 1024), 2)
    
    def get_tags_list(self):
        """Retorna las etiquetas como lista."""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []
    
    def delete(self, *args, **kwargs):
        """Elimina el archivo físico al borrar el registro."""
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)


class FileVersion(models.Model):
    """
    Modelo para mantener historial de versiones de archivos.
    Permite rastrear cambios tanto en JSON como en PDF.
    """
    
    CONTENT_TYPES = [
        ('json_corpus', 'Corpus JSON'),
        ('pdf_document', 'Documento PDF'),
    ]
    
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPES,
        help_text="Tipo de contenido versionado"
    )
    object_id = models.IntegerField(
        help_text="ID del objeto versionado"
    )
    version_number = models.CharField(
        max_length=50,
        help_text="Número de versión"
    )
    file_backup = models.FileField(
        upload_to='versions/%Y/%m/',
        help_text="Copia de respaldo del archivo"
    )
    change_description = models.TextField(
        blank=True,
        help_text="Descripción de los cambios"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text="Fecha de creación de la versión"
    )
    created_by = models.CharField(
        max_length=100,
        blank=True,
        help_text="Usuario que creó la versión"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Versión de Archivo"
        verbose_name_plural = "Versiones de Archivos"
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.get_content_type_display()} v{self.version_number} - {self.created_at.strftime('%Y-%m-%d')}"
    
    def delete(self, *args, **kwargs):
        """Elimina el archivo de respaldo al borrar."""
        if self.file_backup:
            if os.path.isfile(self.file_backup.path):
                os.remove(self.file_backup.path)
        super().delete(*args, **kwargs)
