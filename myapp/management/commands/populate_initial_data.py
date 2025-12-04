"""
Comando de Django para poblar la base de datos con datos iniciales.
Uso: python manage.py populate_initial_data
"""

from django.core.management.base import BaseCommand
from django.core.files import File
from myapp.models import JSONCorpus, PDFDocument
import os
import json
from pathlib import Path


class Command(BaseCommand):
    help = 'Pobla la base de datos con archivos JSON y PDF iniciales'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la recarga de datos existentes',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        self.stdout.write(self.style.SUCCESS('=== Iniciando población de datos ===\n'))
        
        # Cargar corpus JSON
        self.load_json_corpus(force)
        
        # Cargar documentos PDF
        self.load_pdf_documents(force)
        
        self.stdout.write(self.style.SUCCESS('\n=== Población completada ==='))

    def load_json_corpus(self, force=False):
        """Carga el archivo corpus_utpl.json en la base de datos."""
        self.stdout.write('Cargando corpus JSON...')
        
        # Ruta al archivo JSON
        json_path = Path('knowledge_base/corpus_utpl.json')
        
        if not json_path.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠ Archivo no encontrado: {json_path}'))
            return
        
        # Verificar si ya existe
        corpus_name = 'corpus_becas_utpl'
        existing = JSONCorpus.objects.filter(name=corpus_name).first()
        
        if existing and not force:
            self.stdout.write(self.style.WARNING(f'  ⚠ Ya existe corpus "{corpus_name}". Use --force para recargar.'))
            return
        
        # Leer el archivo para contar registros
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                records_count = len(data) if isinstance(data, list) else len(data.get('data', []))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Error al leer JSON: {e}'))
            return
        
        # Eliminar si existe y force=True
        if existing and force:
            self.stdout.write(f'  → Eliminando corpus existente...')
            existing.delete()
        
        # Crear nuevo corpus
        try:
            with open(json_path, 'rb') as f:
                corpus = JSONCorpus(
                    name=corpus_name,
                    corpus_type='becas',
                    description='Corpus de datos de becas UTPL extraído mediante web scraping',
                    version='1.0',
                    is_active=True,
                    records_count=records_count,
                    created_by='Sistema'
                )
                corpus.file.save('corpus_utpl.json', File(f), save=True)
            
            self.stdout.write(self.style.SUCCESS(
                f'  ✓ Corpus cargado: {corpus.name} ({records_count} registros, {corpus.get_file_size_mb()} MB)'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Error al guardar corpus: {e}'))

    def load_pdf_documents(self, force=False):
        """Carga documentos PDF de ejemplo en la base de datos."""
        self.stdout.write('\nCargando documentos PDF...')
        
        # Directorio de documentos
        docs_dir = Path('docs')
        
        if not docs_dir.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠ Directorio no encontrado: {docs_dir}'))
            return
        
        # Buscar archivos PDF
        pdf_files = list(docs_dir.glob('*.pdf'))
        
        if not pdf_files:
            self.stdout.write(self.style.WARNING('  ⚠ No se encontraron archivos PDF en /docs'))
            self.stdout.write(self.style.NOTICE('  ℹ Puedes agregar PDFs manualmente desde el admin de Django'))
            return
        
        # Obtener el corpus relacionado (opcional)
        related_corpus = JSONCorpus.objects.filter(name='corpus_becas_utpl').first()
        
        loaded_count = 0
        for pdf_path in pdf_files:
            # Verificar si ya existe
            doc_title = pdf_path.stem.replace('_', ' ').title()
            existing = PDFDocument.objects.filter(title=doc_title).first()
            
            if existing and not force:
                self.stdout.write(self.style.WARNING(f'  ⚠ Ya existe: {doc_title}'))
                continue
            
            # Eliminar si existe y force=True
            if existing and force:
                existing.delete()
            
            # Crear documento
            try:
                with open(pdf_path, 'rb') as f:
                    document = PDFDocument(
                        title=doc_title,
                        document_type='guide',
                        description=f'Documento importado automáticamente desde {pdf_path.name}',
                        status='published',
                        is_public=True,
                        related_corpus=related_corpus,
                        created_by='Sistema'
                    )
                    document.file.save(pdf_path.name, File(f), save=True)
                
                self.stdout.write(self.style.SUCCESS(
                    f'  ✓ PDF cargado: {document.title} ({document.get_file_size_mb()} MB)'
                ))
                loaded_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error al cargar {pdf_path.name}: {e}'))
        
        if loaded_count == 0 and not pdf_files:
            self.stdout.write(self.style.NOTICE('  ℹ No hay archivos PDF para cargar'))
        elif loaded_count > 0:
            self.stdout.write(self.style.SUCCESS(f'  ✓ Total PDFs cargados: {loaded_count}'))
