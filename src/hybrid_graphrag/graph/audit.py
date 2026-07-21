import json
import os
from datetime import datetime
from ..logging import logger
from .neo4j_client import Neo4jClient

class GraphAuditor:
    def __init__(self, client: Neo4jClient, manifest_dir: str = "data/manifests"):
        self.client = client
        self.manifest_dir = manifest_dir
        os.makedirs(self.manifest_dir, exist_ok=True)

    def count_nodes(self) -> dict:
        query = """
        MATCH (n)
        RETURN labels(n)[0] as label, count(n) as count
        """
        results = self.client.execute_read(query)
        return {r["label"]: r["count"] for r in results if r["label"]}

    def count_edges(self) -> dict:
        query = """
        MATCH ()-[r]->()
        RETURN type(r) as rel_type, count(r) as count
        """
        results = self.client.execute_read(query)
        return {r["rel_type"]: r["count"] for r in results if r["rel_type"]}

    def check_missing_endpoints(self) -> int:
        
        query = """
        MATCH (n)
        WHERE NOT (n)--()
        RETURN count(n) as count
        """
        result = self.client.execute_read(query)
        return result[0]["count"] if result else 0

    def run_audit(self):
        logger.info("Running post-load graph audit...")
        
        nodes = self.count_nodes()
        edges = self.count_edges()
        dangling = self.check_missing_endpoints()
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "nodes": nodes,
            "edges": edges,
            "dangling_nodes_count": dangling,
            "total_nodes": sum(nodes.values()),
            "total_edges": sum(edges.values())
        }
        
        logger.info(f"Audit Results - Total Nodes: {report['total_nodes']}, Total Edges: {report['total_edges']}")
        
        manifest_path = os.path.join(self.manifest_dir, f"graph_load_{int(datetime.utcnow().timestamp())}.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"Audit manifest saved to {manifest_path}")
        return report
