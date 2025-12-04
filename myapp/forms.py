"""
Formularios de Django para BecaBot UTPL.
"""

from django import forms


class ChatForm(forms.Form):
    """
    Formulario para enviar mensajes al chatbot.
    """
    message = forms.CharField(
        required=True,
        max_length=2000,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Escribe tu pregunta aquí...',
            'rows': 3,
            'id': 'chat-input'
        }),
        label='Mensaje'
    )


class DocumentUploadForm(forms.Form):
    """
    Formulario para subir documentos PDF.
    Nota: El manejo de múltiples archivos se hace en la vista con request.FILES.getlist()
    """
    pdf_files = forms.FileField(
        required=False,
        label='Subir PDFs',
        help_text='Puedes seleccionar múltiples archivos PDF'
    )
    
    def clean_pdf_files(self):
        """
        Valida que los archivos sean PDFs válidos.
        Nota: Esta validación se aplica a cada archivo en la vista.
        """
        return self.cleaned_data.get('pdf_files')
