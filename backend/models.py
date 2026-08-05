from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    role = Column(String(20), default="cyclist")  # admin, cyclist
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    bikes = relationship("Bike", back_populates="owner")

class Bike(Base):
    __tablename__ = "bikes"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    serial_number = Column(String(100), unique=True, nullable=False)
    brand = Column(String(50), nullable=False)
    model = Column(String(50), nullable=True)
    type = Column(String(20), default="traditional")  # traditional, electric
    qr_code = Column(String(100), unique=True, index=True, nullable=False)  # token único para el QR
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="bikes")
    parking_records = relationship("ParkingRecord", back_populates="bike")

class ParkingRecord(Base):
    __tablename__ = "parking_records"

    id = Column(Integer, primary_key=True, index=True)
    bike_id = Column(Integer, ForeignKey("bikes.id"), nullable=False)
    entry_time = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    exit_time = Column(DateTime, nullable=True)
    status = Column(String(20), default="active")  # active, pending_payment, completed
    base_rate = Column(Float, default=100.0)  # Tarifa por minuto (ej. 100 COP)
    total_amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    bike = relationship("Bike", back_populates="parking_records")
    energy_consumption = relationship("EnergyConsumption", back_populates="parking_record", uselist=False)
    payments = relationship("Payment", back_populates="parking_record")

class EnergyConsumption(Base):
    __tablename__ = "energy_consumptions"

    id = Column(Integer, primary_key=True, index=True)
    parking_record_id = Column(Integer, ForeignKey("parking_records.id"), nullable=False)
    charge_start_time = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    charge_end_time = Column(DateTime, nullable=True)
    energy_consumed_kwh = Column(Float, default=0.0)  # kWh consumidos medidos
    energy_rate = Column(Float, default=500.0)  # Precio por kWh (ej: 500 COP)
    energy_amount = Column(Float, default=0.0)  # Costo total de energía
    status = Column(String(20), default="active")  # active, completed

    parking_record = relationship("ParkingRecord", back_populates="energy_consumption")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    parking_record_id = Column(Integer, ForeignKey("parking_records.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50), default="online")  # online, cash
    status = Column(String(20), default="pending")  # pending, paid, failed
    transaction_id = Column(String(100), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    parking_record = relationship("ParkingRecord", back_populates="payments")
