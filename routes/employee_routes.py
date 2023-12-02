from flask import Blueprint, jsonify, g, request

from utils.employee_utils import get_employee_by_name_exists, get_employee_by_name_and_id_exists, \
    is_employee_manager, employee_by_id_exist

employees_blueprint = Blueprint('employees', __name__)


@employees_blueprint.route('/', methods=['GET'])
def get_employees_route():
    args = request.args
    name = args.get('filter')
    sort = args.get('sort')

    with g.driver.session() as session:
        employees = session.read_transaction(get_employees, name, sort)

    return jsonify(employees)


def get_employees(tx, name, sort):
    query = "MATCH (n:Employee) "

    if name is not None:
        query += f"WHERE n.name = \"{name}\" "

    query += "RETURN n"

    if sort is not None:
        query += f" ORDER BY n.{sort}"

    results = tx.run(query).data()
    employees = [{"name": result['n']['name']} for result in results]
    return employees


@employees_blueprint.route("/", methods=['POST'])
def post_employee_route():
    data = request.get_json()

    name = data.get('name')
    position = data.get('position')

    if name is None or position is None:
        return jsonify({"error": "Name or position not given"}), 400

    with g.driver.session() as session:
        if session.read_transaction(get_employee_by_name_exists, name):
            return jsonify({"error": "Name already exists"}), 400

        employee = session.write_transaction(post_employee, name, position)

    return jsonify(employee), 201


def post_employee(tx, name, position):
    query = f"CREATE (n :Employee {{name: \"{name}\", position: \"{position}\"}}) RETURN n"
    result = tx.run(query).data()
    return result[0]['n']


@employees_blueprint.route('/<int:id>', methods=['PUT'])
def put_employee_route(id):
    data = request.get_json()

    name = data.get('name')
    position = data.get('position')

    if name is None and position is None:
        return jsonify({"error": "Name or position not given"}), 400

    with g.driver.session() as session:
        if name is not None and session.read_transaction(get_employee_by_name_and_id_exists, name, id):
            return jsonify({"error": "Name already exists"}), 400

        employee = session.write_transaction(put_employee, id, name, position)
        return employee


def put_employee(tx, employee_id, name, position):
    query = f"MATCH (n: Employee) WHERE id(n) = {employee_id} SET "

    if name is not None:
        query += f"n.name = \"{name}\" "

    if position is not None:
        if name is None:
            query += f"n.position = \"{position}\""
        else:
            query += f", n.position = \"{position}\" "

    query += " RETURN n"
    result = tx.run(query).data()
    return result[0]['n']


@employees_blueprint.route('/<int:id>', methods=['DELETE'])
def delete_employee_route(id):
    with g.driver.session() as session:
        if not session.read_transaction(employee_by_id_exist, id):
            return jsonify({"error": "Employee not found"}), 404

        return jsonify(session.write_transaction(delete_employee_and_department, id)), 204


def delete_employee_and_department(tx, id):
    query = f"MATCH (n:Employee)-[r :MANAGES]-(m:Department)-[f]-() WHERE id(n) = {id} DELETE f"
    tx.run(query)
    query = f"MATCH (n:Employee)-[r :MANAGES]-(m:Department) WHERE id(n) = {id} DELETE r,m"
    tx.run(query)
    query = f"MATCH (n :Employee)-[r]-() WHERE id(n) = {id} DELETE r"
    tx.run(query)
    query = f"MATCH (n :Employee) WHERE id(n) = {id} DELETE n"
    tx.run(query)


@employees_blueprint.route('/<int:id>/subordinates', methods=['GET'])
def get_employee_subordinates_route(id):
    with g.driver.session() as session:
        if id is None:
            return jsonify({'error': 'Id not given'}), 400

        if not session.read_transaction(employee_by_id_exist, id):
            return jsonify({'error': 'User not found'}), 404
        if not session.read_transaction(is_employee_manager, id):
            return jsonify({'error': 'User is not a manager'}), 400
        return jsonify(session.read_transaction(get_employee_subordinates, id))


def get_employee_subordinates(tx, id):
    query = f"MATCH (n :Employee)-[:MANAGES]-(:Department)-[:WORKS_IN]-(m :Employee) WHERE id(n) = {id} RETURN m.name"

    results = tx.run(query).data()
    return [employee['m.name'] for employee in results]
