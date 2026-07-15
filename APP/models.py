from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    deve_alterar_senha = models.BooleanField(default=True)

    def __str__(self):
        return self.usuario.username

# SINAL PARA CRIAR/ATUALIZAR O PERFIL AUTOMATICAMENTE
# Quando um User é criado, um Perfil é criado junto.
@receiver(post_save, sender=User)
def criar_ou_atualizar_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(usuario=instance)
    instance.perfil.save()

class Veiculo(models.Model):
    placa = models.CharField(max_length=10, unique=True)
    modelo = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.placa} - {self.modelo}"

class ReservaVeiculo(models.Model):
    veiculo = models.ForeignKey(Veiculo, on_delete=models.CASCADE)
    destino = models.CharField(max_length=200)
    motivo = models.TextField(help_text="Motivo da reserva")
    data_retirada = models.DateField()
    data_devolucao = models.DateField()
    solicitante = models.ForeignKey(User, on_delete=models.CASCADE)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['data_retirada']

    def __str__(self):
        return f"{self.veiculo} - {self.destino} ({self.data_retirada.strftime('%d/%m/%Y')})"