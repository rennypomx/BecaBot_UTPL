"""
Comando de Django para limpiar sesiones antiguas del chat.
Elimina mensajes de sesiones inactivas por más de 2 horas.

Uso:
    python manage.py cleanup_old_sessions
    
Para ejecutar automáticamente cada hora, agregar a cron o Windows Task Scheduler:
    python manage.py cleanup_old_sessions >> logs/cleanup.log 2>&1
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from myapp.models import ChatMessage


class Command(BaseCommand):
    help = 'Limpia sesiones de chat antiguas (inactivas por más de 2 horas)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=2,
            help='Número de horas de inactividad antes de limpiar (default: 2)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se eliminaría sin hacerlo realmente'
        )

    def handle(self, *args, **options):
        hours = options['hours']
        dry_run = options['dry_run']
        
        # Calcular fecha límite
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        self.stdout.write(f"\n{'='*70}")
        self.stdout.write(self.style.WARNING(
            f"Limpieza de sesiones inactivas por más de {hours} horas"
        ))
        self.stdout.write(f"Fecha límite: {cutoff_time}")
        self.stdout.write(f"{'='*70}\n")
        
        # Obtener sesiones con último mensaje antes del cutoff
        # Agrupar por session_key y obtener el último mensaje de cada sesión
        from django.db.models import Max
        
        sessions_with_last_message = ChatMessage.objects.values('session_key').annotate(
            last_message_time=Max('created_at')
        ).filter(
            last_message_time__lt=cutoff_time
        )
        
        total_sessions = sessions_with_last_message.count()
        
        if total_sessions == 0:
            self.stdout.write(self.style.SUCCESS(
                "✓ No hay sesiones antiguas para limpiar"
            ))
            return
        
        # Contar mensajes a eliminar
        session_keys = [s['session_key'] for s in sessions_with_last_message]
        total_messages = ChatMessage.objects.filter(session_key__in=session_keys).count()
        
        self.stdout.write(f"Sesiones a limpiar: {total_sessions}")
        self.stdout.write(f"Mensajes a eliminar: {total_messages}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING(
                "\n[DRY RUN] No se eliminará nada. Sesiones que serían limpiadas:"
            ))
            for session in sessions_with_last_message[:10]:  # Mostrar primeras 10
                self.stdout.write(
                    f"  - {session['session_key'][:12]}... "
                    f"(último mensaje: {session['last_message_time']})"
                )
            if total_sessions > 10:
                self.stdout.write(f"  ... y {total_sessions - 10} sesiones más")
        else:
            # Eliminar mensajes
            deleted_count, _ = ChatMessage.objects.filter(
                session_key__in=session_keys
            ).delete()
            
            self.stdout.write(self.style.SUCCESS(
                f"\n✓ Limpieza completada:"
            ))
            self.stdout.write(f"  - {total_sessions} sesiones eliminadas")
            self.stdout.write(f"  - {deleted_count} mensajes eliminados")
            
            # Calcular espacio liberado (aproximado)
            avg_message_size = 200  # bytes aproximados por mensaje
            space_freed = (deleted_count * avg_message_size) / 1024  # KB
            if space_freed > 1024:
                self.stdout.write(f"  - ~{space_freed/1024:.2f} MB liberados")
            else:
                self.stdout.write(f"  - ~{space_freed:.2f} KB liberados")
        
        self.stdout.write(f"\n{'='*70}\n")
