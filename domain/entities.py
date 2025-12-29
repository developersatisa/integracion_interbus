"""
Entidades de dominio que representan las entidades de Dynamics 365.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class DynamicsEntity:
    """Entidad base para todas las entidades de Dynamics 365."""
    pass


@dataclass
class CompanyATISA(DynamicsEntity):
    """Entidad CompanyATISA."""
    data_area_id: str
    company_atisa_id: str
    description: Optional[str] = None
    raw_data: Optional[Dict[Any, Any]] = None


@dataclass
class WorkerPlace(DynamicsEntity):
    """Entidad WorkerPlace."""
    data_area_id: str
    worker_place_id: str
    description: Optional[str] = None
    raw_data: Optional[Dict[Any, Any]] = None


@dataclass
class ContributionAccountCodeCC(DynamicsEntity):
    """Entidad ContributionAccountCodeCC."""
    data_area_id: str
    contribution_account_code_cc_id: str
    description: Optional[str] = None
    raw_data: Optional[Dict[Any, Any]] = None


@dataclass
class HolidaysAbsencesGroupATISA(DynamicsEntity):
    """Entidad HolidaysAbsencesGroupATISA."""
    data_area_id: str
    holidays_absences_group_atisa_id: str
    description: Optional[str] = None
    raw_data: Optional[Dict[Any, Any]] = None


@dataclass
class VacationBalance(DynamicsEntity):
    """Entidad VacationBalance."""
    data_area_id: str
    vacation_balance_id: str
    description: Optional[str] = None
    raw_data: Optional[Dict[Any, Any]] = None


@dataclass
class IncidentGroupATISA(DynamicsEntity):
    """Entidad IncidentGroupATISA."""
    data_area_id: str
    incident_group_atisa_id: str
    description: Optional[str] = None
    raw_data: Optional[Dict[Any, Any]] = None


@dataclass
class AdvanceGroupATISA(DynamicsEntity):
    """Entidad AdvanceGroupATISA."""
    data_area_id: str
    advance_group_atisa_id: str
    description: Optional[str] = None
    raw_data: Optional[Dict[Any, Any]] = None


@dataclass
class LibrariesGroupATISA(DynamicsEntity):
    """Entidad LibrariesGroupATISA."""
    data_area_id: str
    libraries_group_atisa_id: str
    description: Optional[str] = None
    raw_data: Optional[Dict[Any, Any]] = None


@dataclass
class LeaveGroupATISA(DynamicsEntity):
    """Entidad LeaveGroupATISA."""
    data_area_id: str
    leave_group_atisa_id: str
    description: Optional[str] = None
    raw_data: Optional[Dict[Any, Any]] = None


@dataclass
class VacationCalendar(DynamicsEntity):
    """Entidad VacationCalendar."""
    data_area_id: str
    vacation_calendar_id: str
    description: Optional[str] = None
    raw_data: Optional[Dict[Any, Any]] = None


@dataclass
class HighsLowsChange(DynamicsEntity):
    """Entidad HighsLowsChange."""
    data_area_id: str
    highs_lows_change_id: str
    description: Optional[str] = None
    raw_data: Optional[Dict[Any, Any]] = None


