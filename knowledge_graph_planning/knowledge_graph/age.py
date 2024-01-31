from typing import Any, Dict, List, Optional
from llama_index.graph_stores.types import GraphStore

try:
    import psycopg2
except ImportError:
    raise ImportError("Please install psycopg2")

class AgeGraphStore(GraphStore): # type: ignore
    def __init__(
        self,
        dbname: str,
        user: str,
        password: str,
        host: str,
        port: int,
        graph_name: str,
        node_label: str,
        **kwargs: Any,
    ) -> None:
        try:
            self._conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
            self._conn.autocommit = True
            cur = self._conn.cursor()
            cur.execute(f"LOAD 'age'")
            cur.execute(f"SET search_path = ag_catalog, '$user', public;")
        except psycopg2.OperationalError as err:
            raise ValueError(err)
        self._dbname = dbname
        self._graph_name = graph_name
        self._node_label = node_label

    def cursor(self):
        return self._conn.cursor()

    def get(self, subj: str) -> List[List[str]]:
        """Get triplets."""
        query = (
                    f"SELECT * FROM ag_catalog.cypher('{self._graph_name}', $$ "
                    f"MATCH (:{self._node_label} {{name:'{subj}'}})-[r]->(n2:{self._node_label})"
                    f"RETURN type(r), n2.name"
                    f"$$) as (rel agtype, obj agtype);"
        )
        cur = self.cursor()
        cur.execute(query)
        results = cur.fetchall()
        return [[eval(rel), eval(obj)] for (rel, obj) in results]

    def get_rel_map(
            self, subjs: Optional[List[str]] = None, depth: int = 2, limit: int=30
    ) -> Dict[str, List[List[str]]]:
        """Get flat rel map."""

        rel_map: Dict[Any, List[Any]] = {}
        if subjs is None or len(subjs) == 0:
            # unlike simple graph_store, we don't do get_all here
            return rel_map

        for subj in subjs:
            rel_map[subj] = []

        subjs_str = '["' + '", "'.join(subjs) + '"]'

        for i in range(depth):
            path = f"-[]-(:{self._node_label})" * i

            query = (f"SELECT * FROM ag_catalog.cypher('{self._graph_name}', $$ "
                     f"MATCH p=(n1:{self._node_label}){path}-[]-() "
                     f"WHERE n1.name IN {subjs_str} "
                     f"WITH n1.name AS subj, p, relationships(p) AS rels "
                     f"UNWIND rels AS rel "
                     f"WITH subj AS subj, p, collect([startNode(rel).name, type(rel), endNode(rel).name]) AS predicates "
                     f"RETURN subj, predicates LIMIT {limit}"
                     f"$$) as (subj agtype, rel agtype);"
                     )
            cur = self.cursor()
            try:
                cur.execute(query)
            except psycopg2.errors.SyntaxError as err:
                print(err)
                print(query)
                print(subjs_str)
            results = cur.fetchall()
            for row in results:
                for rel in eval(row[1]):
                    rel_str = "" + rel[0] + ", -[" + rel[1] + "], " + "-> " + rel[2] + ""
                    if rel_str not in rel_map[eval(row[0])]:
                        rel_map[eval(row[0])].append(rel_str)

        return rel_map

    def upsert_triplet(self, subj: str, rel: str, obj: str) -> None:
        """Add triplet."""
        cur = self.cursor()
        cur.execute(
            f"SELECT * FROM cypher('{self._graph_name}', "
            f"$$MERGE (u {{name: '{subj}'}})"
            f"MERGE (v {{name: '{obj}'}}) "
            f"MERGE (u)-[e:{rel}]->(v) $$) as (e agtype);")

    def upsert_triplet_entity(self, subj: str, rel: str, obj: str) -> None:
        """Add triplet with entity value."""
        cur = self.cursor()
        cur.execute(
            f"SELECT * FROM cypher('{self._graph_name}', "
            f"$$MERGE (a:entity {{id: '{subj}' }}) "
            f"RETURN a $$) as (a agtype);")
        cur.execute(
            f"SELECT * FROM cypher('{self._graph_name}', "
            f"$$MERGE (a:entity {{id: '{obj}' }}) "
            f"RETURN a $$) as (a agtype);")
        cur.execute(
            f"SELECT * FROM cypher('{self._graph_name}', $$MATCH (u:entity {{id: '{subj}'}}), "
            f"(v:entity {{id: '{obj}'}}) CREATE (u)-[e:{rel}]->(v) RETURN e$$) as (e agtype);")

    def upsert_triplet_bool(self, subj: str, rel: str, obj: str) -> None:
        """Add triplet with bool value."""
        cur = self.cursor()
        cur.execute(
            f"SELECT * FROM cypher('{self._graph_name}', "
            f"$$MERGE (a:bool {{name: '{obj}' }}) "
            f"RETURN a $$) as (a agtype);")
        cur.execute(
            f"SELECT * FROM cypher('{self._graph_name}', $$MATCH (u:entity {{id: '{subj}'}}), "
            f"(v:bool {{name: '{obj}'}}) CREATE (u)-[e:{rel}]->(v) RETURN e$$) as (e agtype);")

    def upsert_triplet_float(self, subj: str, rel: str, obj: str) -> None:
        """Add triplet with float value."""
        cur = self.cursor()
        cur.execute(
            f"SELECT * FROM cypher('{self._graph_name}', "
            f"$$MERGE (a:float {{name: '{obj}' }}) "
            f"RETURN a $$) as (a agtype);")
        cur.execute(
            f"SELECT * FROM cypher('{self._graph_name}', $$MATCH (u:entity {{id: '{subj}'}}), "
            f"(v:float {{name: '{obj}'}}) CREATE (u)-[e:{rel}]->(v) RETURN e$$) as (e agtype);")
    
    def upsert_triplet_int(self, subj: str, rel: str, obj: str) -> None:
        """Add triplet with int value."""
        cur = self.cursor()
        cur.execute(
            f"SELECT * FROM cypher('{self._graph_name}', "
            f"$$MERGE (a:int {{name: '{obj}' }}) "
            f"RETURN a $$) as (a agtype);")
        cur.execute(
            f"SELECT * FROM cypher('{self._graph_name}', $$MATCH (u:entity {{id: '{subj}'}}), "
            f"(v:int {{name: '{obj}'}}) CREATE (u)-[e:{rel}]->(v) RETURN e$$) as (e agtype);")

    def upsert_triplet_str(self, subj: str, rel: str, obj: str) -> None:
        """Add triplet with string value."""
        cur = self.cursor()
        cur.execute(
            f"SELECT * FROM cypher('{self._graph_name}', "
            f"$$MERGE (a:str {{name: '{obj}' }}) "
            f"RETURN a $$) as (a agtype);")
        cur.execute(
            f"SELECT * FROM cypher('{self._graph_name}', $$MATCH (u:entity {{id: '{subj}'}}), "
            f"(v:str {{name: '{obj}'}}) CREATE (u)-[e:{rel}]->(v) RETURN e$$) as (e agtype);")

    def delete(self, subj: str, rel: str, obj: str) -> None:
        """Delete triplet."""
        cur = self.cursor()

        def check_edges(entity: str) -> bool:
            cur.execute(
                f"SELECT * FROM cypher('{self._graph_name}', "
                f"$$MATCH (u {{name: '{entity}'}})-[]-(v) "
                f"RETURN v $$) as (v agtype);")
            results = cur.fetchall()
            return bool(len(results))

        def delete_entity(entity: str) -> None:
            cur.execute(
                f"SELECT * FROM cypher('{self._graph_name}', "
                f"$$MATCH (u {{name: '{entity}'}}) DELETE u$$) as (u agtype);")

        def delete_rel(subj: str, obj: str, rel: str) -> None:
            cur.execute(
                f"SELECT * FROM cypher('{self._graph_name}', "
                f"$$MATCH (u {{name: '{subj}'}})-[e:{rel}]->(v {{name: '{obj}'}}) DELETE e$$) as (e agtype);")

        delete_rel(subj, obj, rel)
        if not check_edges(subj):
            delete_entity(subj)
        if not check_edges(obj):
            delete_entity(obj)

    def delete_rel_with_subj(self, subj: str, rel: str) -> None:
        """Delete triplet with subj and rel."""
        cur = self.cursor()
        cur.execute(
            f"SELECT * FROM cypher('{self._graph_name}', "
            f"$$MATCH (u:entity {{name: '{subj}'}})-[e:{rel}]->() DELETE e$$) as (e agtype);")

    def delete_rel_with_obj(self, rel: str, obj: str) -> None:
        """Delete triplet with obj and rel."""
        cur = self.cursor()
        cur.execute(
            f"SELECT * FROM cypher('{self._graph_name}', "
            f"$$MATCH (u)-[e:{rel}]->(v:entity {{name: '{obj}'}}) DELETE e$$) as (e agtype);")

    def query(self, query: str, param_map: Optional[Dict[str, Any]] = {}) -> Any:
        cur = self.cursor()
        query = query.format(param_map)
        cur.execute(
            f"SELECT * FROM cypher('{self._graph_name}', "
            f"$${query}$$) as (a agtype);")
        results = cur.fetchall()
        return results
