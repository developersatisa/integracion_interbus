"""
Puertos (interfaces) que definen los contratos que deben cumplir los adaptadores.
Sigue el principio de inversión de dependencias (DIP) de SOLID.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from domain.entities import DynamicsEntity


class TokenRepository(ABC):
    """Puerto para obtener tokens de autenticación."""
    
    @abstractmethod
    def get_access_token(self) -> str:
        """
        Obtiene un token de acceso de Azure AD.
        
        Returns:
            str: Token de acceso
        """
        pass


class DynamicsAPIAdapter(ABC):
    """Puerto para interactuar con la API de Dynamics 365."""
    
    @abstractmethod
    def get_entity_data(self, entity_name: str, access_token: str) -> List[Dict[Any, Any]]:
        """
        Obtiene datos de una entidad de Dynamics 365.
        
        Args:
            entity_name: Nombre de la entidad
            access_token: Token de acceso
            
        Returns:
            Lista de registros de la entidad
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def update_entity_data(
        self, 
        entity_name: str, 
        access_token: str, 
        item_id: str, 
        data: Dict[Any, Any]
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
        pass
    
    @abstractmethod
    def delete_entity_data(self, entity_name: str, access_token: str, item_id: str) -> bool:
        """
        Elimina un registro de una entidad de Dynamics 365.
        
        Args:
            entity_name: Nombre de la entidad
            access_token: Token de acceso
            item_id: ID del registro a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        pass


class DatabaseAdapter(ABC):
    """Puerto para interactuar con la base de datos."""
    
    @abstractmethod
    def save_entity_data(self, entity_name: str, data: List[Dict[Any, Any]]) -> int:
        """
        Guarda datos de una entidad en la base de datos.
        
        Args:
            entity_name: Nombre de la entidad
            data: Datos a guardar
            
        Returns:
            Número de registros guardados
        """
        pass
    
    @abstractmethod
    def clear_entity_data(self, entity_name: str) -> bool:
        """
        Limpia los datos de una entidad de la base de datos.
        
        Args:
            entity_name: Nombre de la entidad
            
        Returns:
            True si se limpió correctamente
        """
        pass
    
    @abstractmethod
    def initialize_database(self) -> bool:
        """
        Inicializa la base de datos creando las tablas necesarias.
        
        Returns:
            True si se inicializó correctamente
        """
        pass


