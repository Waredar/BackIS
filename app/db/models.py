# app/db/models.py

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Numeric, Date, Text, TIMESTAMP
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

# ========== AUTH TABLES ==========

class Role(Base):
    __tablename__ = "roles"
    roleid = Column(Integer, primary_key=True, index=True)
    rolename = Column(String(50), unique=True, nullable=False)
    users = relationship("UserRole", back_populates="role")

class User(Base):
    __tablename__ = "users"
    userid = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashedpassword = Column(String(255), nullable=False)
    fullname = Column(String(100))
    isactive = Column(Boolean, default=True, nullable=False)
    createdat = Column(TIMESTAMP, server_default=func.now())
    roles = relationship("UserRole", back_populates="user")

class UserRole(Base):
    __tablename__ = "user_roles"
    userid = Column(Integer, ForeignKey("users.userid"), primary_key=True)
    roleid = Column(Integer, ForeignKey("roles.roleid"), primary_key=True)
    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")

# ========== BUSINESS TABLES ==========

class DimDate(Base):
    __tablename__ = "dimdate"
    dateid = Column(Integer, primary_key=True)
    fulldate = Column(Date, unique=True, nullable=False)
    year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    monthname = Column(String(20), nullable=False)
    week = Column(Integer, nullable=False)
    dayofmonth = Column(Integer, nullable=False)
    dayofweek = Column(Integer, nullable=False)
    dayname = Column(String(20), nullable=False)
    isweekend = Column(Boolean, nullable=False)
    season = Column(String(20), nullable=False)

class Client(Base):
    __tablename__ = "clients"
    clientid = Column(Integer, primary_key=True)
    fullname = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(100))
    birthdate = Column(Date)
    registrationdate = Column(TIMESTAMP, nullable=False, server_default=func.now())
    loyaltystatus = Column(String(30), nullable=False, default='Basic')
    notes = Column(Text)

class Master(Base):
    __tablename__ = "masters"
    masterid = Column(Integer, primary_key=True)
    fullname = Column(String(100), nullable=False)
    specialization = Column(String(100))
    phone = Column(String(20), nullable=False)
    # Расширенные поля
    email = Column(String(100))
    passport = Column(String(20))
    emergencycontactphone = Column(String(20))
    address = Column(String(200))
    birthdate = Column(Date)
    hiredate = Column(Date, nullable=False)
    firedate = Column(Date)
    salary = Column(Numeric(10, 2))
    commissionpercent = Column(Numeric(5, 2), default=0)
    paymenttype = Column(String(20), default='Monthly')
    education = Column(String(255))
    photo = Column(String(255))
    rating = Column(Numeric(3, 2))
    isactive = Column(Boolean, nullable=False, default=True)

class Service(Base):
    __tablename__ = "services"
    serviceid = Column(Integer, primary_key=True)
    servicename = Column(String(100), nullable=False)
    description = Column(String(255))
    category = Column(String(50))
    durationminutes = Column(Integer, nullable=False)
    baseprice = Column(Numeric(10, 2), nullable=False)
    isactive = Column(Boolean, nullable=False, default=True)

class Product(Base):
    __tablename__ = "products"
    productid = Column(Integer, primary_key=True)
    productname = Column(String(100), nullable=False)
    category = Column(String(50))
    unit = Column(String(20), nullable=False)
    unitprice = Column(Numeric(10, 2), nullable=False)
    stockquantity = Column(Integer, nullable=False, default=0)
    isactive = Column(Boolean, nullable=False, default=True)

class Appointment(Base):
    __tablename__ = "appointments"
    appointmentid = Column(Integer, primary_key=True)
    clientid = Column(Integer, ForeignKey("clients.clientid"), nullable=False)
    masterid = Column(Integer, ForeignKey("masters.masterid"), nullable=False)
    # Связь с DimDate обязательна
    dateid = Column(Integer, ForeignKey("dimdate.dateid"), nullable=False)
    startdatetime = Column(TIMESTAMP, nullable=False)
    enddatetime = Column(TIMESTAMP)
    status = Column(String(20), nullable=False, default='Planned')
    source = Column(String(20), nullable=False)
    createdat = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updatedat = Column(TIMESTAMP)

class AppointmentService(Base):
    __tablename__ = "appointmentservices"
    appointmentid = Column(Integer, ForeignKey("appointments.appointmentid"), primary_key=True)
    serviceid = Column(Integer, ForeignKey("services.serviceid"), primary_key=True)
    quantity = Column(Integer, nullable=False, default=1)
    priceatvisit = Column(Numeric(10, 2), nullable=False)
    discountamount = Column(Numeric(10, 2), nullable=False, default=0)

class AppointmentProduct(Base):
    __tablename__ = "appointmentproducts"
    appointmentid = Column(Integer, ForeignKey("appointments.appointmentid"), primary_key=True)
    productid = Column(Integer, ForeignKey("products.productid"), primary_key=True)
    quantity = Column(Integer, nullable=False, default=1)
    priceatvisit = Column(Numeric(10, 2), nullable=False)
    discountamount = Column(Numeric(10, 2), nullable=False, default=0)

class Payment(Base):
    __tablename__ = "payments"
    paymentid = Column(Integer, primary_key=True)
    appointmentid = Column(Integer, ForeignKey("appointments.appointmentid"), nullable=False)
    paymentdatetime = Column(TIMESTAMP, nullable=False, server_default=func.now())
    amount = Column(Numeric(10, 2), nullable=False)
    discounttotal = Column(Numeric(10, 2), nullable=False, default=0)
    amountpaid = Column(Numeric(10, 2), nullable=False)
    paymentmethod = Column(String(20), nullable=False)
    paymentstatus = Column(String(20), nullable=False, default='Pending')
