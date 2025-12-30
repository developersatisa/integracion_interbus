import sys
import os
import logging
from pathlib import Path
import mysql.connector
from mysql.connector import Error

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def list_dfo_altas():
    logger.info("🔍 Consultando tabla dfo_com_altas (interbus_365)...")
    
    connection = None
    cursor = None
    
    try:
        connection = mysql.connector.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            database="interbus_365"
        )
        
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            
            # Consultar últimos 20 registros
            query = """
                SELECT id, etag, personnel_number, created_date 
                FROM dfo_com_altas 
                ORDER BY id DESC 
                LIMIT 20
            """
            
            cursor.execute(query)
            records = cursor.fetchall()
            
            if not records:
                logger.info("⚠️ No se encontraron registros en dfo_com_altas.")
                return

            logger.info(f"\n📋 Últimos {len(records)} registros encontrados:")
            logger.info("-" * 80)
            logger.info(f"{'ID':<10} | {'Personnel #':<15} | {'Created Date':<20} | {'ETag (parcial)'}")
            logger.info("-" * 80)
            
            for row in records:
                etag_short = (row['etag'][:30] + '...') if row['etag'] and len(row['etag']) > 30 else row['etag']
                logger.info(f"{row['id']:<10} | {str(row['personnel_number']):<15} | {str(row['created_date']):<20} | {etag_short}")
            
            logger.info("-" * 80)
            
    except Error as e:
        logger.error(f"❌ Error conectando a MySQL: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    list_dfo_altas()
