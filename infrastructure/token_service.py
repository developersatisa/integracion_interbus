"""
Servicio para obtener tokens de Azure AD.
Implementa el puerto TokenRepository.
"""
import http.client
import urllib.parse
from typing import Dict, Any
from config.settings import settings


class AzureADTokenService:
    """Implementa la obtención de tokens de Azure AD."""
    
    def __init__(self):
        self._tenant_id = settings.azure_ad_tenant_id
        self._client_id = settings.azure_ad_client_id
        self._client_secret = settings.azure_ad_client_secret
        self._resource = settings.azure_ad_resource
    
    def get_access_token(self) -> str:
        """
        Obtiene un token de acceso de Azure AD usando el flujo client credentials.
        
        Returns:
            str: Token de acceso
            
        Raises:
            Exception: Si falla la autenticación
        """
        # Preparar el payload
        payload_data = {
            'grant_type': 'client_credentials',
            'client_id': self._client_id,
            'client_secret': self._client_secret,
            'resource': self._resource
        }
        payload = urllib.parse.urlencode(payload_data)
        
        # Headers
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Realizar petición
        conn = http.client.HTTPSConnection("login.microsoftonline.com")
        conn.request(
            "POST",
            f"/{self._tenant_id}/oauth2/token",
            payload,
            headers
        )
        
        response = conn.getresponse()
        data = response.read().decode("utf-8")
        
        if response.status != 200:
            raise Exception(f"Error obteniendo token: {data}")
        
        # Parsear respuesta JSON
        import json
        token_data = json.loads(data)
        
        if 'access_token' not in token_data:
            raise Exception(f"Token no encontrado en respuesta: {data}")
        
        return token_data['access_token']


