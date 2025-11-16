"""
Database migration script to add Grad-CAM fields.
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import logging
from sqlalchemy import inspect, text
from src.app.database import DatabaseManager, AnalysisJob

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_add_gradcam_fields():
    """
    Add Grad-CAM fields to existing database.
    Safe to run multiple times - checks if columns exist first.
    """
    db = DatabaseManager()
    
    # Check if columns already exist
    inspector = inspect(db.engine)
    existing_columns = [col['name'] for col in inspector.get_columns('analysis_jobs')]
    
    new_columns = {
        'gradcam_enabled': 'BOOLEAN DEFAULT 0 NOT NULL',
        'gradcam_dir': 'VARCHAR(500)',
        'gradcam_avg_heatmap': 'VARCHAR(500)',
        'gradcam_frame_count': 'INTEGER'
    }
    
    # Add missing columns
    added_count = 0
    with db.engine.connect() as connection:
        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                logger.info(f"Adding column: {column_name}")
                try:
                    # SQLite ALTER TABLE syntax
                    connection.execute(
                        text(f"ALTER TABLE analysis_jobs ADD COLUMN {column_name} {column_type}")
                    )
                    connection.commit()
                    added_count += 1
                    logger.info(f"✅ Added column: {column_name}")
                except Exception as e:
                    logger.error(f"❌ Failed to add column {column_name}: {e}")
            else:
                logger.info(f"✓ Column {column_name} already exists, skipping")
    
    if added_count > 0:
        logger.info(f"🎉 Migration complete! Added {added_count} new columns")
    else:
        logger.info("✅ Database already up to date")


if __name__ == '__main__':
    logger.info("Starting database migration...")
    migrate_add_gradcam_fields()
    logger.info("Migration finished!")
