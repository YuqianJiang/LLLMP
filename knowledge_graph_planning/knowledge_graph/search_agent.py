from typing import Optional
from pathlib import Path
import os
import json
import time
from openai import OpenAI
import networkx as nx
import numpy as np
import copy
from pydantic import BaseModel
from contextlib import redirect_stdout

from knowledge_representation import get_default_ltmc # type: ignore
from knowledge_representation.knowledge_loader import load_knowledge_from_yaml, populate_with_knowledge

from knowledge_graph_planning.knowledge_graph.age_graph import AgeGraph
from knowledge_graph_planning.knowledge_graph.agent import KGAgent
from knowledge_graph_planning.knowledge_graph.utils import reset_database
from knowledge_graph_planning.knowledge_graph.load_graph import load_graph
from knowledge_graph_planning.knowledge_graph.schema import select_schema, update_schema
from knowledge_graph_planning.pddl_parser.PDDL import PDDL_Parser, Action

# from pydantic.types import PositiveInt
from typing import Union, Literal
class EntityExtraction(BaseModel):
    entities: list[str]

class Object(BaseModel):
    id: int
    description: str
    candidates: list[str]
    multi_match: bool

class BooleanRelationship(BaseModel):
    object: int
    relation: Literal['phone_ringing', 'window_open', 'tv_on', 'light_on', 'faucet_on', 'dish_is_clean',
                      'cloth_is_clean', 'cloth_is_dry', 'glass_empty', 'head_by_robot']
    value: bool

class BinaryRelationship(BaseModel):
    subject: int
    relation: Literal['in_hand', 'room_has', 'placed_at_table', 'placed_at_washer', 'placed_at_laundrybasket',
                      'tv_playing_channel', 'placed_at_fridge', 'placed_at_dryer', 'placed_at_shelf', 'shelf_has_level',
                      'on_shelf_level', 'placed_at_kitchensink', 'glass_has_liquid']
    object: int

class Update(BaseModel):
    objects: list[Object]
    conditions: list[Union[BooleanRelationship, BinaryRelationship]]
    effects: list[Union[BooleanRelationship, BinaryRelationship]]

class KGSearchAgent(KGAgent):

    def __init__(self, log_dir: str) -> None:
        self.log_dir = log_dir
        self.dbname = "knowledge_base"
        self.dbuser = "postgres"
        self.dbpass = "password"
        self.dbhost = "localhost"
        self.dbport = 5432
        self.dbschema = os.path.join(os.path.dirname(__file__), "schema_postgresql.sql")
        self.graph_name = "knowledge_graph"
        self.time = 0

        openai_keys_file = os.path.join(os.path.dirname(__file__), "../../keys/openai_keys.txt")
        with open(openai_keys_file, "r") as f:
            keys = f.read()
        keys = keys.strip().split('\n')
        prompts_dir = os.path.join(os.path.dirname(__file__), "prompts/")
        self.llm = OpenAI(api_key=keys[0])
        with open(os.path.join(prompts_dir, "search_select_system.txt"), "r") as f:
            self.select_prompt = f.read()
        with open(os.path.join(prompts_dir, "search_multi_select_system.txt"), "r") as f:
            self.multi_select_system_prompt = f.read()
        with open(os.path.join(prompts_dir, "search_multi_select_user.txt"), "r") as f:
            self.multi_select_user_prompt = f.read()
        with open(os.path.join(prompts_dir, "search_update_system.txt"), "r") as f:
            self.update_system_prompt = f.read()
        with open(os.path.join(prompts_dir, "search_update_user.txt"), "r") as f:
            self.update_user_prompt = f.read()
        with open(os.path.join(prompts_dir, "search_goal_system.txt"), "r") as f:
            self.goal_system_prompt = f.read()
        with open(os.path.join(prompts_dir, "search_goal_user.txt"), "r") as f:
            self.goal_user_prompt = f.read()

    def input_initial_state(self, initial_state: str, knowledge_path: str, predicate_names: list[str],
                            domain_path: str) -> None:
        reset_database(
            dbname=self.dbname,
            user=self.dbuser,
            password=self.dbpass,
            host=self.dbhost,
            port=self.dbport,
            schema_file=self.dbschema
        )
        all_knowledge = [load_knowledge_from_yaml(knowledge_path)]
        populate_with_knowledge(get_default_ltmc(), all_knowledge)

        self.graph_store = AgeGraph(
            dbname=self.dbname,
            user=self.dbuser,
            password=self.dbpass,
            host=self.dbhost,
            port=self.dbport,
            graph_name=self.graph_name,
            node_label="entity"
        )
        load_graph(self.graph_store, self.graph_name)

        cur = self.graph_store.cursor()

        # get all the entity_names (used for entity selection)
        entity_names_query = """SELECT attribute_value "name" FROM entities
        			JOIN entity_attributes_str ON entities.entity_id = entity_attributes_str.entity_id
        			WHERE attribute_name = 'name';
        		"""
        cur.execute(entity_names_query)
        entity_list = [row[0] for row in cur.fetchall()]

        instance_of_query = ("SELECT * from instance_of")
        cur.execute(instance_of_query)
        self.entity_types = {self.graph_store.id_to_name[row[0]]: row[1] for row in cur.fetchall() if
                             row[0] in self.graph_store.id_to_name}
        self.entity_list = list(self.entity_types.keys())
        cur.close()
        entity_names = ", ".join(entity_list)

        pddl_parser = PDDL_Parser()
        pddl_parser.parse_domain(domain_path)
        self.pddl_actions: dict[str, Action] = {}
        for action in pddl_parser.actions:
            self.pddl_actions[action.name] = action

        self.pddl_supertypes: dict[str, list[str]] = {}
        for supertype in pddl_parser.types:
            if supertype not in self.pddl_supertypes:
                self.pddl_supertypes[supertype] = [supertype]
            for type in pddl_parser.types[supertype]:
                if type not in self.pddl_supertypes:
                    self.pddl_supertypes[type] = [type]
                self.pddl_supertypes[type] += self.pddl_supertypes[supertype]

        self.pddl_predicates = pddl_parser.predicates
        for pred in self.pddl_predicates:
            args = self.pddl_predicates[pred]
            for arg in args:
                if isinstance(args[arg], str):
                    args[arg] = [args[arg]]
                else:
                    args[arg].remove("either")

        self.entities_by_type: dict[str, list[str]] = {}
        for entity, entity_type in self.entity_types.items():
            for supertype in self.pddl_supertypes[entity_type]:
                if supertype not in self.entities_by_type:
                    self.entities_by_type[supertype] = []
                self.entities_by_type[supertype].append(entity)

        self.domain_path = domain_path

    def input_state_change(self, state_change: str) -> None:
        start_time = time.time()
        self.entity_types = self.graph_store.get_all_entities()
        self.all_entities = list(self.entity_types.keys())
        log_file = self.log_dir + f"/{self.time:04d}_state_change.log"
        # output the results
        with open(log_file, "w") as f:
            f.write("------------------------------------------------\n")
            f.write(f"STATE CHANGE: {state_change}\n")
            with redirect_stdout(f):
                # select_schema_with_objects = copy.deepcopy(select_schema)
                # select_schema_with_objects["schema"]["properties"]["objects"]["items"]["properties"]["candidates"][
                #     "description"] = "Select likely matches from " + ", ".join(self.all_entities)
                system_prompt = self.select_prompt.format(entity_names=", ".join(self.all_entities))
                structured_query = self.parse(system_prompt, state_change, select_schema)
                # TODO: match object type
                query_g = self.build_query_graph(structured_query['entities'], structured_query['relationships'])
                mapping = self.subgraph_matching(state_change, structured_query['entities'], query_g)
            f.write(f"MAPPING: {mapping}\n")
            selected_entities = []
            for mapped_list in list(mapping.values()):
                selected_entities.extend(mapped_list)
            relations = self.graph_store.get_rel_map(selected_entities, depth=1, limit=200)
            context = ""
            for triplet_list in list(relations.values()):
                for triplet in triplet_list:
                    context += triplet + "\n"
            f.write(f"CONTEXT: {context}\n")
            update_user_prompt = self.update_user_prompt.format(text=state_change, context=context)
            with redirect_stdout(f):
                updates = self.parse(self.update_system_prompt, update_user_prompt, update_schema)

            for effect in updates['relationships']:
                predicate = effect['predicate']
                subj = effect['subject']
                obj = effect['object']
                action = effect['action']

                if isinstance(obj, bool):
                    obj = str(obj).lower()

                if action == "delete":
                    # TODO: check relation exists
                    self.graph_store.delete(subj, predicate, obj)
                elif action == "add":
                    self.graph_store.upsert_triplet(subj, predicate, obj)
                elif action == "update":
                    self.graph_store.delete_rel_with_subj(subj, predicate)
                    self.graph_store.upsert_triplet(subj, predicate, obj)

            f.write(f"Total time to process the update: {time.time() - start_time}")

        self.time += 1

    def answer_planning_query(self, query: str) -> list[str]:
        start_time = time.time()
        self.entity_types = self.graph_store.get_all_entities()
        self.all_entities = list(self.entity_types.keys())

        log_file = self.log_dir + f"/{self.time:04d}_plan_query"
        with open(log_file + ".context.log", "w") as f:
            f.write(f"TASK: {query}\n")
            with redirect_stdout(f):
                system_prompt = self.select_prompt.format(entity_names=", ".join(self.all_entities))
                structured_query = self.parse(system_prompt, query, select_schema)
                # TODO: match object type
                query_g = self.build_query_graph(structured_query['entities'], structured_query['relationships'])
                mapping = self.subgraph_matching(query, structured_query['entities'], query_g)
            f.write(f"MAPPING: {mapping}\n")

        nodes = ['the_agent']
        for matches in list(mapping.values()):
            nodes.extend(matches)
        relations = self.graph_store.get_rel_map(nodes, depth=2, limit=200)

        objects = set()
        init_block = "\t(:init\n"
        for node in relations:
            for rel in relations[node]:
                predicate = rel.split('-[')[1].split(']')[0]
                arg1 = rel.split(',')[0]
                arg2 = rel.split('->, ')[1]
                if arg2 == 'true':
                    init_block += f"\t\t({predicate} {arg1})\n"
                    objects.add(arg1)
                elif arg2 == 'false':
                    continue
                else:
                    init_block += f"\t\t({predicate} {arg1} {arg2})\n"
                    objects.add(arg1)
                    objects.add(arg2)

        init_block += "\t)\n"
        objects_block = "\t(:objects\n"
        for obj in objects:
            obj_type = self.graph_store.get_type(obj)
            objects_block += f"\t\t{obj} - {obj_type}\n"
        objects_block += "\t)\n"

        goal_user_prompt = self.goal_user_prompt.format(text=query, context=objects_block + init_block)
        completion = self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": self.goal_system_prompt},
                {"role": "user", "content": goal_user_prompt}
            ],
            temperature=0
        )
        goal_block = completion.choices[0].message.content

        '''
        goal_block = "\t(:goal\n \t\t(and\n"
        for goal in structured_query['goals']:
            predicate = goal['predicate']
            for subject in mapping[goal['subject']]:
                value = list(goal.values())[2]
                if isinstance(value, bool):
                    if value:
                        goal_block += f"\t\t\t({predicate} {subject})\\n"
                    else:
                        goal_block += f"\t\t\t(not ({predicate} {subject}))\n"
                elif isinstance(value, int):
                    for obj in mapping[value]:
                        goal_block += f"\t\t\t({predicate} {subject} {obj})\n"
                else:
                    goal_block += f"\t\t\t({predicate} {subject} {value})\n"

        goal_block += "\t\t)\n\t)\n"
        '''

        task_pddl_ = f"(define (problem p{self.time})\n" + \
                     f"\t(:domain simulation)\n" + \
                     objects_block + \
                     init_block + \
                     f"{goal_block}\n)"

        # B. write the problem file into the problem folder
        task_pddl_file_name = os.path.join(self.log_dir, f"{self.time:04d}_problem.pddl")
        with open(task_pddl_file_name, "w") as f:
            f.write(task_pddl_)
        time.sleep(1)

        # C. run lapkt to plan
        plan_file_name = self.log_dir + f"/{self.time:04d}_plan.pddl"

        project_dir = Path(__file__).parent.parent.parent.as_posix()
        os.system(f"docker run --rm -v {project_dir}:/root/experiments lapkt/lapkt-public ./siw-then-bfsf " + \
                  f"--domain /root/experiments/{self.domain_path} " + \
                  f"--problem /root/experiments/{task_pddl_file_name} " + \
                  f"--output /root/experiments/{plan_file_name} " + \
                  f"> {log_file}.pddl.log")

        with open(log_file + ".log", "w") as f:
            f.write(f"Total time to generate the plan: {time.time() - start_time}")

        self.time += 1
        return plan_file_name

    def parse(self, system, user, schema):
        start_time = time.time()
        completion = self.llm.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_schema", "json_schema": schema},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            temperature=0
        )
        parse_result = json.loads(completion.choices[0].message.content)
        print("------------------------------------------------")
        print(json.dumps(parse_result, indent=2))
        print("Time: ", time.time() - start_time)
        return parse_result

    def multi_match_llm(self, text, description, current_mapping, indices):
        start_time = time.time()
        entity_names = "[" + ", ".join(self.all_entities) + "]"
        reference_entities = [self.all_entities[i] for i in indices]
        for mapped_list in list(current_mapping.values()):
            reference_entities.extend(mapped_list)
        relations = self.graph_store.get_rel_map(reference_entities, depth=1, limit=200)
        context = ""
        for triplet_list in list(relations.values()):
            for triplet in triplet_list:
                context += triplet + "\n"
        user_prompt = self.multi_select_user_prompt.format(text=text,
                                                           description=description,
                                                           entity_names=entity_names,
                                                           context=context)

        completion = self.llm.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": self.multi_select_system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
            response_format=EntityExtraction
        )
        print("------------------------------------------------")
        print(user_prompt)
        parse_result = completion.choices[0].message.parsed.entities
        print("SELECTED ENTITIES: " + ", ".join(parse_result))
        print("Time: ", time.time() - start_time)
        return parse_result

    def subgraph_matching(self, text, query_nodes, query_g):
        # M = np.ones((n, m), dtype=float)
        target_g_embeddings = np.array([self.graph_store.model.encode(v, show_progress_bar=False) for v in self.all_entities])
        query_g_embeddings = np.array([self.graph_store.model.encode(v['description'], show_progress_bar=False) for v in query_nodes])
        # print (target_g_embeddings.shape, query_g_embeddings.shape)
        dot_product = np.dot(query_g_embeddings, target_g_embeddings.T)

        # Calculate the magnitude of each row vector in both matrices
        norm_query = np.linalg.norm(query_g_embeddings, axis=1)[:, np.newaxis]
        norm_target = np.linalg.norm(target_g_embeddings, axis=1)[np.newaxis, :]

        # Compute cosine similarity for each pair of rows
        M = dot_product / (norm_query * norm_target)
        # M = np.dot(query_g_embeddings, target_g_embeddings.T)
        # print(M.shape)
        query_node_order = np.argsort(-np.max(M, axis=1))
        query_q = []
        for node_idx in query_node_order:
            if query_nodes[node_idx]['multi_match']:
                query_q.append(node_idx)
        for node_idx in query_node_order:
            if not query_nodes[node_idx]['multi_match']:
                query_q.append(node_idx)
        best_mapping_score = -np.inf
        best_mapping = None
        best_mapping_score, best_mapping = self.backtrack(text, query_nodes, query_g, M, query_q, {},
                                                          best_mapping_score, best_mapping, cutoff_ratio=0.9)
        return best_mapping

    def mapping_score(self, query_g, current_mapping):
        score = 0.0
        for query_v in current_mapping.keys():
            target_v = current_mapping[query_v][0]
            for query_u in query_g.successors(query_v):
                query_r = query_g.get_edge_data(query_v, query_u)['predicate']
                query_r_emb = self.graph_store.model.encode(query_r, show_progress_bar=False)

                if query_u in current_mapping.keys():
                    target_u = current_mapping[query_u][0]

                    # if an edge exists in the target graph, score is the similarity
                    # if the edge does not exist in the target graph, score is 0
                    edges = self.graph_store.get_edge(target_v, target_u)
                    max_similarity = 0
                    for target_r in edges:
                        similarity = np.dot(query_r_emb,
                                            self.graph_store.model.encode(target_r, show_progress_bar=False))
                        if similarity > max_similarity:
                            max_similarity = similarity

                    score += max_similarity
                else:
                    # score is node similarity of the most similar edge
                    edges = self.graph_store.get(target_v)
                    edge_similarities = [np.dot(query_r_emb, self.graph_store.model.encode(e, show_progress_bar=False)) for e, u in edges]
                    if len(edge_similarities) > 0:
                        target_e, target_u = edges[np.argmax(edge_similarities)]
                        score += np.dot(self.graph_store.model.encode(str(query_u), show_progress_bar=False),
                                        self.graph_store.model.encode(target_u, show_progress_bar=False))

        return score

    def backtrack(self, text, query_nodes, query_g, M, query_q, current_mapping, best_mapping_score, best_mapping,
                  cutoff_ratio=0.5):
        # m = len(query_nodes)
        n = len(self.all_entities)
        if len(query_q) == 0:
            score = self.mapping_score(query_g, current_mapping)
            if score > best_mapping_score or best_mapping is None:
                best_mapping = copy.deepcopy(current_mapping)
                best_mapping_score = score

            return best_mapping_score, best_mapping

        next_node_idx = query_q[0]
        next_node = query_nodes[next_node_idx]

        indices = np.argsort(-M[next_node_idx, :])
        cutoff = max(0.2, M[next_node_idx, indices[0]] * cutoff_ratio)
        above_cutoff_indices = [i for i in indices if M[next_node_idx, i] >= cutoff]
        candidate_indices = []

        if 'candidates' in next_node.keys() and len(next_node['candidates']) > 0:
            candidates = [i for i in range(n) if self.all_entities[i] in next_node['candidates']]
            candidate_indices = np.array(candidates)[np.argsort(-M[next_node_idx, candidates])]
        #     indices = list(candidate_indices)
        # else:
        #     indices = above_cutoff_indices
        indices = list(candidate_indices)
        indices.extend([i for i in above_cutoff_indices if i not in candidate_indices])

        if 'multi_match' in next_node.keys() and next_node['multi_match']:
            matched_indices = self.multi_match_llm(text, next_node['description'], current_mapping, indices)
            current_mapping[next_node['id']] = matched_indices
            best_mapping_score, best_mapping = self.backtrack(text, query_nodes, query_g, M, query_q[1:], current_mapping,
                                                              best_mapping_score, best_mapping, cutoff_ratio)
            current_mapping.pop(next_node['id'])
        else:
            for i in range(len(indices)):
                matched_node = indices[i]
                current_mapping[next_node['id']] = [self.all_entities[matched_node]]
                best_mapping_score, best_mapping = self.backtrack(text, query_nodes, query_g, M, query_q[1:], current_mapping,
                                                                  best_mapping_score, best_mapping, cutoff_ratio)
                current_mapping.pop(next_node['id'])

        return best_mapping_score, best_mapping

    @staticmethod
    def build_query_graph(nodes, edges):
        query_g = nx.DiGraph()

        for obj in nodes:
            query_g.add_node(obj['id'], type=obj['description'], candidates=obj['candidates'])

        for edge in edges:
            if len(edge.values()) < 3:
                continue
            obj = list(edge.values())[2]
            subj = list(edge.values())[0]
            if isinstance(obj, bool):
                obj = 'True' if obj else 'False'
            if not isinstance(obj, int):
                if obj not in query_g:
                    query_g.add_node(obj, type=obj)

            query_g.add_edge(subj, obj, predicate=edge['predicate'])

        return query_g

    def get_all_relations(self) -> list[str]:
        relations = self.graph_store.query("MATCH (V)-[R]->(V2) RETURN V.name, type(R), V2.name", return_count=3)
        return [" -> ".join(item[1:-1] for item in row) for row in relations if all(isinstance(s, str) for s in row)]

    def close(self) -> None:
        self.graph_store._conn.close()
