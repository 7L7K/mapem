from sqlalchemy import (
    Column, BigInteger, Integer, String, Date, DateTime,
    Float, JSON, ForeignKey, Index
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class Individual(Base):
    __tablename__ = "individuals"
    def to_dict(self):
        return {
            "id": self.id,
            "gedcom_id": self.gedcom_id,
            "tree_id": self.tree_id,
            "name": self.name,
            "occupation": self.occupation,
            "notes": self.notes
        }

    id         = Column(BigInteger, primary_key=True, autoincrement=True)
    gedcom_id  = Column(String)
    tree_id    = Column(BigInteger, ForeignKey("uploaded_trees.id"), index=True)
    name       = Column(String, nullable=False)
    occupation = Column(String)
    notes      = Column(String)

    events      = relationship("Event", back_populates="individual")
    residences  = relationship("ResidenceHistory", back_populates="individual")
    sources     = relationship("IndividualSource", back_populates="individual")

class Family(Base):
    __tablename__ = "families"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    gedcom_id  = Column(String)
    tree_id    = Column(BigInteger, ForeignKey("uploaded_trees.id"), index=True)
    husband_id = Column(BigInteger, ForeignKey("individuals.id"))
    wife_id    = Column(BigInteger, ForeignKey("individuals.id"))
    extra_details = Column(JSON)

    events = relationship("Event", back_populates="family")

class Event(Base):
    __tablename__ = "events"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    event_type     = Column(String, nullable=False)
    date           = Column(Date)
    date_precision = Column(String)
    notes          = Column(String)
    source_tag     = Column(String)          # NEW: GEDCOM tag that generated this event
    category       = Column(String)          # NEW: e.g. "life_event", "migration", "religious"
    
    individual_id  = Column(BigInteger, ForeignKey("individuals.id"))
    family_id      = Column(Integer, ForeignKey("families.id"))
    location_id    = Column(Integer, ForeignKey("locations.id"))
    tree_id        = Column(BigInteger, ForeignKey("uploaded_trees.id"), index=True)

    individual = relationship("Individual", back_populates="events")
    family     = relationship("Family", back_populates="events")
    location   = relationship("Location")


class Location(Base):
    __tablename__ = "locations"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    raw_name        = Column(String, nullable=False)      # ✅ ADD THIS
    name            = Column(String, unique=True)
    normalized_name = Column(String)          # NEW: Standardized version for deduplication
    latitude        = Column(Float)
    longitude       = Column(Float)
    confidence_score= Column(Float)           # NEW: Confidence of the geocode result
    timestamp       = Column(DateTime, default=datetime.utcnow)
    historical_data = Column(JSON)

class ResidenceHistory(Base):
    __tablename__ = "residence_history"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    individual_id = Column(BigInteger, ForeignKey("individuals.id"))
    location_id   = Column(Integer, ForeignKey("locations.id"))
    start_date    = Column(Date)
    end_date      = Column(Date)
    notes         = Column(String)

    individual = relationship("Individual", back_populates="residences")
    location   = relationship("Location")

class TreeVersion(Base):
    __tablename__ = "tree_versions"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    tree_name      = Column(String, nullable=False)
    version_number = Column(Integer, nullable=False)
    created_at     = Column(DateTime, default=datetime.utcnow)
    diff_summary   = Column(JSON)

class Source(Base):
    __tablename__ = "sources"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    source_type = Column(String)
    description = Column(String)
    url         = Column(String)

class IndividualSource(Base):
    __tablename__ = "individual_sources"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    individual_id = Column(BigInteger, ForeignKey("individuals.id"))
    source_id     = Column(Integer, ForeignKey("sources.id"))
    notes         = Column(String)

    individual = relationship("Individual", back_populates="sources")
    source     = relationship("Source")

class UserAction(Base):
    __tablename__ = "user_actions"
    id        = Column(Integer, primary_key=True, autoincrement=True)
    user_id   = Column(Integer)
    action_type = Column(String)
    context   = Column(JSON)
    decision  = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    tree_id   = Column(BigInteger, ForeignKey("uploaded_trees.id"))

class UploadedTree(Base):
    __tablename__ = "uploaded_trees"
    id                = Column(BigInteger, primary_key=True, autoincrement=True)
    uploaded_at       = Column(DateTime, default=datetime.utcnow)
    original_filename = Column(String)
    uploader_name     = Column(String)
    notes             = Column(String)

class TreePerson(Base):
    __tablename__ = "tree_people"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    tree_id         = Column(BigInteger, ForeignKey("uploaded_trees.id"), index=True)
    first_name      = Column(String)
    last_name       = Column(String)
    full_name       = Column(String)
    birth_date      = Column(Date)
    death_date      = Column(Date)
    birth_location  = Column(String)
    death_location  = Column(String)
    gender          = Column(String)
    occupation      = Column(String)
    race            = Column(String)
    external_id     = Column(String)
    notes           = Column(String)

class TreeRelationship(Base):
    __tablename__ = "tree_relationships"
    id               = Column(Integer, primary_key=True, autoincrement=True)
    tree_id          = Column(BigInteger, ForeignKey("uploaded_trees.id"), index=True)
    person_id        = Column(Integer)
    related_person_id= Column(Integer)
    relationship_type= Column(String)
    notes            = Column(String)

# handy composite indexes
Index("ix_individuals_tree_gedcom", Individual.tree_id, Individual.gedcom_id)
Index("ix_families_tree_gedcom",   Family.tree_id,     Family.gedcom_id)
