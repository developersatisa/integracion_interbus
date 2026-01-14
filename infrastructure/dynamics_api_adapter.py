"""
Adaptador para la API de Dynamics 365.
Implementa el puerto DynamicsAPIAdapter.
"""
import http.client
import json
import logging
import urllib.parse
from typing import List, Dict, Any
from config.settings import settings

logger = logging.getLogger(__name__)


class DynamicsAPIAdapter:
    """Adaptador para interactuar con la API de Dynamics 365."""
    
    def __init__(self):
        self._base_url = settings.api_base_url
    
    def get_entity_data(
        self,
        entity_name: str,
        access_token: str,
        filter_expression: str = None,
        metadata: str = "minimal"
    ) -> List[Dict[Any, Any]]:
        """
        Obtiene todos los datos de una entidad de Dynamics 365.
        
        Args:
            entity_name: Nombre de la entidad
            access_token: Token de acceso
            filter_expression: Expresión de filtro OData opcional (ej: "anio eq 2024")
            
        Returns:
            Lista de registros de la entidad
        """
        conn = http.client.HTTPSConnection(self._base_url)
        
        accept_header = 'application/json'
        if metadata:
            accept_header = f"application/json;odata.metadata={metadata}"

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': accept_header
        }
        
        # Construir URL con filtro si se proporciona
        url = f"/data/{entity_name}"
        if filter_expression:
            import urllib.parse
            url = f"{url}?$filter={urllib.parse.quote(filter_expression)}"
        
        # Realizar petición GET
        full_url = f"https://{self._base_url}{url}"
        logger.info(f"🌐 API REQUEST [GET]: {full_url}")
        conn.request("GET", url, '', headers)
        
        response = conn.getresponse()
        data = response.read().decode("utf-8")
        
        if response.status != 200:
            raise Exception(f"Error obteniendo datos de {entity_name}: {data}")
        
        # Parsear respuesta JSON
        response_data = json.loads(data)
        
        # OData devuelve los datos en el campo 'value'
        if 'value' in response_data:
            return response_data['value']
        
        return []
    
    def create_entity_data(self, entity_name: str, access_token: str, data: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Crea un nuevo registro en una entidad de Dynamics 365.
        
        Args:
            entity_name: Nombre de la entidad
            access_token: Token de acceso
            data: Datos del nuevo registro
            
        Returns:
            Datos del registro creado
        """
        conn = http.client.HTTPSConnection(self._base_url)
        
        payload = json.dumps(data)
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
        
        # Realizar petición POST
        # Añadir company=itb para asegurar el contexto de la empresa
        url = f"/data/{entity_name}?company=itb"
        conn.request("POST", url, payload, headers)
        
        response = conn.getresponse()
        result_data = response.read().decode("utf-8")
        
        if response.status not in [200, 201]:
            raise Exception(f"Error creando registro en {entity_name}: {result_data}")
        
        return json.loads(result_data)
    
    def update_entity_data(
        self,
        entity_name: str,
        access_token: str,
        item_id: str,
        data: Dict[Any, Any],
        key_field: str = 'EQMHolidaysAbsencesGroupATISAId',
        data_area_id: str = 'itb',
        if_match: str = None
    ) -> Dict[Any, Any]:
        """
        Actualiza un registro existente en una entidad de Dynamics 365.
        
        Args:
            entity_name: Nombre de la entidad
            access_token: Token de acceso
            item_id: ID del registro a actualizar
            data: Datos a actualizar
            
        Returns:
            Datos del registro actualizado
        """
        conn = http.client.HTTPSConnection(self._base_url)
        
        payload = json.dumps(data)
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
        if if_match:
            headers['If-Match'] = if_match
        
        # Dynamics 365 requiere clave compuesta con dataAreaId para la mayoría de entidades
        # Pero para entidades globales (como ContributionAccountCodeCCs) no se usa
        quoted_id = urllib.parse.quote(item_id)
        
        if entity_name == 'ContributionAccountCodeCCs':
            url = f"/data/{entity_name}({key_field}='{quoted_id}')?company={data_area_id}"
        else:
            url = f"/data/{entity_name}(dataAreaId='{data_area_id}',{key_field}='{quoted_id}')?company={data_area_id}"
        
        # Realizar petición PATCH
        full_url = f"https://{self._base_url}{url}"
        logger.info(f"🌐 API REQUEST [PATCH]: {full_url}")
        conn.request("PATCH", url, payload, headers)
        
        response = conn.getresponse()
        result_data = response.read().decode("utf-8")
        
        if response.status not in [200, 204]:
            raise Exception(f"Error actualizando registro en {entity_name}: {result_data}")
        
        # Si la respuesta está vacía (status 204), devolver los datos enviados
        if response.status == 204:
            return data
        
        return json.loads(result_data) if result_data else data

    def update_entity_data_by_url(
        self,
        entity_url: str,
        access_token: str,
        data: Dict[Any, Any],
        if_match: str = None
    ) -> Dict[Any, Any]:
        """
        Actualiza un registro usando la URL completa o el path OData.
        """
        conn = http.client.HTTPSConnection(self._base_url)
        payload = json.dumps(data)

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
        if if_match:
            headers['If-Match'] = if_match

        url = entity_url
        if entity_url.startswith("http"):
            parsed = urllib.parse.urlparse(entity_url)
            url = parsed.path
            if parsed.query:
                url = f"{url}?{parsed.query}"

        full_url = f"https://{self._base_url}{url}"
        logger.info(f"🌐 API REQUEST [PATCH]: {full_url}")
        conn.request("PATCH", url, payload, headers)

        response = conn.getresponse()
        result_data = response.read().decode("utf-8")

        if response.status not in [200, 204]:
            raise Exception(f"Error actualizando registro: {result_data}")

        if response.status == 204:
            return data

        return json.loads(result_data) if result_data else data
    
    def delete_entity_data(self, entity_name: str, access_token: str, item_id: str, key_field: str = 'EQMHolidaysAbsencesGroupATISAId', data_area_id: str = 'itb') -> bool:
        """
        Elimina un registro de una entidad de Dynamics 365.
        
        Args:
            entity_name: Nombre de la entidad
            access_token: Token de acceso
            item_id: ID del registro a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        conn = http.client.HTTPSConnection(self._base_url)
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
        
        # Dynamics 365 requiere clave compuesta con dataAreaId
        # Formato: /data/Entity(dataAreaId='itb',PrimaryKey='value')
        # Para ContributionAccountCodeCCs: usar solo EQMCCC
        if entity_name == 'ContributionAccountCodeCCs':
            if isinstance(item_id, dict):
                # Clave compuesta pasada como diccionario
                eqmccc = urllib.parse.quote(str(item_id.get('EQMCCC', '')))
                worker_place = urllib.parse.quote(str(item_id.get('EQMWorkerPlaceID', '')))
                url = f"/data/{entity_name}(EQMCCC='{eqmccc}',EQMWorkerPlaceID='{worker_place}')?company={data_area_id}"
            elif isinstance(item_id, str) and '_' in item_id:
                # Clave compuesta pasada como string con guion bajo
                parts = item_id.split('_', 1)
                if len(parts) == 2:
                    eqmccc = urllib.parse.quote(parts[0])
                    worker_place = urllib.parse.quote(parts[1])
                    url = f"/data/{entity_name}(EQMCCC='{eqmccc}',EQMWorkerPlaceID='{worker_place}')?company={data_area_id}"
                else:
                    raise Exception(f"Formato de ID incorrecto: {item_id}")
            else:
                # Fallback o error
                quoted_ccc = urllib.parse.quote(str(item_id))
                url = f"/data/{entity_name}(EQMCCC='{quoted_ccc}')?company={data_area_id}"
        else:
            quoted_id = urllib.parse.quote(str(item_id))
            url = f"/data/{entity_name}(dataAreaId='{data_area_id}',{key_field}='{quoted_id}')?company={data_area_id}"
        
        # Realizar petición DELETE
        full_url = f"https://{self._base_url}{url}"
        logger.info(f"🌐 API REQUEST [DELETE]: {full_url}")
        conn.request("DELETE", url, '', headers)
        
        response = conn.getresponse()
        result_data = response.read().decode("utf-8")
        
        if response.status not in [200, 204]:
            raise Exception(f"Error eliminando registro de {entity_name}: {result_data}")
        
        return True

