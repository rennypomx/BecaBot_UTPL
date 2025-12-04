from django.urls import path
from . import views

urlpatterns = [
    # URLs del chatbot principal
    path('', views.home, name='home'),
    path('send-message/', views.send_message, name='send_message'),
    path('get-chat-history/', views.get_chat_history, name='get_chat_history'),
    path('upload-documents/', views.upload_documents, name='upload_documents'),
    path('update-becas/', views.update_becas, name='update_becas'),
    path('clear-chat/', views.clear_chat, name='clear_chat'),
    path('test-bot/', views.test_bot, name='test_bot'),
    path('regenerate-vectordb/', views.regenerate_vectordb, name='regenerate_vectordb'),
    
    # URLs del Panel de Administración
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    
    # Corpus
    path('admin-panel/corpus/', views.admin_corpus, name='admin_corpus'),
    path('admin-panel/corpus/upload/', views.admin_corpus_upload, name='admin_corpus_upload'),
    path('admin-panel/corpus/<int:pk>/view/', views.admin_corpus_view, name='admin_corpus_view'),
    path('admin-panel/corpus/<int:pk>/edit/', views.admin_corpus_edit, name='admin_corpus_edit'),
    path('admin-panel/corpus/<int:pk>/toggle/', views.admin_corpus_toggle, name='admin_corpus_toggle'),
    path('admin-panel/corpus/<int:pk>/delete/', views.admin_corpus_delete, name='admin_corpus_delete'),
    
    # PDF
    path('admin-panel/pdf/', views.admin_pdf, name='admin_pdf'),
    path('admin-panel/pdf/upload/', views.admin_pdf_upload, name='admin_pdf_upload'),
    path('admin-panel/pdf/<int:pk>/view/', views.admin_pdf_view, name='admin_pdf_view'),
    path('admin-panel/pdf/<int:pk>/edit/', views.admin_pdf_edit, name='admin_pdf_edit'),
    path('admin-panel/pdf/<int:pk>/delete/', views.admin_pdf_delete, name='admin_pdf_delete'),
    
    # Otros
    path('admin-panel/messages/', views.admin_messages, name='admin_messages'),
    path('admin-panel/messages/clear/', views.admin_messages_clear, name='admin_messages_clear'),
    path('admin-panel/scraping/', views.admin_scraping, name='admin_scraping'),
    path('admin-panel/scraping/run/', views.admin_run_scraping, name='admin_run_scraping'),
]