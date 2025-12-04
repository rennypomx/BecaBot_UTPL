"""
Configuración del panel de administración de Django.
Incluye administración avanzada de archivos JSON y PDF.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from myapp.models import (
    ChatMessage, 
    UploadedDocument, 
    ScrapingLog,
    JSONCorpus,
    PDFDocument,
    FileVersion
)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """Admin para mensajes de chat."""
    list_display = ['id', 'session_key_short', 'role', 'content_preview', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['session_key', 'content']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def session_key_short(self, obj):
        return obj.session_key[:8] + '...'
    session_key_short.short_description = 'Sesión'
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Contenido'


@admin.register(UploadedDocument)
class UploadedDocumentAdmin(admin.ModelAdmin):
    """Admin para documentos subidos (Legacy)."""
    list_display = ['id', 'filename', 'session_key_short', 'processed', 'uploaded_at']
    list_filter = ['processed', 'uploaded_at']
    search_fields = ['filename', 'session_key']
    date_hierarchy = 'uploaded_at'
    ordering = ['-uploaded_at']
    
    def session_key_short(self, obj):
        return obj.session_key[:8] + '...'
    session_key_short.short_description = 'Sesión'


@admin.register(ScrapingLog)
class ScrapingLogAdmin(admin.ModelAdmin):
    """Admin para logs de scraping."""
    list_display = ['id', 'executed_at', 'success', 'num_becas', 'error_preview']
    list_filter = ['success', 'executed_at']
    search_fields = ['error_message']
    date_hierarchy = 'executed_at'
    ordering = ['-executed_at']
    
    def error_preview(self, obj):
        if obj.error_message:
            return obj.error_message[:50] + '...' if len(obj.error_message) > 50 else obj.error_message
        return '-'
    error_preview.short_description = 'Error'


# ============================================================================
# ADMINISTRACIÓN AVANZADA DE ARCHIVOS
# ============================================================================

@admin.register(JSONCorpus)
class JSONCorpusAdmin(admin.ModelAdmin):
    """
    Administración avanzada de corpus JSON.
    Incluye filtros, búsqueda, acciones en lote y visualización mejorada.
    """
    
    list_display = [
        'id',
        'name',
        'corpus_type_badge',
        'status_badge',
        'version',
        'records_count',
        'file_size_display',
        'download_link',
        'created_at',
    ]
    
    list_filter = [
        'corpus_type',
        'is_active',
        'created_at',
    ]
    
    search_fields = [
        'name',
        'description',
        'version',
        'created_by',
    ]
    
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    readonly_fields = [
        'file_size',
        'records_count',
        'created_at',
        'updated_at',
        'file_preview',
        'version_history_link',
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'corpus_type', 'description', 'version')
        }),
        ('Archivo', {
            'fields': ('file', 'file_preview')
        }),
        ('Metadatos', {
            'fields': ('records_count', 'file_size', 'is_active'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Versionado', {
            'fields': ('version_history_link',),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'activate_corpus',
        'deactivate_corpus',
        'create_backup_version',
    ]
    
    def corpus_type_badge(self, obj):
        """Muestra el tipo de corpus con color."""
        colors = {
            'becas': '#28a745',
            'faqs': '#17a2b8',
            'general': '#6c757d',
            'custom': '#ffc107',
        }
        color = colors.get(obj.corpus_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_corpus_type_display()
        )
    corpus_type_badge.short_description = 'Tipo'
    
    def status_badge(self, obj):
        """Muestra el estado activo/inactivo."""
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Activo</span>'
            )
        return format_html(
            '<span style="color: red;">✗ Inactivo</span>'
        )
    status_badge.short_description = 'Estado'
    
    def file_size_display(self, obj):
        """Muestra el tamaño del archivo en formato legible."""
        size_mb = obj.get_file_size_mb()
        if size_mb < 1:
            return f"{round(size_mb * 1024, 2)} KB"
        return f"{size_mb} MB"
    file_size_display.short_description = 'Tamaño'
    
    def download_link(self, obj):
        """Enlace para descargar el archivo."""
        try:
            if obj.file and hasattr(obj.file, 'url') and obj.file.name:
                return format_html(
                    '<a href="{}" target="_blank" style="color: #007bff;">📥 Descargar</a>',
                    obj.file.url
                )
        except (ValueError, AttributeError, Exception):
            pass
        return format_html('<span style="color: #999;">-</span>')
    download_link.short_description = 'Descarga'
    
    def file_preview(self, obj):
        """Vista previa del contenido JSON (primeros registros)."""
        if not obj.file:
            return format_html('<span style="color: #999;">No hay archivo</span>')
        
        try:
            import json
            with obj.file.open('r', encoding='utf-8') as f:
                content = json.load(f)
            
            # Mostrar solo los primeros 3 elementos si es una lista
            if isinstance(content, list):
                preview = content[:3]
            else:
                preview = content
            
            json_str = json.dumps(preview, indent=2, ensure_ascii=False)
            
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; '
                'border-radius: 5px; max-height: 300px; overflow-y: auto;">{}</pre>',
                json_str
            )
        except Exception as e:
            return format_html(
                '<span style="color: red;">Error al cargar preview: {}</span>',
                str(e)
            )
    file_preview.short_description = 'Vista Previa'
    
    def version_history_link(self, obj):
        """Enlace al historial de versiones."""
        if not obj.pk:
            return format_html('<span style="color: #999;">Guarda primero para ver versiones</span>')
        
        versions_count = FileVersion.objects.filter(
            content_type='json_corpus',
            object_id=obj.id
        ).count()
        
        if versions_count > 0:
            return format_html(
                '<a href="{}?content_type=json_corpus&object_id={}">'
                '📚 Ver {} versión(es) anteriores</a>',
                reverse('admin:myapp_fileversion_changelist'),
                obj.id,
                versions_count
            )
        return format_html('<span style="color: #999;">Sin versiones anteriores</span>')
    version_history_link.short_description = 'Historial de Versiones'
    
    def activate_corpus(self, request, queryset):
        """Activa los corpus seleccionados."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} corpus activados.')
    activate_corpus.short_description = '✓ Activar corpus seleccionados'
    
    def deactivate_corpus(self, request, queryset):
        """Desactiva los corpus seleccionados."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} corpus desactivados.')
    deactivate_corpus.short_description = '✗ Desactivar corpus seleccionados'
    
    def create_backup_version(self, request, queryset):
        """Crea versiones de backup de los corpus seleccionados."""
        from myapp.services.file_manager_service import FileManagerService
        
        created = 0
        for corpus in queryset:
            version = FileManagerService._create_version_backup(
                content_type='json_corpus',
                object_id=corpus.id,
                old_file=corpus.file,
                version=corpus.version or 'backup',
                description='Backup manual desde admin'
            )
            if version:
                created += 1
        
        self.message_user(request, f'{created} backups creados.')
    create_backup_version.short_description = '💾 Crear backup de seleccionados'


@admin.register(PDFDocument)
class PDFDocumentAdmin(admin.ModelAdmin):
    """
    Administración avanzada de documentos PDF.
    Incluye gestión de estado, versionado y metadatos.
    """
    
    list_display = [
        'id',
        'title',
        'document_type_badge',
        'status_badge',
        'version',
        'page_count',
        'file_size_display',
        'public_badge',
        'download_link',
        'created_at',
    ]
    
    list_filter = [
        'document_type',
        'status',
        'is_public',
        'processed_for_vectordb',
        'created_at',
    ]
    
    search_fields = [
        'title',
        'description',
        'tags',
        'created_by',
    ]
    
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    readonly_fields = [
        'file_size',
        'page_count',
        'created_at',
        'updated_at',
        'pdf_preview',
        'version_history_link',
        'tags_display',
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'document_type', 'description', 'version', 'status')
        }),
        ('Archivo', {
            'fields': ('file', 'pdf_preview')
        }),
        ('Clasificación', {
            'fields': ('tags', 'tags_display', 'is_public'),
        }),
        ('Metadatos', {
            'fields': ('page_count', 'file_size', 'processed_for_vectordb'),
            'classes': ('collapse',)
        }),
        ('Relaciones', {
            'fields': ('related_corpus',),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Versionado', {
            'fields': ('version_history_link',),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = []
    
    actions = [
        'publish_documents',
        'archive_documents',
        'make_public',
        'make_private',
        'mark_as_processed',
        'create_backup_version',
    ]
    
    def document_type_badge(self, obj):
        """Badge para tipo de documento."""
        colors = {
            'report': '#007bff',
            'guide': '#28a745',
            'manual': '#17a2b8',
            'regulations': '#dc3545',
            'form': '#ffc107',
            'other': '#6c757d',
        }
        color = colors.get(obj.document_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_document_type_display()
        )
    document_type_badge.short_description = 'Tipo'
    
    def status_badge(self, obj):
        """Badge para estado del documento."""
        colors = {
            'draft': '#6c757d',
            'published': '#28a745',
            'archived': '#ffc107',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def public_badge(self, obj):
        """Badge para visibilidad pública."""
        if obj.is_public:
            return format_html('<span style="color: green;">🌐 Público</span>')
        return format_html('<span style="color: gray;">🔒 Privado</span>')
    public_badge.short_description = 'Visibilidad'
    
    def file_size_display(self, obj):
        """Tamaño del archivo en formato legible."""
        size_mb = obj.get_file_size_mb()
        if size_mb < 1:
            return f"{round(size_mb * 1024, 2)} KB"
        return f"{size_mb} MB"
    file_size_display.short_description = 'Tamaño'
    
    def download_link(self, obj):
        """Enlace de descarga."""
        try:
            if obj.file and hasattr(obj.file, 'url') and obj.file.name:
                return format_html(
                    '<a href="{}" target="_blank" style="color: #007bff;">📥 Descargar</a>',
                    obj.file.url
                )
        except (ValueError, AttributeError, Exception):
            pass
        return format_html('<span style="color: #999;">-</span>')
    download_link.short_description = 'Descarga'
    
    def pdf_preview(self, obj):
        """Vista previa del PDF (info)."""
        if not obj.file or not obj.file.name:
            return format_html('<span style="color: #999;">No hay archivo</span>')
        
        try:
            file_url = obj.file.url
            file_path = obj.file.path if hasattr(obj.file, 'path') else 'N/A'
        except (ValueError, AttributeError, Exception) as e:
            return format_html('<span style="color: red;">Archivo no disponible: {}</span>', str(e))
        
        info = f"""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
            <p><strong>Archivo:</strong> {obj.file.name}</p>
            <p><strong>Tamaño:</strong> {self.file_size_display(obj)}</p>
            <p><strong>Páginas:</strong> {obj.page_count or 'No disponible'}</p>
            <p><strong>Ruta:</strong> <code>{file_path}</code></p>
            <p><a href="{file_url}" target="_blank" class="button">Ver PDF</a></p>
        </div>
        """
        return mark_safe(info)
    pdf_preview.short_description = 'Información del PDF'
    
    def tags_display(self, obj):
        """Muestra las tags como badges."""
        tags = obj.get_tags_list()
        if not tags:
            return format_html('<span style="color: #999;">Sin etiquetas</span>')
        
        badges = ''.join([
            f'<span style="background: #e9ecef; padding: 3px 8px; margin: 2px; '
            f'border-radius: 3px; display: inline-block; font-size: 11px;">{tag}</span>'
            for tag in tags
        ])
        return mark_safe(badges)
    tags_display.short_description = 'Etiquetas'
    
    def version_history_link(self, obj):
        """Enlace al historial de versiones."""
        if not obj.pk:
            return format_html('<span style="color: #999;">Guarda primero para ver versiones</span>')
        
        versions_count = FileVersion.objects.filter(
            content_type='pdf_document',
            object_id=obj.id
        ).count()
        
        if versions_count > 0:
            return format_html(
                '<a href="{}?content_type=pdf_document&object_id={}">'
                '📚 Ver {} versión(es) anteriores</a>',
                reverse('admin:myapp_fileversion_changelist'),
                obj.id,
                versions_count
            )
        return format_html('<span style="color: #999;">Sin versiones anteriores</span>')
    version_history_link.short_description = 'Historial de Versiones'
    
    # Acciones en lote
    def publish_documents(self, request, queryset):
        """Publica los documentos seleccionados."""
        updated = queryset.update(status='published')
        self.message_user(request, f'{updated} documentos publicados.')
    publish_documents.short_description = '📢 Publicar documentos'
    
    def archive_documents(self, request, queryset):
        """Archiva los documentos seleccionados."""
        updated = queryset.update(status='archived')
        self.message_user(request, f'{updated} documentos archivados.')
    archive_documents.short_description = '📦 Archivar documentos'
    
    def make_public(self, request, queryset):
        """Hace públicos los documentos."""
        updated = queryset.update(is_public=True)
        self.message_user(request, f'{updated} documentos ahora son públicos.')
    make_public.short_description = '🌐 Hacer públicos'
    
    def make_private(self, request, queryset):
        """Hace privados los documentos."""
        updated = queryset.update(is_public=False)
        self.message_user(request, f'{updated} documentos ahora son privados.')
    make_private.short_description = '🔒 Hacer privados'
    
    def mark_as_processed(self, request, queryset):
        """Marca como procesados en vectorDB."""
        updated = queryset.update(processed_for_vectordb=True)
        self.message_user(request, f'{updated} documentos marcados como procesados.')
    mark_as_processed.short_description = '✓ Marcar como procesados'
    
    def create_backup_version(self, request, queryset):
        """Crea versiones de backup."""
        from myapp.services.file_manager_service import FileManagerService
        
        created = 0
        for doc in queryset:
            version = FileManagerService._create_version_backup(
                content_type='pdf_document',
                object_id=doc.id,
                old_file=doc.file,
                version=doc.version or 'backup',
                description='Backup manual desde admin'
            )
            if version:
                created += 1
        
        self.message_user(request, f'{created} backups creados.')
    create_backup_version.short_description = '💾 Crear backup'


@admin.register(FileVersion)
class FileVersionAdmin(admin.ModelAdmin):
    """
    Administración de versiones de archivos.
    Permite ver y restaurar versiones anteriores.
    """
    
    list_display = [
        'id',
        'content_type_badge',
        'version_number',
        'file_link',
        'created_at',
        'created_by',
        'restore_button',
    ]
    
    list_filter = [
        'content_type',
        'created_at',
    ]
    
    search_fields = [
        'version_number',
        'change_description',
        'created_by',
    ]
    
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    readonly_fields = [
        'content_type',
        'object_id',
        'version_number',
        'file_backup',
        'created_at',
        'created_by',
        'original_object_link',
    ]
    
    def content_type_badge(self, obj):
        """Badge para tipo de contenido."""
        if obj.content_type == 'json_corpus':
            return format_html(
                '<span style="background: #17a2b8; color: white; padding: 3px 10px; '
                'border-radius: 3px;">📄 JSON</span>'
            )
        return format_html(
            '<span style="background: #dc3545; color: white; padding: 3px 10px; '
            'border-radius: 3px;">📕 PDF</span>'
        )
    content_type_badge.short_description = 'Tipo'
    
    def file_link(self, obj):
        """Enlace al archivo de backup."""
        try:
            if obj.file_backup and hasattr(obj.file_backup, 'url') and obj.file_backup.name:
                return format_html(
                    '<a href="{}" target="_blank">📥 Descargar</a>',
                    obj.file_backup.url
                )
        except (ValueError, AttributeError, Exception):
            pass
        return format_html('<span style="color: #999;">-</span>')
    file_link.short_description = 'Archivo'
    
    def restore_button(self, obj):
        """Botón para restaurar versión (placeholder)."""
        # TODO: Implementar vista para restaurar
        return format_html('<span style="color: #6c757d;">⟲ Restaurar</span>')
    restore_button.short_description = 'Acción'
    
    def original_object_link(self, obj):
        """Enlace al objeto original."""
        if obj.content_type == 'json_corpus':
            try:
                corpus = JSONCorpus.objects.get(id=obj.object_id)
                url = reverse('admin:myapp_jsoncorpus_change', args=[corpus.id])
                return format_html('<a href="{}">Ver Corpus Original</a>', url)
            except JSONCorpus.DoesNotExist:
                return format_html('<span style="color: #999;">Objeto eliminado</span>')
        elif obj.content_type == 'pdf_document':
            try:
                doc = PDFDocument.objects.get(id=obj.object_id)
                url = reverse('admin:myapp_pdfdocument_change', args=[doc.id])
                return format_html('<a href="{}">Ver Documento Original</a>', url)
            except PDFDocument.DoesNotExist:
                return format_html('<span style="color: #999;">Objeto eliminado</span>')
        return format_html('<span style="color: #999;">-</span>')
    original_object_link.short_description = 'Objeto Original'
