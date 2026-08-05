from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
import datetime
import uuid
from typing import List, Optional

from database import engine, Base, get_db
import models
import schemas

# Crear tablas si se usa SQLite localmente (para despliegue fácil)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Biciparking API", description="Sistema de Gestión Integral de Biciparking")

# Configurar CORS para permitir comunicación con el frontend de VueJS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, restringir a los dominios del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de Biciparking - Sistema Digital de Gestión"}


# --- AUTHENTICATION & USERS ---

@app.post("/api/auth/register", response_model=schemas.UserOut)
def register_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user_in.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está registrado.")
    
    db_email = db.query(models.User).filter(models.User.email == user_in.email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado.")
    
    # En producción usaríamos un hashing seguro como bcrypt/passlib, para este mockup guardamos simplificado
    new_user = models.User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=user_in.password,  # Guardado simple para fines demostrativos
        role=user_in.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/api/auth/login")
def login_user(login_in: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == login_in.username).first()
    if not user or user.hashed_password != login_in.password:
        raise HTTPException(status_code=400, detail="Credenciales incorrectas.")
    
    return {
        "access_token": f"mock-token-{user.id}",
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    }


@app.get("/api/users", response_model=List[schemas.UserOut])
def get_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()


# --- BICYCLE MANAGEMENT ---

@app.post("/api/bikes", response_model=schemas.BikeOut)
def register_bike(owner_id: int, bike_in: schemas.BikeCreate, db: Session = Depends(get_db)):
    # Verificar si el dueño existe
    owner = db.query(models.User).filter(models.User.id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Usuario dueño no encontrado.")
    
    # Verificar si el número de serie ya existe
    existing_bike = db.query(models.Bike).filter(models.Bike.serial_number == bike_in.serial_number).first()
    if existing_bike:
        raise HTTPException(status_code=400, detail="Este número de serie ya está registrado.")

    # Generar un código QR único (UUID representativo)
    qr_token = f"QR-BIKE-{uuid.uuid4().hex[:12].upper()}"

    new_bike = models.Bike(
        owner_id=owner_id,
        serial_number=bike_in.serial_number,
        brand=bike_in.brand,
        model=bike_in.model,
        type=bike_in.type,
        qr_code=qr_token
    )
    db.add(new_bike)
    db.commit()
    db.refresh(new_bike)
    return new_bike


@app.get("/api/bikes", response_model=List[schemas.BikeOut])
def get_all_bikes(owner_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.Bike)
    if owner_id:
        query = query.filter(models.Bike.owner_id == owner_id)
    return query.all()


# --- PARKING REGISTRATION & CONTROL (QR CODE CHECK-IN / CHECK-OUT) ---

@app.post("/api/parking/check-in", response_model=schemas.ParkingRecordOut)
def parking_check_in(req: schemas.CheckInRequest, db: Session = Depends(get_db)):
    # Buscar la bicicleta por el código QR
    bike = db.query(models.Bike).filter(models.Bike.qr_code == req.qr_code).first()
    if not bike:
        raise HTTPException(status_code=404, detail="Código QR no válido. Bicicleta no registrada.")
    
    # Verificar si ya tiene un parqueo activo
    active_parking = db.query(models.ParkingRecord).filter(
        models.ParkingRecord.bike_id == bike.id,
        models.ParkingRecord.status == "active"
    ).first()
    
    if active_parking:
        raise HTTPException(status_code=400, detail="Esta bicicleta ya cuenta con un ingreso de parqueo activo.")

    # Crear registro de parqueo
    new_parking = models.ParkingRecord(
        bike_id=bike.id,
        entry_time=datetime.datetime.utcnow(),
        status="active",
        base_rate=100.0  # COP por minuto
    )
    db.add(new_parking)
    db.commit()
    db.refresh(new_parking)
    
    # Retornar con relaciones cargadas
    return db.query(models.ParkingRecord).options(
        joinedload(models.ParkingRecord.bike).joinedload(models.Bike.owner)
    ).filter(models.ParkingRecord.id == new_parking.id).first()


@app.post("/api/parking/check-out")
def parking_check_out(req: schemas.CheckOutRequest, db: Session = Depends(get_db)):
    # Buscar bicicleta por QR
    bike = db.query(models.Bike).filter(models.Bike.qr_code == req.qr_code).first()
    if not bike:
        raise HTTPException(status_code=404, detail="Código QR no válido.")

    # Buscar parqueo activo
    parking = db.query(models.ParkingRecord).filter(
        models.ParkingRecord.bike_id == bike.id,
        models.ParkingRecord.status == "active"
    ).first()

    if not parking:
        raise HTTPException(status_code=400, detail="No se encontró un parqueo activo para esta bicicleta.")

    now = datetime.datetime.utcnow()
    parking.exit_time = now

    # Calcular tiempo en minutos (mínimo 1 minuto para pruebas si fue instantáneo)
    duration_seconds = (now - parking.entry_time).total_seconds()
    duration_minutes = max(1.0, duration_seconds / 60.0)
    
    # Calcular costo de parqueo
    parking_cost = duration_minutes * parking.base_rate

    # Verificar si hubo servicio de carga eléctrica
    energy_cost = 0.0
    energy_rec = db.query(models.EnergyConsumption).filter(
        models.EnergyConsumption.parking_record_id == parking.id,
        models.EnergyConsumption.status == "active"
    ).first()

    if energy_rec:
        # Detener la carga automáticamente al salir
        energy_rec.charge_end_time = now
        energy_rec.status = "completed"
        
        # Simular consumo basado en el tiempo de carga (e.g. 0.05 kWh por minuto)
        charge_duration_minutes = max(1.0, (now - energy_rec.charge_start_time).total_seconds() / 60.0)
        energy_rec.energy_consumed_kwh = round(charge_duration_minutes * 0.05, 2)
        energy_rec.energy_amount = energy_rec.energy_consumed_kwh * energy_rec.energy_rate
        energy_cost = energy_rec.energy_amount

    # Actualizar monto total y estado
    parking.total_amount = round(parking_cost + energy_cost, 2)
    parking.status = "pending_payment"
    db.commit()

    return {
        "message": "Salida registrada con éxito. Pago pendiente.",
        "parking_record_id": parking.id,
        "entry_time": parking.entry_time,
        "exit_time": parking.exit_time,
        "duration_minutes": round(duration_minutes, 1),
        "parking_cost": round(parking_cost, 2),
        "energy_cost": round(energy_cost, 2),
        "total_amount": parking.total_amount,
        "payment_link": f"/payment/{parking.id}"  # Enlace simulado de pasarela de pago
    }


@app.get("/api/parking/active", response_model=List[schemas.ParkingRecordOut])
def get_active_parkings(db: Session = Depends(get_db)):
    return db.query(models.ParkingRecord).options(
        joinedload(models.ParkingRecord.bike).joinedload(models.Bike.owner),
        joinedload(models.ParkingRecord.energy_consumption)
    ).filter(models.ParkingRecord.status == "active").all()


@app.get("/api/parking/history", response_model=List[schemas.ParkingRecordOut])
def get_parking_history(owner_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.ParkingRecord).options(
        joinedload(models.ParkingRecord.bike).joinedload(models.Bike.owner),
        joinedload(models.ParkingRecord.energy_consumption)
    )
    if owner_id:
        query = query.join(models.Bike).filter(models.Bike.owner_id == owner_id)
    return query.order_by(models.ParkingRecord.entry_time.desc()).all()


# --- ENERGY / E-BIKE CHARGING MANAGEMENT ---

@app.post("/api/energy/start-charge", response_model=schemas.EnergyConsumptionOut)
def start_charging(req: schemas.ToggleChargeRequest, db: Session = Depends(get_db)):
    # Verificar si el parqueo existe y está activo
    parking = db.query(models.ParkingRecord).filter(
        models.ParkingRecord.id == req.parking_record_id,
        models.ParkingRecord.status == "active"
    ).first()

    if not parking:
        raise HTTPException(status_code=404, detail="Registro de parqueo activo no encontrado.")

    # Verificar que sea de tipo eléctrica
    bike = db.query(models.Bike).filter(models.Bike.id == parking.bike_id).first()
    if bike.type != "electric":
        raise HTTPException(status_code=400, detail="Esta bicicleta no es eléctrica, no admite servicio de carga.")

    # Verificar si ya tiene una carga activa
    existing_charge = db.query(models.EnergyConsumption).filter(
        models.EnergyConsumption.parking_record_id == parking.id,
        models.EnergyConsumption.status == "active"
    ).first()

    if existing_charge:
        raise HTTPException(status_code=400, detail="La carga de energía ya está activa para esta bicicleta.")

    # Crear registro de carga
    new_charge = models.EnergyConsumption(
        parking_record_id=parking.id,
        charge_start_time=datetime.datetime.utcnow(),
        energy_rate=500.0,  # COP por kWh
        status="active"
    )
    db.add(new_charge)
    db.commit()
    db.refresh(new_charge)
    return new_charge


@app.post("/api/energy/stop-charge", response_model=schemas.EnergyConsumptionOut)
def stop_charging(req: schemas.ToggleChargeRequest, db: Session = Depends(get_db)):
    # Buscar carga activa
    charge = db.query(models.EnergyConsumption).filter(
        models.EnergyConsumption.parking_record_id == req.parking_record_id,
        models.EnergyConsumption.status == "active"
    ).first()

    if not charge:
        raise HTTPException(status_code=404, detail="No se encontró una carga de energía activa.")

    now = datetime.datetime.utcnow()
    charge.charge_end_time = now
    charge.status = "completed"

    # Simulación de consumo: 0.05 kWh por minuto transcurrido
    duration_minutes = max(1.0, (now - charge.charge_start_time).total_seconds() / 60.0)
    charge.energy_consumed_kwh = round(duration_minutes * 0.05, 2)
    charge.energy_amount = round(charge.energy_consumed_kwh * charge.energy_rate, 2)

    db.commit()
    db.refresh(charge)
    return charge


# --- PAYMENTS SIMULATION ---

@app.post("/api/payments/process")
def process_payment(req: schemas.PaymentCreate, db: Session = Depends(get_db)):
    parking = db.query(models.ParkingRecord).filter(
        models.ParkingRecord.id == req.parking_record_id
    ).first()

    if not parking:
        raise HTTPException(status_code=404, detail="Registro de parqueo no encontrado.")
    
    if parking.status != "pending_payment":
        raise HTTPException(status_code=400, detail=f"El registro no se encuentra pendiente de pago (Estado: {parking.status}).")

    # Registrar el pago exitoso (simulado)
    transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
    new_payment = models.Payment(
        parking_record_id=parking.id,
        amount=parking.total_amount,
        payment_method=req.payment_method,
        status="paid",
        transaction_id=transaction_id
    )
    
    # Actualizar parqueo a completado
    parking.status = "completed"
    
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    return {
        "message": "¡Pago procesado con éxito!",
        "payment": {
            "id": new_payment.id,
            "amount": new_payment.amount,
            "payment_method": new_payment.payment_method,
            "status": new_payment.status,
            "transaction_id": new_payment.transaction_id,
            "created_at": new_payment.created_at
        },
        "parking_record_id": parking.id
    }


# --- DASHBOARD STATS ---

@app.get("/api/dashboard/stats", response_model=schemas.DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    active_parkings = db.query(models.ParkingRecord).filter(models.ParkingRecord.status == "active").count()
    active_charges = db.query(models.EnergyConsumption).filter(models.EnergyConsumption.status == "active").count()
    total_registered_bikes = db.query(models.Bike).count()
    
    # Calcular ingresos totales sumando los pagos exitosos
    revenue_sum = db.query(models.Payment).filter(models.Payment.status == "paid").sum(models.Payment.amount)
    total_revenue = float(revenue_sum) if revenue_sum is not None else 0.0

    # Alternativa manual por si el driver o ORM devuelve None en query vacía
    payments = db.query(models.Payment).filter(models.Payment.status == "paid").all()
    total_revenue = sum([p.amount for p in payments])

    return {
        "active_parkings": active_parkings,
        "active_charges": active_charges,
        "total_registered_bikes": total_registered_bikes,
        "total_revenue": total_revenue
    }
