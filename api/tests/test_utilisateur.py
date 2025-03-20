import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from api.models import Utilisateur, OTP
from django.utils import timezone

@pytest.fixture
def client():
    """Fixture pour créer un client API de test."""
    return APIClient()

@pytest.fixture
def user(db):
    """Fixture pour créer un utilisateur de test dans la base de données."""
    return Utilisateur.objects.create_user(username='testuser', email='test@example.com', password='test123')

@pytest.mark.django_db
def test_register_user(client):
    """Teste l’inscription d’un nouvel utilisateur via l’endpoint /register/."""
    url = reverse('register')  # Nécessite que 'register' soit nommé dans urls.py
    data = {
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'newpass123'
    }
    response = client.post(url, data, format='json')
    assert response.status_code == 201
    assert response.data['status'] == 'Utilisateur créé, OTP envoyé par email'
    assert Utilisateur.objects.filter(username='newuser').exists()
    assert OTP.objects.filter(utilisateur__username='newuser').exists()

@pytest.mark.django_db
def test_verify_otp(client, user):
    """Teste la vérification d’un OTP pour activer un compte utilisateur."""
    otp = OTP.objects.create(
        utilisateur=user,
        code='123456',
        expiration=timezone.now() + timezone.timedelta(minutes=10)
    )
    url = reverse('verify-otp')  # Nécessite que 'verify-otp' soit nommé dans urls.py
    data = {'user_id': user.id, 'code': '123456'}
    response = client.post(url, data, format='json')
    assert response.status_code == 200
    assert response.data['status'] == 'Compte activé'
    user.refresh_from_db()
    assert user.is_active is True
    otp.refresh_from_db()
    assert otp.is_used is True

@pytest.mark.django_db
def test_me_authenticated(client, user):
    """Teste la récupération des informations de l’utilisateur connecté via /me/."""
    client.force_authenticate(user=user)
    url = reverse('utilisateur-me')  # Nécessite que 'utilisateur-me' soit nommé dans urls.py
    response = client.get(url)
    assert response.status_code == 200
    assert response.data['username'] == 'testuser'