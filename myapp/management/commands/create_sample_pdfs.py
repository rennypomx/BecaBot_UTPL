"""
Comando para crear documentos PDF de ejemplo.
Uso: python manage.py create_sample_pdfs

Nota: Este comando crea registros en la base de datos para PDFs de ejemplo.
Los archivos PDF reales deben agregarse manualmente desde el admin de Django.
"""

from django.core.management.base import BaseCommand
from myapp.models import PDFDocument, JSONCorpus


class Command(BaseCommand):
    help = 'Crea registros de documentos PDF de ejemplo para el sistema'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Creando registros de PDFs de ejemplo ===\n'))
        
        # Obtener el corpus relacionado
        related_corpus = JSONCorpus.objects.filter(name='corpus_becas_utpl').first()
        
        # Crear registros de ejemplo (sin archivos)
        self.create_sample_records(related_corpus)
        
        self.stdout.write(self.style.SUCCESS('\n=== Registros creados ==='))
        self.stdout.write(self.style.NOTICE('\nℹ Para agregar archivos PDF reales:'))
        self.stdout.write('  1. Accede al admin de Django: http://localhost:8000/admin/')
        self.stdout.write('  2. Ve a "Documentos PDF"')
        self.stdout.write('  3. Edita cada registro y sube el archivo PDF correspondiente')

    def create_sample_records(self, related_corpus):
        """Crea registros de ejemplo de documentos PDF."""
        
        samples = [
            {
                'title': 'Guía de Becas UTPL 2024',
                'document_type': 'guide',
                'description': 'Guía completa sobre las becas disponibles en la UTPL, requisitos y proceso de solicitud',
                'version': '1.0',
                'tags': 'becas,utpl,guía,estudiantes,2024',
                'status': 'draft',
            },
            {
                'title': 'Reglamento de Becas UTPL',
                'document_type': 'regulations',
                'description': 'Reglamento oficial que regula el sistema de becas de la UTPL',
                'version': '2024',
                'tags': 'becas,reglamento,normativa,utpl',
                'status': 'draft',
            },
            {
                'title': 'Preguntas Frecuentes - Becas UTPL',
                'document_type': 'guide',
                'description': 'Respuestas a las preguntas más comunes sobre el sistema de becas UTPL',
                'version': '1.0',
                'tags': 'becas,faq,preguntas,respuestas,ayuda',
                'status': 'draft',
            },
            {
                'title': 'Formulario de Solicitud de Beca',
                'document_type': 'form',
                'description': 'Formulario oficial para solicitar becas en la UTPL',
                'version': '2024-1',
                'tags': 'becas,formulario,solicitud',
                'status': 'draft',
            },
        ]
        
        created_count = 0
        for sample in samples:
            # Verificar si ya existe
            if PDFDocument.objects.filter(title=sample['title']).exists():
                self.stdout.write(self.style.WARNING(f"  ⚠ Ya existe: {sample['title']}"))
                continue
            
            # Crear registro
            document = PDFDocument(
                title=sample['title'],
                document_type=sample['document_type'],
                description=sample['description'],
                version=sample['version'],
                tags=sample['tags'],
                status=sample['status'],
                is_public=False,
                related_corpus=related_corpus,
                created_by='Sistema'
            )
            document.save()
            
            self.stdout.write(self.style.SUCCESS(f"  ✓ Creado: {sample['title']}"))
            created_count += 1
        
        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(f'\n  Total registros creados: {created_count}'))
        else:
            self.stdout.write(self.style.WARNING('\n  No se crearon nuevos registros (ya existen)'))
