from django.contrib import admin
from .models import ReservaVeiculo, Perfil, Veiculo

@admin.register(Veiculo)
class VeiculoAdmin(admin.ModelAdmin):
    list_display = ('placa', 'modelo')

@admin.register(ReservaVeiculo)
class ReservaVeiculoAdmin(admin.ModelAdmin):
    list_display = ('veiculo', 'destino', 'data_retirada', 'solicitante')
    list_filter = ('data_retirada', 'solicitante')

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'deve_alterar_senha')