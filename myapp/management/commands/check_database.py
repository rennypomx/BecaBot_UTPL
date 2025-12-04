"""
Comando para verificar datos en la base de datos.
Uso: python manage.py check_database
"""

from django.core.management.base import BaseCommand
from myapp.models import JSONCorpus, PDFDocument


class Command(BaseCommand):
    help = 'Verifica los datos en la base de datos'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== CORPUS JSON ==='))
        
        corpus_list = JSONCorpus.objects.all()
        if corpus_list:
            for c in corpus_list:
                status = "✓ Activo" if c.is_active else "✗ Inactivo"
                self.stdout.write(f'  {status} {c.name}')
                self.stdout.write(f'     Tipo: {c.get_corpus_type_display()}')
                self.stdout.write(f'     Registros: {c.records_count}')
                self.stdout.write(f'     Tamaño: {c.get_file_size_mb()} MB')
                self.stdout.write(f'     Archivo: {c.file.name if c.file else "Sin archivo"}\n')
        else:
            self.stdout.write(self.style.WARNING('  No hay corpus en la base de datos\n'))
        
        self.stdout.write(self.style.SUCCESS('=== DOCUMENTOS PDF ==='))
        
        pdf_list = PDFDocument.objects.all()
        if pdf_list:
            for p in pdf_list:
                has_file = "✓" if p.file else "✗"
                self.stdout.write(f'  {has_file} {p.title}')
                self.stdout.write(f'     Tipo: {p.get_document_type_display()}')
                self.stdout.write(f'     Estado: {p.get_status_display()}')
                if p.file:
                    self.stdout.write(f'     Tamaño: {p.get_file_size_mb()} MB')
                    self.stdout.write(f'     Archivo: {p.file.name}')
                else:
                    self.stdout.write(self.style.WARNING('     Sin archivo adjunto'))
                self.stdout.write('')
        else:
            self.stdout.write(self.style.WARNING('  No hay documentos PDF en la base de datos\n'))
        
        self.stdout.write(self.style.SUCCESS(f'\n=== RESUMEN ==='))
        self.stdout.write(f'Total Corpus JSON: {corpus_list.count()}')
        self.stdout.write(f'Total Documentos PDF: {pdf_list.count()}')
        self.stdout.write(f'PDFs con archivo: {pdf_list.filter(file__isnull=False).exclude(file="").count()}')
        self.stdout.write(f'PDFs sin archivo: {pdf_list.filter(file="").count() + pdf_list.filter(file__isnull=True).count()}')
