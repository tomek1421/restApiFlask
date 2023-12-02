def employee_by_id_exist(tx, id):
    query = f"MATCH (n: Employee) WHERE id(n) = {id} RETURN n"
    result = tx.run(query).data()
    return len(result) > 0

def get_employee_by_name_exists(tx, name):
    query = f"MATCH (n :Employee) WHERE n.name = \"{name}\" RETURN n"
    result = tx.run(query).data()
    return len(result) != 0


def get_employee_by_name_and_id_exists(tx, name, id):
    query = f"MATCH (n :Employee) WHERE n.name = \"{name}\" AND NOT id(n) = {id} RETURN n"
    result = tx.run(query).data()
    return len(result) != 0

def is_employee_manager(tx, id):
    query = f"MATCH (n: Employee)-[:MANAGES]-() WHERE id(n) = {id} RETURN n"
    return len(tx.run(query).data()) != 0
