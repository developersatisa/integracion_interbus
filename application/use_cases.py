"""
Casos de uso que orquestan la lógica de negocio.
Sigue el principio de responsabilidad única (SRP) de SOLID.
"""
from typing import List, Dict, Any
from domain.ports import TokenRepository, DynamicsAPIAdapter, DatabaseAdapter


class SyncDynamicsEntityUseCase:
    """Caso de uso para sincronizar una entidad de Dynamics 365 con la base de datos."""
    
    def __init__(
        self,
        token_repository: TokenRepository,
        dynamics_api: DynamicsAPIAdapter,
        database_adapter: DatabaseAdapter
    ):
        self._token_repository = token_repository
        self._dynamics_api = dynamics_api
        self._database_adapter = database_adapter
    
    def execute(self, entity_name: str) -> Dict[str, Any]:
        """
        Sincroniza una entidad de Dynamics 365 con la base de datos.
        
        Args:
            entity_name: Nombre de la entidad a sincronizar
            
        Returns:
            Diccionario con el resultado de la sincronización
        """
        try:
            # Obtener token
            access_token = self._token_repository.get_access_token()
            
            # Obtener datos de la entidad
            entity_data = self._dynamics_api.get_entity_data(entity_name, access_token)
            
            # Limpiar datos antiguos
            self._database_adapter.clear_entity_data(entity_name)
            
            # Guardar datos nuevos
            records_saved = self._database_adapter.save_entity_data(entity_name, entity_data)
            
            return {
                "success": True,
                "entity": entity_name,
                "records_synced": records_saved,
                "records_count": len(entity_data)
            }
        except Exception as e:
            return {
                "success": False,
                "entity": entity_name,
                "error": str(e)
            }


class SyncAllEntitiesUseCase:
    """Caso de uso para sincronizar todas las entidades."""
    
    def __init__(self, token_repository: TokenRepository, 
                 dynamics_api: DynamicsAPIAdapter, 
                 database_adapter: DatabaseAdapter):
        self._token_repository = token_repository
        self._dynamics_api = dynamics_api
        self._database_adapter = database_adapter
    
    def execute(self, entity_names: List[str]) -> List[Dict[str, Any]]:
        """
        Sincroniza todas las entidades especificadas.
        
        Args:
            entity_names: Lista de nombres de entidades
            
        Returns:
            Lista de resultados de sincronización
        """
        results = []
        for entity_name in entity_names:
            use_case = SyncDynamicsEntityUseCase(
                self._token_repository,
                self._dynamics_api,
                self._database_adapter
            )
            result = use_case.execute(entity_name)
            results.append(result)
        return results


