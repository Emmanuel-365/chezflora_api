from django.conf import settings
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from django.http import JsonResponse
from rest_framework import status

def custom_exception_handler(exc, context):
    """
    Personnalise la gestion des exceptions pour retourner des réponses JSON cohérentes.
    """
    # Appelle le gestionnaire par défaut de DRF
    response = exception_handler(exc, context)

    # Si DRF n’a pas géré l’exception (ex. erreur 500 interne)
    if response is None:
        return JsonResponse({
            'error': 'Erreur interne du serveur',
            'detail': str(exc) if settings.DEBUG else 'Une erreur inattendue est survenue',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Personnalise les exceptions DRF
    if isinstance(exc, APIException):
        # Pour toutes les exceptions DRF (ex. ValidationError, PermissionDenied)
        response_data = {
            'error': exc.__class__.__name__,
            'detail': response.data.get('detail', str(exc)),
        }
        # Si c’est une ValidationError avec des champs spécifiques
        if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
            response_data['fields'] = exc.detail
        
        response.data = response_data

    return response


# api/exceptions.py
class BannedUserException(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Ce compte est banni et ne peut pas être utilisé."
    default_code = 'banned_user'