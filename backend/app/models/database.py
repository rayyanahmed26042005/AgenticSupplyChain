"""
Database ORM models (placeholder for future persistence).
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON
from datetime import datetime
from app.data.storage.database import Base


class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, default="")
    days = Column(Integer)
    disruptions = Column(Integer)
    base_demand = Column(Float)
    seed = Column(Integer)
    status = Column(String, default="completed")
    statistics = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentDecision(Base):
    __tablename__ = "agent_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String)
    action = Column(String)
    details = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
