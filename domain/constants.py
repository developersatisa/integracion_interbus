"""
Constantes del dominio.
Define las entidades disponibles para sincronización.
"""
from typing import List

# Lista de entidades de Dynamics 365 a sincronizar
ENTITIES: List[str] = [
    'CompanyATISAs',
    'WorkerPlaces',
    'ContributionAccountCodeCCs',
    'HolidaysAbsencesGroupATISAs',
    'VacationBalances',
    'IncidentGroupATISAs',
    'AdvanceGroupATISAs',
    'LibrariesGroupATISAs',
    'LeaveGroupATISAs',
    'VacationCalenders',
    'HighsLowsChanges'
]


# Diccionario de mapeo de entidades a nombres descriptivos
ENTITY_NAMES: dict[str, str] = {
    'CompanyATISAs': 'Compañías ATISAs',
    'WorkerPlaces': 'Lugares de Trabajo',
    'ContributionAccountCodeCCs': 'Códigos de Cuenta de Contribución',
    'HolidaysAbsencesGroupATISAs': 'Grupos de Vacaciones y Ausencias',
    'VacationBalances': 'Balances de Vacaciones',
    'IncidentGroupATISAs': 'Grupos de Incidentes',
    'AdvanceGroupATISAs': 'Grupos de Avances',
    'LibrariesGroupATISAs': 'Grupos de Bibliotecas',
    'LeaveGroupATISAs': 'Grupos de Licencias',
    'VacationCalenders': 'Calendarios de Vacaciones',
    'HighsLowsChanges': 'Cambios de Altas y Bajas'
}


