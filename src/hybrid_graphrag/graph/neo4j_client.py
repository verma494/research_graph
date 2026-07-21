import os
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, TransientError
from typing import List, Dict, Any, Optional
import time

from ..logging import logger
from ..config import settings

class Neo4jClient:
    def __init__(self):
        self.uri = settings.neo4j_uri
        username = settings.neo4j_username
        password = settings.neo4j_password
        
        self.driver = GraphDatabase.driver(self.uri, auth=(username, password))
        
    def close(self):
        self.driver.close()
        
    def check_health(self) -> bool:
        try:
            self.driver.verify_connectivity()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            return False

    def execute_write(self, query: str, parameters: Optional[Dict[str, Any]] = None, max_retries: int = 3):
        parameters = parameters or {}
        retries = 0
        while retries < max_retries:
            try:
                with self.driver.session() as session:
                    result = session.execute_write(self._run_query, query, parameters)
                    return result
            except (ServiceUnavailable, TransientError) as e:
                retries += 1
                logger.warning(f"Transient error executing query, retrying ({retries}/{max_retries}): {e}")
                time.sleep(2 ** retries)
            except Exception as e:
                logger.error(f"Error executing write query: {e}\nQuery: {query}\nParams: {parameters}")
                raise e
        raise Exception(f"Failed to execute query after {max_retries} retries.")

    def execute_read(self, query: str, parameters: Optional[Dict[str, Any]] = None):
        parameters = parameters or {}
        try:
            with self.driver.session() as session:
                result = session.execute_read(self._run_query, query, parameters)
                return result
        except Exception as e:
            logger.error(f"Error executing read query: {e}")
            raise e

    @staticmethod
    def _run_query(tx, query, parameters):
        result = tx.run(query, parameters)
        return [record.data() for record in result]
