from django import forms
from .models import ReservaVeiculo
from django.core.exceptions import ValidationError
from datetime import datetime, date

class AgendamentoForm(forms.ModelForm):
    class Meta:
        model = ReservaVeiculo
        fields = ['veiculo', 'destino', 'motivo', 'data_retirada', 'data_devolucao']
        widgets = {
            'veiculo': forms.Select(attrs={'class': 'form-select'}),
            'destino': forms.TextInput(attrs={'class': 'form-control'}),
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'data_retirada': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_devolucao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        data_retirada = cleaned_data.get("data_retirada")
        data_devolucao = cleaned_data.get("data_devolucao")

        hoje = date.today()

        if data_retirada:
            if data_retirada < hoje:
                raise ValidationError("Não é possível reservar com data no passado.")

        if data_retirada and data_devolucao:
            if data_devolucao < data_retirada:
                raise ValidationError("A data de devolução não pode ser anterior à data de retirada.")
                
            veiculo = cleaned_data.get("veiculo")
            if veiculo:
                # Busca reservas que sobreponham o período
                conflitos = ReservaVeiculo.objects.filter(
                    veiculo=veiculo,
                    data_retirada__lte=data_devolucao,
                    data_devolucao__gte=data_retirada
                ).exclude(
                    data_devolucao=data_retirada # Permite que a devolução de um seja no mesmo dia da retirada de outro
                ).exclude(
                    data_retirada=data_devolucao # Permite o inverso
                )
                
                if self.instance and self.instance.pk:
                    conflitos = conflitos.exclude(pk=self.instance.pk)
                    
                if conflitos.exists():
                    raise ValidationError("Este veículo já está reservado durante este período.")
        
        return cleaned_data