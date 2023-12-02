def department_by_id_exist(tx, id):
    query = f"MATCH (n: Department) WHERE id(n) = {id} RETURN n"
    result = tx.run(query).data()
    return len(result) > 0