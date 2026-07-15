import calendar
from datetime import date, timedelta
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
# Importações relacionadas a formulários e usuários
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User # <--- IMPORTAÇÃO ADICIONADA AQUI
from django.contrib import messages
from django.db.models import Q
from .models import ReservaVeiculo
from .forms import AgendamentoForm
import locale

# Define o locale para o Brasil para traduzir nomes
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

@login_required
def dashboard(request, ano=None, mes=None):
    hoje = date.today()
    
    if ano is None or mes is None:
        ano, mes = hoje.year, hoje.month
    
    data_atual = date(ano, mes, 1)
    mes_anterior_data = data_atual - timedelta(days=1)
    proximo_mes_data = (data_atual.replace(day=28) + timedelta(days=4)).replace(day=1)

    contexto_navegacao = {
        'mes_anterior': {'ano': mes_anterior_data.year, 'mes': mes_anterior_data.month},
        'proximo_mes': {'ano': proximo_mes_data.year, 'mes': proximo_mes_data.month},
        'mes_ano_display': data_atual.strftime('%B de %Y').capitalize(),
    }

    cal = calendar.Calendar(firstweekday=6)
    calendario_matriz = cal.monthdayscalendar(ano, mes)

    reunioes_do_mes = ReservaVeiculo.objects.filter(
        Q(data_retirada__year=ano, data_retirada__month=mes) |
        Q(data_devolucao__year=ano, data_devolucao__month=mes)
    )
    dias_retirada = {r.data_retirada.day for r in reunioes_do_mes if r.data_retirada.month == mes}
    dias_devolucao = {r.data_devolucao.day for r in reunioes_do_mes if r.data_devolucao.month == mes}

    reunioes_de_hoje = reunioes_do_mes.filter(
        Q(data_retirada=hoje) | Q(data_devolucao=hoje)
    ).distinct() if (ano == hoje.year and mes == hoje.month) else []

    context = {
        'calendario': calendario_matriz,
        'dias_retirada': dias_retirada,
        'dias_devolucao': dias_devolucao,
        'hoje': hoje,
        'ano_atual': ano,
        'mes_atual': mes,
        'reunioes_do_dia': reunioes_de_hoje,
        'navegacao': contexto_navegacao,
        'dias_semana': [d.capitalize() for d in calendar.day_abbr[6:]] + [d.capitalize() for d in calendar.day_abbr[:6]]
    }
    return render(request, 'APP/dashboard.html', context)


@login_required
def detalhe_reuniao(request, pk):
    reuniao = get_object_or_404(ReservaVeiculo, pk=pk)
    pode_apagar = date.today() <= reuniao.data_retirada
    context = {
        'reuniao': reuniao,
        'pode_apagar': pode_apagar
    }
    return render(request, 'APP/detalhe_reuniao.html', context)

@login_required
def novo_agendamento(request):
    if request.method == 'POST':
        form = AgendamentoForm(request.POST)
        if form.is_valid():
            agendamento = form.save(commit=False)
            agendamento.solicitante = request.user
            
            # Alerta caso haja devolução do mesmo veículo no dia da retirada
            conflito_devolucao = ReservaVeiculo.objects.filter(
                veiculo=agendamento.veiculo,
                data_devolucao=agendamento.data_retirada
            ).first()
            if conflito_devolucao:
                nome_alerta = conflito_devolucao.solicitante.get_full_name() or conflito_devolucao.solicitante.username
                messages.add_message(request, messages.SUCCESS, f"Reserva efetuada com sucesso!\n\nAlinhe a retirada com o(a) {nome_alerta}, para não haver atrasos.", extra_tags='popup')
            else:
                messages.success(request, 'Reserva agendada com sucesso!')

            agendamento.save()
            return redirect('dashboard')
        else:
            messages.error(request, 'Ocorreu um erro. Por favor, verifique os dados informados.')
    else:
        form = AgendamentoForm()
    
    context = {
        'form': form
    }
    return render(request, 'APP/agendamento_form.html', context)

def pode_cadastrar_usuarios(user):
    """
    Verifica se o usuário é um superusuário OU pertence ao grupo 'Gerenciador de Usuários'.
    """
    is_manager = user.groups.filter(name='Gerenciador de Usuários').exists()
    return user.is_superuser or is_manager

@login_required # Adicionamos login_required para garantir que o usuário esteja logado
@user_passes_test(pode_cadastrar_usuarios)
def cadastrar_usuario(request):
    if request.method == 'POST':
        nome_completo = request.POST.get('nome_completo')
        username = request.POST.get('username')
        
        if not username or not nome_completo:
            messages.error(request, 'O nome completo e o nome de usuário são obrigatórios.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, f'O usuário "{username}" já existe.')
        else:
            nome_parts = nome_completo.split(' ', 1)
            first_name = nome_parts[0]
            last_name = nome_parts[1] if len(nome_parts) > 1 else ''
            
            User.objects.create_user(username=username, password='mudarsenha', first_name=first_name, last_name=last_name)
            messages.success(request, f'Usuário {username} criado com sucesso! A senha inicial é "mudarsenha".')
            return redirect('dashboard')
            
    return render(request, 'APP/cadastrar_usuario.html')

@login_required
def alterar_senha(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            
            user.perfil.deve_alterar_senha = False
            user.perfil.save()

            messages.success(request, 'Sua senha foi alterada com sucesso!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = PasswordChangeForm(request.user)

    if request.user.perfil.deve_alterar_senha:
        messages.warning(request, 'Por segurança, você deve alterar sua senha inicial antes de continuar.')
        
    return render(request, 'APP/alterar_senha.html', {'form': form})
    
@login_required
def editar_agendamento(request, pk):
    reuniao = get_object_or_404(ReservaVeiculo, pk=pk)

    if request.user != reuniao.solicitante:
        messages.error(request, 'Você não tem permissão para editar este agendamento.')
        return redirect('detalhe_reuniao', pk=reuniao.pk)

    if request.method == 'POST':
        form = AgendamentoForm(request.POST, instance=reuniao)
        if form.is_valid():
            agendamento = form.save(commit=False)

            conflito_devolucao = ReservaVeiculo.objects.filter(
                veiculo=agendamento.veiculo,
                data_devolucao=agendamento.data_retirada
            ).exclude(pk=agendamento.pk).first()
            if conflito_devolucao:
                nome_alerta = conflito_devolucao.solicitante.get_full_name() or conflito_devolucao.solicitante.username
                messages.add_message(request, messages.SUCCESS, f"Reserva atualizada com sucesso!\n\nAlinhe a retirada com o(a) {nome_alerta}, para não haver atrasos.", extra_tags='popup')
            else:
                messages.success(request, 'Reserva atualizada com sucesso!')

            agendamento.save()
            return redirect('detalhe_reuniao', pk=reuniao.pk)
        else:
            messages.error(request, 'Ocorreu um erro. Por favor, verifique os dados informados.')
    else:
        form = AgendamentoForm(instance=reuniao)
    
    context = {
        'form': form,
        'edit_mode': True
    }
    return render(request, 'APP/agendamento_form.html', context)


@login_required
def apagar_agendamento(request, pk):
    reuniao = get_object_or_404(ReservaVeiculo, pk=pk)

    if request.user != reuniao.solicitante:
        messages.error(request, 'Você não tem permissão para apagar este agendamento.')
        return redirect('detalhe_reuniao', pk=reuniao.pk)

    if date.today() > reuniao.data_retirada:
        messages.error(request, 'Não é possível apagar uma reserva após a data de retirada ter passado.')
        return redirect('detalhe_reuniao', pk=reuniao.pk)

    if request.method == 'POST':
        reuniao.delete()
        messages.success(request, 'A reserva foi apagada com sucesso.')
        return redirect('dashboard')

    context = {
        'reuniao': reuniao
    }
    return render(request, 'APP/apagar_confirmacao.html', context)

@login_required
def reunioes_por_dia_api(request, ano, mes, dia):
    try:
        data_selecionada = date(ano, mes, dia)
        reunioes = ReservaVeiculo.objects.filter(
            Q(data_retirada=data_selecionada) | Q(data_devolucao=data_selecionada)
        ).distinct()
        
        reunioes_json = [
            {
                'id': reuniao.id,
                'titulo': f"{reuniao.veiculo.placa} - {reuniao.veiculo.modelo} ({reuniao.destino})",
                'data_retirada': reuniao.data_retirada.strftime('%d/%m/%Y'),
                'data_devolucao': reuniao.data_devolucao.strftime('%d/%m/%Y'),
                'organizador': reuniao.solicitante.get_full_name() or reuniao.solicitante.username,
                'url_detalhes': f'/reuniao/{reuniao.id}/'
            } for reuniao in reunioes
        ]
        
        return JsonResponse({'reunioes': reunioes_json})
    except ValueError:
        return JsonResponse({'error': 'Data inválida'}, status=400)