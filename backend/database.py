# database.py

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

# This creates (or connects to) a SQLite database file called sentiment.db
# The file will appear in your backend/ folder automatically
# "check_same_thread=False" is needed for FastAPI which uses multiple threads
engine = create_engine(
    "sqlite:///./sentiment.db",
    connect_args={"check_same_thread": False}
)

# SessionLocal is a factory that creates database sessions
# A session = one conversation with the database
# Open session → do work → close session
SessionLocal = sessionmaker(bind=engine)

# Base is the parent class all our table models will inherit from
Base = declarative_base()


# ── This class defines our database table ────────────────────────────────────

class SearchRecord(Base):
    """
    Every time someone calls /analyze/{ticker}, we save one row here.
    
    The class name = the Python object
    __tablename__ = the actual table name in the database
    Each Column = one column in the table
    """
    __tablename__ = "searches"

    # Integer primary key — auto-increments (1, 2, 3...)
    # This uniquely identifies every row
    id = Column(Integer, primary_key=True, index=True)

    # The stock ticker searched — max 20 characters
    ticker = Column(String(20), nullable=False, index=True)
    # index=True means: make this column fast to search by
    # without index: "find all TSLA rows" = scan every row
    # with index:    "find all TSLA rows" = instant lookup

    # The company name (Tesla, Apple, etc.)
    company = Column(String(100))

    # The overall signal we calculated
    signal = Column(String(20), nullable=False)

    # Average confidence score across all headlines
    avg_confidence = Column(Float)

    # How many headlines we analyzed
    headline_count = Column(Integer)

    # The full breakdown as JSON string: {"positive": 3, "negative": 0, "neutral": 7}
    # SQLite doesn't have a native JSON column type, so we store it as text
    breakdown_json = Column(Text)

    # The full headlines + sentiments as JSON
    # This is the complete result — we store it so we never need to re-fetch
    headlines_json = Column(Text)

    # When was this search made — defaults to right now automatically
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Create the table if it doesn't exist ─────────────────────────────────────
# This runs when the file is imported
# If the table already exists, it does nothing (safe to call repeatedly)
Base.metadata.create_all(bind=engine)


# ── Helper functions ──────────────────────────────────────────────────────────

def save_search(ticker: str, company: str, result: dict) -> SearchRecord:
    """
    Save one analysis result to the database.
    
    We open a session, add the record, commit it (save permanently),
    then close the session. Always close sessions — they hold resources.
    """
    db = SessionLocal()
    
    try:
        record = SearchRecord(
            ticker=ticker,
            company=company,
            signal=result["overall_signal"],
            avg_confidence=result["avg_confidence"],
            headline_count=result["headline_count"],
            # json.dumps() converts a Python dict → JSON string for storage
            breakdown_json=json.dumps(result["breakdown"]),
            headlines_json=json.dumps(result["headlines"]),
        )
        
        # Add the record to the session (not saved to disk yet)
        db.add(record)
        
        # Commit = write to disk permanently
        # If this fails, nothing is saved (atomic operation)
        db.commit()
        
        # Refresh loads the auto-generated id back into our object
        db.refresh(record)
        
        return record
        
    except Exception as e:
        # If anything went wrong, roll back — don't save partial data
        db.rollback()
        raise e
        
    finally:
        # Always close the session whether it succeeded or failed
        db.close()


def get_search_history(ticker: str = None, limit: int = 20) -> list[dict]:
    """
    Fetch past searches from the database.
    
    If ticker is provided: return history for that specific ticker
    If ticker is None: return all recent searches
    """
    db = SessionLocal()
    
    try:
        # Start building the query
        query = db.query(SearchRecord)
        
        # Filter by ticker if provided
        # .filter() = WHERE clause in SQL
        if ticker:
            query = query.filter(SearchRecord.ticker == ticker.upper())
        
        # .order_by() = ORDER BY in SQL
        # descending = newest first
        # .limit() = only return N rows
        records = query.order_by(SearchRecord.created_at.desc()).limit(limit).all()
        
        # Convert each record to a dictionary for the API response
        result = []
        for r in records:
            result.append({
                "id": r.id,
                "ticker": r.ticker,
                "company": r.company,
                "signal": r.signal,
                "avg_confidence": r.avg_confidence,
                "headline_count": r.headline_count,
                # json.loads() converts JSON string back to Python dict
                "breakdown": json.loads(r.breakdown_json) if r.breakdown_json else {},
                "created_at": r.created_at.isoformat(),
            })
        
        return result
        
    finally:
        db.close()


def get_ticker_stats(ticker: str) -> dict:
    """
    Aggregate stats for a ticker across all its searches.
    
    Example output:
    {
        "ticker": "TSLA",
        "total_searches": 5,
        "signal_history": ["neutral", "positive", "neutral", "negative", "positive"],
        "most_common_signal": "neutral"
    }
    
    This is useful for showing trends — is TSLA getting more positive over time?
    """
    db = SessionLocal()
    
    try:
        records = db.query(SearchRecord)\
            .filter(SearchRecord.ticker == ticker.upper())\
            .order_by(SearchRecord.created_at.desc())\
            .all()
        
        if not records:
            return {"ticker": ticker.upper(), "total_searches": 0}
        
        signals = [r.signal for r in records]
        
        # Count occurrences of each signal
        signal_counts = {}
        for s in signals:
            signal_counts[s] = signal_counts.get(s, 0) + 1
        
        most_common = max(signal_counts, key=signal_counts.get)
        
        return {
            "ticker": ticker.upper(),
            "total_searches": len(records),
            "signal_history": signals,
            "signal_counts": signal_counts,
            "most_common_signal": most_common,
            "latest_signal": signals[0] if signals else None,
        }
        
    finally:
        db.close()