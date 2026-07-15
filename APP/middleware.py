from django.shortcuts import redirect
from django.urls import reverse

class ForcarAlteracaoSenhaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Continua se o usuário não estiver logado
        if not request.user.is_authenticated:
            return self.get_response(request)

        # URLs permitidas enquanto a senha não for alterada
        urls_permitidas = [
            reverse('alterar_senha'),
            reverse('logout')
        ]

        # Redireciona se o usuário precisar alterar a senha e não estiver em uma URL permitida
        if request.user.perfil.deve_alterar_senha and request.path not in urls_permitidas:
            return redirect('alterar_senha')

        return self.get_response(request)