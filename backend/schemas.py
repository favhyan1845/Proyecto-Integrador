from pydantic import BaseModel, EmailStr
from typing import Optional, List
import datetime

# --- USUARIOS ---
class UserBase(BaseModel):
    full_name: Optional[str] = None
    username: str
    email: EmailStr
    role: Optional[str] = "cyclist"

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(UserBase):
    id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# --- BICICLETAS ---
class BikeBase(BaseModel):
    serial_number: str
    brand: str
    model: Optional[str] = None
    type: str  # traditional, electric

class BikeCreate(BikeBase):
    pass

class BikeOut(BikeBase):
    id: int
    owner_id: int
    qr_code: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# --- CONSUMO DE ENERGÍA ---
class EnergyConsumptionBase(BaseModel):
    energy_consumed_kwh: float
    energy_rate: float
    energy_amount: float
    status: str

class EnergyConsumptionOut(EnergyConsumptionBase):
    id: int
    parking_record_id: int
    charge_start_time: datetime.datetime
    charge_end_time: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True


# --- REGISTRO DE PARQUEO (PARKING) ---
class ParkingRecordBase(BaseModel):
    bike_id: int
    entry_time: datetime.datetime
    exit_time: Optional[datetime.datetime] = None
    status: str
    base_rate: float
    total_amount: float

class ParkingRecordOut(ParkingRecordBase):
    id: int
    bike: BikeOut
    energy_consumption: Optional[EnergyConsumptionOut] = None

    class Config:
        from_attributes = True


# --- PAGOS ---
class PaymentBase(BaseModel):
    amount: float
    payment_method: str
    status: str
    transaction_id: Optional[str] = None

class PaymentCreate(BaseModel):
    parking_record_id: int
    payment_method: str

class PaymentOut(PaymentBase):
    id: int
    parking_record_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# --- SOLICITUDES Y ACCIONES ---
class CheckInRequest(BaseModel):
    qr_code: str

class CheckOutRequest(BaseModel):
    qr_code: str

class ToggleChargeRequest(BaseModel):
    parking_record_id: int

# --- ESTADÍSTICAS ---
class DashboardStats(BaseModel):
    active_parkings: int
    active_charges: int
    total_registered_bikes: int
    total_revenue: float
