"""
Vistas de Django para BecaBot UTPL.
Arquitectura limpia separando presentación de lógica de negocio.
Adaptadas para usar el template existente en myapp/template/index.html
"""
from django.shortcuts import render


def is_ajax(request):
    """Helper para detectar peticiones AJAX"""
    return request.headers.get("x-requested-with") == "XMLHttpRequest" or \
           request.headers.get("X-Requested-With") == "XMLHttpRequest"


def render_partial_or_base(request, partial_name, context=None, base_template='admin_base.html'):
    """
    Renderiza un partial si es petición AJAX, o el template base si no lo es.
    
    Args:
        request: HttpRequest object
        partial_name: Nombre del archivo partial (ej: 'admin_panel')
        context: Diccionario de contexto para el template
        base_template: Template base a usar si no es AJAX
    """
    if context is None:
        context = {}
    
    if is_ajax(request):
        return render(request, f"partials/{partial_name}.html", context)
    else:
        # Primera carga: renderizar el partial dentro del admin_base
        from django.template.loader import render_to_string
        partial_html = render_to_string(f"partials/{partial_name}.html", context, request=request)
        context['initial_content'] = partial_html
        return render(request, base_template, context)


def index(request):
    return render(request, 'index.html')


def admin_panel(request):
    """Panel principal de administración."""
    try:
        from myapp.models import ChatMessage, JSONCorpus, PDFDocument, ScrapingLog
        from django.db.models import Sum
        import os
        
        # Estadísticas de Corpus JSON
        total_corpus = JSONCorpus.objects.count()
        active_corpus = JSONCorpus.objects.filter(is_active=True).count()
        
        # Estadísticas de PDFs
        total_pdfs = PDFDocument.objects.count()
        public_pdfs = PDFDocument.objects.filter(is_public=True).count()
        
        # Estadísticas de Mensajes
        total_messages = ChatMessage.objects.count()
        active_sessions = ChatMessage.objects.values('session_key').distinct().count()
        
        # Estadísticas de Scraping
        total_scrapings = ScrapingLog.objects.filter(success=True).count()
        last_scraping = ScrapingLog.objects.filter(success=True).order_by('-executed_at').first()
        
        # Calcular espacio usado (aproximado)
        total_size = 0
        # Tamaño de corpus
        corpus_size = JSONCorpus.objects.aggregate(total=Sum('file_size'))['total'] or 0
        # Tamaño de PDFs
        pdf_size = PDFDocument.objects.aggregate(total=Sum('file_size'))['total'] or 0
        total_size = (corpus_size + pdf_size) / (1024 * 1024)  # Convertir a MB
        
        stats = {
            'total_corpus': total_corpus,
            'active_corpus': active_corpus,
            'total_pdfs': total_pdfs,
            'public_pdfs': public_pdfs,
            'total_messages': total_messages,
            'total_scrapings': total_scrapings,
            'total_size_mb': round(total_size, 2),
            'active_sessions': active_sessions
        }
        
        # Actividad reciente
        recent_corpus = JSONCorpus.objects.all().order_by('-created_at')[:5]
        recent_pdfs = PDFDocument.objects.all().order_by('-created_at')[:5]
        
        context = {
            'stats': stats,
            'recent_corpus': recent_corpus,
            'recent_pdfs': recent_pdfs,
            'last_scraping': last_scraping,
            'section': 'dashboard',
        }
        
        print(f"Dashboard Stats: {stats}", flush=True)
        return render_partial_or_base(request, 'admin_panel', context)
        
    except Exception as e:
        print(f"Error en admin_panel: {e}", flush=True)
        import traceback
        traceback.print_exc()
        # Retornar con estadísticas vacías en caso de error
        context = {
            'stats': {
                'total_corpus': 0,
                'active_corpus': 0,
                'total_pdfs': 0,
                'public_pdfs': 0,
                'total_messages': 0,
                'total_scrapings': 0,
                'total_size_mb': 0,
                'active_sessions': 0
            },
            'recent_corpus': [],
            'recent_pdfs': [],
            'last_scraping': None,
            'section': 'dashboard',
        }
        return render_partial_or_base(request, 'admin_panel', context)


def admin_corpus(request):
    """Lista de corpus JSON."""
    from myapp.models import JSONCorpus
    
    # Obtener filtros
    corpus_type = request.GET.get('corpus_type', '')
    is_active = request.GET.get('is_active', '')
    
    # Query base
    corpus_list = JSONCorpus.objects.all().order_by('-created_at')
    
    # Aplicar filtros
    if corpus_type:
        corpus_list = corpus_list.filter(corpus_type=corpus_type)
    
    if is_active:
        corpus_list = corpus_list.filter(is_active=(is_active == 'true'))
    
    context = {
        'corpus_list': corpus_list,
        'section': 'corpus',
        'filters': {
            'corpus_type': corpus_type,
            'is_active': is_active,
        }
    }
    return render_partial_or_base(request, 'admin_corpus', context)


def admin_corpus_upload(request):
    """Subir nuevo corpus JSON."""
    from myapp.models import JSONCorpus
    import json
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            corpus_type = request.POST.get('corpus_type')
            description = request.POST.get('description', '')
            version = request.POST.get('version', '1.0')
            is_active = request.POST.get('is_active') == 'on'
            file = request.FILES.get('file')
            
            # Validar que el archivo sea JSON válido
            if file:
                content = file.read().decode('utf-8')
                data = json.loads(content)  # Validar JSON
                file.seek(0)  # Resetear para guardarlo
                
                # Contar registros
                num_records = len(data) if isinstance(data, list) else 1
            else:
                messages.error(request, 'Debe seleccionar un archivo')
                return redirect('admin_corpus_upload')
            
            # Crear corpus
            corpus = JSONCorpus.objects.create(
                name=name,
                corpus_type=corpus_type,
                description=description,
                version=version,
                file=file,
                records_count=num_records,
                file_size=file.size,
                is_active=is_active,
                created_by='admin'
            )
            
            messages.success(request, f'✓ Corpus "{name}" creado exitosamente')
            return redirect('admin_corpus')
            
        except json.JSONDecodeError:
            messages.error(request, 'El archivo no es un JSON válido')
        except Exception as e:
            messages.error(request, f'Error al crear corpus: {str(e)}')
            print(f"Error en admin_corpus_upload: {e}", flush=True)
    
    return render_partial_or_base(request, 'admin_corpus_upload', {})


def admin_corpus_view(request, pk):
    """Ver detalles de un corpus."""
    from myapp.models import JSONCorpus
    
    try:
        corpus = JSONCorpus.objects.get(pk=pk)
        
        # Preview del contenido JSON
        preview_data = None
        if corpus.file:
            try:
                import json
                with corpus.file.open('r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        preview_data = data[:3]  # Primeros 3 elementos
                    else:
                        preview_data = data
            except Exception as e:
                print(f"Error al cargar preview: {e}", flush=True)
        
        context = {
            'corpus': corpus,
            'preview_data': preview_data,
            'section': 'corpus',
        }
        return render_partial_or_base(request, 'admin_corpus_view', context)
        
    except JSONCorpus.DoesNotExist:
        messages.error(request, 'Corpus no encontrado')
        return redirect('admin_corpus')


def admin_corpus_edit(request, pk):
    """Editar un corpus."""
    from myapp.models import JSONCorpus
    import json
    
    try:
        corpus = JSONCorpus.objects.get(pk=pk)
        
        if request.method == 'POST':
            try:
                corpus.name = request.POST.get('name', corpus.name)
                corpus.corpus_type = request.POST.get('corpus_type', corpus.corpus_type)
                corpus.description = request.POST.get('description', corpus.description)
                corpus.version = request.POST.get('version', corpus.version)
                corpus.is_active = request.POST.get('is_active') == 'on'
                
                # Si hay nuevo archivo
                new_file = request.FILES.get('file')
                if new_file:
                    # Validar JSON
                    content = new_file.read().decode('utf-8')
                    data = json.loads(content)
                    new_file.seek(0)
                    
                    corpus.file = new_file
                    corpus.records_count = len(data) if isinstance(data, list) else 1
                    corpus.file_size = new_file.size
                
                corpus.save()
                messages.success(request, f'✓ Corpus "{corpus.name}" actualizado')
                return redirect('admin_corpus_view', pk=pk)
                
            except json.JSONDecodeError:
                messages.error(request, 'El archivo no es un JSON válido')
            except Exception as e:
                messages.error(request, f'Error al actualizar: {str(e)}')
                print(f"Error en admin_corpus_edit: {e}", flush=True)
        
        context = {
            'corpus': corpus,
            'section': 'corpus',
        }
        return render_partial_or_base(request, 'admin_corpus_edit', context)
        
    except JSONCorpus.DoesNotExist:
        messages.error(request, 'Corpus no encontrado')
        return redirect('admin_corpus')


def admin_corpus_toggle(request, pk):
    """Activar/Desactivar corpus."""
    from myapp.models import JSONCorpus
    
    if request.method == 'POST':
        try:
            corpus = JSONCorpus.objects.get(pk=pk)
            corpus.is_active = not corpus.is_active
            corpus.save()
            
            status = 'activado' if corpus.is_active else 'desactivado'
            messages.success(request, f'✓ Corpus "{corpus.name}" {status}')
            
        except JSONCorpus.DoesNotExist:
            messages.error(request, 'Corpus no encontrado')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('admin_corpus')


def admin_corpus_delete(request, pk):
    """Eliminar corpus."""
    from myapp.models import JSONCorpus
    
    if request.method == 'POST':
        try:
            corpus = JSONCorpus.objects.get(pk=pk)
            name = corpus.name
            corpus.delete()
            messages.success(request, f'✓ Corpus "{name}" eliminado')
            
        except JSONCorpus.DoesNotExist:
            messages.error(request, 'Corpus no encontrado')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('admin_corpus')


def admin_pdf(request):
    """Lista de PDFs."""
    try:
        from myapp.models import PDFDocument
        pdf_list = PDFDocument.objects.all().order_by('-created_at')
    except Exception as e:
        print(f"Error al cargar PDFs: {e}")
        pdf_list = []
    
    context = {
        'pdf_list': pdf_list,
        'section': 'pdf',
    }
    return render_partial_or_base(request, 'admin_pdf', context)


def admin_pdf_upload(request):
    """Subir nuevo PDF."""
    if request.method == 'POST':
        try:
            from myapp.models import PDFDocument
            from myapp.services.document_service import DocumentService
            from myapp.services.vectordb_service import VectorDBService
            import os
            
            # Obtener datos del formulario
            title = request.POST.get('title')
            document_type = request.POST.get('document_type')
            description = request.POST.get('description', '')
            status = request.POST.get('status', 'draft')
            is_public = request.POST.get('is_public') == 'on'
            file = request.FILES.get('file')
            
            if not title or not file:
                messages.error(request, 'Título y archivo son obligatorios')
                return redirect('admin_pdf_upload')
            
            # Crear registro en base de datos
            pdf_doc = PDFDocument.objects.create(
                title=title,
                document_type=document_type,
                description=description,
                status=status,
                is_public=is_public,
                file=file,
                file_size=file.size
            )
            
            # Guardar también en carpeta docs/ para la vectordb
            doc_service = DocumentService()
            doc_service.save_uploaded_files([file])
            
            # Regenerar base vectorial
            pdf_files = doc_service.get_existing_documents()
            vectordb_service = VectorDBService()
            vectordb_service.get_vectorstore(pdf_files, force_regenerate=True)
            
            # Marcar como procesado
            pdf_doc.processed_for_vectordb = True
            pdf_doc.save()
            
            messages.success(request, f'Documento "{title}" subido correctamente')
            return redirect('admin_pdf')
            
        except Exception as e:
            messages.error(request, f'Error al subir documento: {str(e)}')
            return redirect('admin_pdf_upload')
    
    return render_partial_or_base(request, 'admin_pdf_upload', {})


def admin_pdf_view(request, pk=None):
    """Ver detalles de un PDF."""
    try:
        from myapp.models import PDFDocument
        pdf = PDFDocument.objects.get(pk=pk)
        context = {'pk': pk, 'pdf': pdf}
    except:
        context = {'pk': pk, 'pdf': None}
    return render_partial_or_base(request, 'admin_pdf_view', context)


def admin_pdf_edit(request, pk=None):
    """Editar un PDF."""
    try:
        from myapp.models import PDFDocument
        pdf = PDFDocument.objects.get(pk=pk)
        
        if request.method == 'POST':
            # Actualizar campos
            pdf.title = request.POST.get('title', pdf.title)
            pdf.document_type = request.POST.get('document_type', pdf.document_type)
            pdf.description = request.POST.get('description', pdf.description)
            pdf.status = request.POST.get('status', pdf.status)
            pdf.is_public = request.POST.get('is_public') == 'on'
            pdf.save()
            
            messages.success(request, f'Documento "{pdf.title}" actualizado correctamente')
            return redirect('admin_pdf')
        
        context = {'pk': pk, 'pdf': pdf}
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        context = {'pk': pk, 'pdf': None}
    
    return render_partial_or_base(request, 'admin_pdf_edit', context)


def admin_pdf_delete(request, pk):
    """Eliminar un PDF."""
    if request.method == 'POST':
        try:
            from myapp.models import PDFDocument
            pdf = PDFDocument.objects.get(pk=pk)
            title = pdf.title
            pdf.delete()
            
            messages.success(request, f'Documento "{title}" eliminado correctamente')
        except Exception as e:
            messages.error(request, f'Error al eliminar: {str(e)}')
    
    return redirect('admin_pdf')


def admin_messages(request):
    """Historial de mensajes del chatbot."""
    from myapp.models import ChatMessage
    from django.db.models import Count
    
    # Obtener filtros
    session_key = request.GET.get('session', '')
    role = request.GET.get('role', '')
    search = request.GET.get('search', '')
    
    # Query base
    messages_list = ChatMessage.objects.all().order_by('-created_at')
    
    # Aplicar filtros
    if session_key:
        messages_list = messages_list.filter(session_key=session_key)
    
    if role:
        messages_list = messages_list.filter(role=role)
    
    if search:
        messages_list = messages_list.filter(content__icontains=search)
    
    # Limitar a los últimos 100 mensajes para no sobrecargar
    messages_list = messages_list[:100]
    
    # Obtener lista de sesiones únicas para el filtro
    sessions = ChatMessage.objects.values('session_key').annotate(
        message_count=Count('id')
    ).order_by('-message_count')[:20]
    
    # Estadísticas
    stats = {
        'total_messages': ChatMessage.objects.count(),
        'total_sessions': ChatMessage.objects.values('session_key').distinct().count(),
        'human_messages': ChatMessage.objects.filter(role='human').count(),
        'ai_messages': ChatMessage.objects.filter(role='ai').count(),
    }
    
    context = {
        'messages_list': messages_list,
        'sessions': sessions,
        'stats': stats,
        'filters': {
            'session': session_key,
            'role': role,
            'search': search,
        },
        'section': 'messages',
    }
    return render_partial_or_base(request, 'admin_messages', context)


def admin_messages_clear(request):
    """Limpiar todos los mensajes del historial."""
    from myapp.models import ChatMessage
    
    if request.method == 'POST':
        try:
            count = ChatMessage.objects.count()
            ChatMessage.objects.all().delete()
            messages.success(request, f'✓ {count} mensajes eliminados correctamente')
            print(f"Se eliminaron {count} mensajes del historial", flush=True)
        except Exception as e:
            messages.error(request, f'Error al eliminar mensajes: {str(e)}')
            print(f"Error al eliminar mensajes: {e}", flush=True)
    
    return redirect('admin_messages')


def admin_scraping(request):
    """Vista de scraping con historial."""
    try:
        from myapp.models import ScrapingLog
        logs = ScrapingLog.objects.all().order_by('-executed_at')[:20]
    except Exception as e:
        print(f"Error al cargar logs: {e}")
        logs = []
    
    context = {
        'logs': logs,
        'section': 'scraping',
    }
    return render_partial_or_base(request, 'admin_scraping', context)


def admin_run_scraping(request):
    """Ejecutar scraping de becas."""
    import logging
    logger = logging.getLogger(__name__)
    
    print("\n" + "="*60, flush=True)
    print("VISTA admin_run_scraping EJECUTADA", flush=True)
    print(f"Método: {request.method}", flush=True)
    print("="*60 + "\n", flush=True)
    
    logger.info("="*60)
    logger.info("VISTA admin_run_scraping EJECUTADA")
    logger.info(f"Método: {request.method}")
    logger.info("="*60)
    
    if request.method == 'POST':
        try:
            print("Iniciando proceso de scraping...", flush=True)
            logger.info("Iniciando proceso de scraping...")
            
            from myapp.services.scraper_service import ScraperService
            from myapp.services.vectordb_service import VectorDBService
            from myapp.services.document_service import DocumentService
            from myapp.models import ScrapingLog
            
            scraper_service = ScraperService()
            
            # Ejecutar scraping
            print("Llamando a scraper_service.scrape_becas()...", flush=True)
            logger.info("Llamando a scraper_service.scrape_becas()...")
            success, num_becas, error_msg = scraper_service.scrape_becas()
            print(f"Scraping completado: success={success}, num_becas={num_becas}", flush=True)
            logger.info(f"Scraping completado: success={success}, num_becas={num_becas}")
            
            # Guardar log
            log_entry = ScrapingLog.objects.create(
                success=success,
                num_becas=num_becas,
                error_message=error_msg if not success else None
            )
            print(f"Log guardado con ID: {log_entry.id}", flush=True)
            logger.info(f"Log guardado con ID: {log_entry.id}")
            
            if success:
                # Regenerar base vectorial con el nuevo corpus
                print("Regenerando base vectorial...", flush=True)
                logger.info("Regenerando base vectorial...")
                doc_service = DocumentService()
                pdf_files = doc_service.get_existing_documents()
                vectordb_service = VectorDBService()
                vectordb_service.get_vectorstore(pdf_files, force_regenerate=True)
                print("Base vectorial regenerada", flush=True)
                logger.info("Base vectorial regenerada")
                
                messages.success(request, f'✓ Actualización exitosa: {num_becas} becas procesadas')
            else:
                print(f"Error en scraping: {error_msg}", flush=True)
                logger.error(f"Error en scraping: {error_msg}")
                messages.error(request, f'✗ Error al actualizar: {error_msg}')
            
        except Exception as e:
            print(f"Excepción en admin_run_scraping: {str(e)}", flush=True)
            logger.error(f"Excepción en admin_run_scraping: {str(e)}", exc_info=True)
            messages.error(request, f'Error: {str(e)}')
    
    print("Redirigiendo a admin_scraping\n", flush=True)
    logger.info("Redirigiendo a admin_scraping")
    return redirect('admin_scraping')

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
import json

from myapp.forms import ChatForm, DocumentUploadForm
from myapp.models import ChatMessage, UploadedDocument, ScrapingLog
from myapp.services.chat_service import ChatService
from myapp.services.vectordb_service import VectorDBService
from myapp.services.document_service import DocumentService
from myapp.services.scraper_service import ScraperService


def home(request):
    """
    Vista principal del chatbot.
    Renderiza el template existente con la interfaz UTPL.
    """
    # Inicializar servicios
    scraper_service = ScraperService()
    
    # Obtener o crear session_key
    if not request.session.session_key:
        request.session.create()
    
    # Verificar si existe corpus de becas
    corpus_info = scraper_service.get_corpus_info()
    
    # Si no existe el corpus, crearlo automáticamente
    if not corpus_info:
        try:
            success, num_becas, error_msg = scraper_service.scrape_becas()
            if success:
                ScrapingLog.objects.create(
                    success=True,
                    num_becas=num_becas
                )
        except Exception as e:
            print(f"⚠️ Error al crear corpus inicial: {e}")
    
    # Renderizar el template existente
    return render(request, 'index.html')


@require_http_methods(["POST"])
def send_message(request):
    """
    Procesa un mensaje del usuario y retorna la respuesta del chatbot.
    Endpoint AJAX para comunicación asíncrona.
    """
    try:
        form = ChatForm(request.POST)
        
        if not form.is_valid():
            return JsonResponse({
                'success': False,
                'error': 'Mensaje inválido'
            }, status=400)
        
        message = form.cleaned_data['message']
        
        # Obtener o crear session_key
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        
        # Inicializar servicios
        chat_service = ChatService()
        vectordb_service = VectorDBService()
        doc_service = DocumentService()
        
        # Obtener vectordb
        pdf_files = doc_service.get_existing_documents()
        vectordb = vectordb_service.get_vectorstore(pdf_files, force_regenerate=False)
        
        if not vectordb:
            return JsonResponse({
                'success': False,
                'error': 'No se pudo inicializar la base de conocimiento'
            }, status=500)
        
        # Obtener historial previo
        previous_messages = ChatMessage.objects.filter(
            session_key=session_key
        ).order_by('created_at')
        
        # Convertir a formato LangChain
        langchain_history = chat_service.convert_to_langchain_messages([
            {'role': msg.role, 'content': msg.content}
            for msg in previous_messages
        ])
        
        # Obtener chain en caché si existe
        cached_chain = request.session.get('retrieval_chain')
        
        # Generar respuesta
        response, context_docs = chat_service.get_response(
            question=message,
            chat_history=langchain_history,
            vectordb=vectordb,
            retrieval_chain=cached_chain
        )
        
        # Guardar mensajes en la base de datos
        ChatMessage.objects.create(
            session_key=session_key,
            role='human',
            content=message
        )
        
        ChatMessage.objects.create(
            session_key=session_key,
            role='ai',
            content=response
        )
        
        # Extraer información de fuentes
        sources = chat_service.extract_source_info(context_docs)
        
        return JsonResponse({
            'success': True,
            'response': response,
            'sources': sources
        })
    
    except Exception as e:
        # Log del error para debugging
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ ERROR en send_message: {str(e)}")
        print(error_trace)
        
        return JsonResponse({
            'success': False,
            'error': f'Error del servidor: {str(e)}',
            'trace': error_trace if request.user.is_authenticated else None
        }, status=500)


@require_http_methods(["GET"])
def get_chat_history(request):
    """
    Retorna el historial de chat de la sesión actual.
    Útil para cargar mensajes previos al abrir el chat.
    """
    if not request.session.session_key:
        return JsonResponse({
            'success': True,
            'messages': []
        })
    
    session_key = request.session.session_key
    messages_qs = ChatMessage.objects.filter(
        session_key=session_key
    ).order_by('created_at')
    
    messages_data = [
        {
            'role': msg.role,
            'content': msg.content,
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        for msg in messages_qs
    ]
    
    return JsonResponse({
        'success': True,
        'messages': messages_data
    })


@require_http_methods(["POST"])
def upload_documents(request):
    """
    Procesa la subida de documentos PDF.
    """
    form = DocumentUploadForm(request.POST, request.FILES)
    
    if not form.is_valid():
        messages.error(request, 'Error al procesar los archivos')
        return redirect('home')
    
    files = request.FILES.getlist('pdf_files')
    
    if not files:
        messages.info(request, 'No se seleccionaron archivos')
        return redirect('home')
    
    # Procesar archivos
    doc_service = DocumentService()
    result = doc_service.save_uploaded_files(files)
    
    # Guardar registro en BD
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    
    for filename in result['saved_files']:
        UploadedDocument.objects.create(
            session_key=session_key,
            filename=filename,
            file_path=f"docs/{filename}",
            processed=False
        )
    
    # Regenerar base vectorial
    if result['saved_files']:
        vectordb_service = VectorDBService()
        pdf_files = doc_service.get_existing_documents()
        vectordb = vectordb_service.get_vectorstore(pdf_files, force_regenerate=True)
        
        # Marcar como procesados
        UploadedDocument.objects.filter(
            session_key=session_key,
            filename__in=result['saved_files']
        ).update(processed=True)
        
        # Limpiar chain en caché
        if 'retrieval_chain' in request.session:
            del request.session['retrieval_chain']
        
        messages.success(
            request,
            f"{len(result['saved_files'])} archivo(s) procesado(s) correctamente"
        )
    
    if result['skipped_files']:
        messages.info(
            request,
            f"{len(result['skipped_files'])} archivo(s) ya existían"
        )
    
    if result['errors']:
        for error in result['errors']:
            messages.error(request, error)
    
    return redirect('home')


@require_http_methods(["POST"])
def update_becas(request):
    """
    Ejecuta el web scraping para actualizar información de becas.
    """
    scraper_service = ScraperService()
    
    try:
        success, num_becas, error_msg = scraper_service.scrape_becas()
        
        # Registrar en log
        ScrapingLog.objects.create(
            success=success,
            num_becas=num_becas,
            error_message=error_msg
        )
        
        if success:
            # Regenerar base vectorial
            doc_service = DocumentService()
            vectordb_service = VectorDBService()
            pdf_files = doc_service.get_existing_documents()
            vectordb_service.get_vectorstore(pdf_files, force_regenerate=True)
            
            # Limpiar chain en caché
            if 'retrieval_chain' in request.session:
                del request.session['retrieval_chain']
            
            messages.success(
                request,
                f"Scraping completado: {num_becas} becas actualizadas"
            )
        else:
            messages.error(request, f"Error en scraping: {error_msg}")
    
    except Exception as e:
        messages.error(request, f"Error al actualizar becas: {str(e)}")
    
    return redirect('home')


@require_http_methods(["POST"])
def clear_chat(request):
    """
    Limpiar el historial de chat de la sesión actual.
    Puede ser llamado manualmente o por timeout automático.
    """
    try:
        if not request.session.session_key:
            return JsonResponse({
                'success': True,
                'message': 'No hay sesión activa',
                'messages_deleted': 0
            })

        session_key = request.session.session_key
        
        # Contar mensajes antes de eliminar
        count = ChatMessage.objects.filter(session_key=session_key).count()
        
        # Eliminar mensajes de esta sesión
        ChatMessage.objects.filter(session_key=session_key).delete()

        # Limpiar chain en caché
        if 'retrieval_chain' in request.session:
            del request.session['retrieval_chain']
        
        # Limpiar otros datos de sesión relacionados con el chat
        if 'chat_context' in request.session:
            del request.session['chat_context']

        print(f"🗑️ Sesión {session_key[:8]}... limpiada ({count} mensajes eliminados)", flush=True)
        
        return JsonResponse({
            'success': True,
            'message': 'Conversación limpiada exitosamente',
            'messages_deleted': count
        })
        
    except Exception as e:
        print(f"❌ Error al limpiar chat: {e}", flush=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def test_bot(request):
    """
    Endpoint de prueba para verificar que los servicios funcionan.
    Acceder en: http://127.0.0.1:8000/test-bot/
    """
    try:
        from myapp.services.chat_service import ChatService
        from myapp.services.vectordb_service import VectorDBService
        from myapp.services.document_service import DocumentService
        
        results = {
            'chat_service': 'No probado',
            'vectordb_service': 'No probado',
            'document_service': 'No probado',
            'env_loaded': False,
            'api_key_exists': False,
        }
        
        # Verificar .env
        import os
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('GOOGLE_API_KEY')
        results['env_loaded'] = True
        results['api_key_exists'] = bool(api_key)
        results['api_key_preview'] = f"{api_key[:10]}..." if api_key else "No existe"
        
        # Probar DocumentService
        doc_service = DocumentService()
        pdf_files = doc_service.get_existing_documents()
        results['document_service'] = f'OK - {len(pdf_files)} PDFs encontrados'
        
        # Probar VectorDBService
        vectordb_service = VectorDBService()
        vectordb = vectordb_service.get_vectorstore(pdf_files, force_regenerate=False)
        results['vectordb_service'] = 'OK' if vectordb else 'Error: VectorDB es None'
        
        # Probar ChatService
        chat_service = ChatService()
        results['chat_service'] = 'OK - Servicio inicializado'
        
        return JsonResponse({
            'success': True,
            'message': 'Prueba completada',
            'results': results
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'trace': traceback.format_exc()
        }, status=500)


@require_http_methods(["POST", "GET"])
def regenerate_vectordb(request):
    """
    Regenera la base vectorial incluyendo todos los PDFs y el corpus JSON.
    Útil cuando se agregan PDFs manualmente a la carpeta docs.
    """
    try:
        from myapp.services.vectordb_service import VectorDBService
        from myapp.services.document_service import DocumentService
        import shutil
        
        doc_service = DocumentService()
        pdf_files = doc_service.get_existing_documents()
        
        # Verificar si hay corpus JSON
        import os
        json_path = "knowledge_base/corpus_utpl.json"
        has_corpus = os.path.exists(json_path)
        
        if not pdf_files and not has_corpus:
            return JsonResponse({
                'success': False,
                'error': 'No hay PDFs ni corpus JSON para procesar'
            }, status=400)
        
        # Eliminar base vectorial anterior
        vectordb_dir = "Vector_DB - Documents"
        if os.path.exists(vectordb_dir):
            shutil.rmtree(vectordb_dir)
            print(f"✓ Base vectorial anterior eliminada")
        
        # Crear nueva base vectorial
        vectordb_service = VectorDBService()
        vectordb = vectordb_service.create_vectorstore(pdf_files, json_path)
        
        if vectordb:
            # Limpiar chain en caché
            if 'retrieval_chain' in request.session:
                del request.session['retrieval_chain']
            
            return JsonResponse({
                'success': True,
                'message': f'Base vectorial regenerada correctamente',
                'pdf_count': len(pdf_files),
                'has_corpus': has_corpus,
                'pdf_files': pdf_files
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Error al crear la base vectorial'
            }, status=500)
    
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'trace': traceback.format_exc()
        }, status=500)

