from django.urls import path
from . import views

urlpatterns = [
    # A URL do dashboard agora pode receber ano e mês
    path('', views.dashboard, name='dashboard'),
    path('<int:ano>/<int:mes>/', views.dashboard, name='dashboard_mes'),
    path('alterar-senha/', views.alterar_senha, name='alterar_senha'),
    path('agendar/', views.novo_agendamento, name='novo_agendamento'),
    path('reuniao/<int:pk>/', views.detalhe_reuniao, name='detalhe_reuniao'),
    path('usuarios/cadastrar/', views.cadastrar_usuario, name='cadastrar_usuario'),
    path('reuniao/<int:pk>/editar/', views.editar_agendamento, name='editar_agendamento'),
    path('reuniao/<int:pk>/apagar/', views.apagar_agendamento, name='apagar_agendamento'),
    path('api/reunioes/<int:ano>/<int:mes>/<int:dia>/', views.reunioes_por_dia_api, name='reunioes_por_dia_api'),
]