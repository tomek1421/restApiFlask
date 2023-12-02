from flask import Blueprint, jsonify, g, request

from utils.department_utils import department_by_id_exist
from utils.employee_utils import get_employee_by_name_exists

department_blueprint = Blueprint('department', __name__)


@department_blueprint.route('/', methods=['GET'])
def get_departments_route():
    filter = request.args.get('filter')
    sort = request.args.get('sort')
    with g.driver.session() as session:
        return jsonify(session.read_transaction(get_departments, filter, sort))


def get_departments(tx, filter, sort):
    query = "MATCH (n :Department) "

    if filter is not None:
        query += f"WHERE n.name = \"{filter}\" "

    query += "RETURN n.name "

    if sort is not None:
        query += f"ORDER BY n.{sort} "

    results = tx.run(query).data()
    return [department['n.name'] for department in results]


@department_blueprint.route('/<int:id>/employees', methods=['GET'])
def get_department_employees_route(id):
    with g.driver.session() as session:
        if id is None:
            return jsonify({'error': 'Id not given'}), 400
        if not session.read_transaction(department_by_id_exist, id):
            return jsonify({'error': 'Department not found'}), 404

        return jsonify(session.read_transaction(get_department_employees, id))


def get_department_employees(tx, id):
    query = f"MATCH (n :Department)-[:WORKS_IN]-(m :Employee) WHERE id(n) = {id} RETURN m.name"

    results = tx.run(query).data()
    return [employee['m.name'] for employee in results]


@department_blueprint.route('/<string:name>', methods=['GET'])
def get_department_details_route(name):
    with g.driver.session() as session:
        if not session.read_transaction(get_employee_by_name_exists, name):
            return jsonify({"error": "Employee not found"}), 404

        return jsonify(session.read_transaction(get_department_details, name))


def get_department_details(tx, name):
    query = f"MATCH (n :Employee)-[]-(m : Department) WHERE n.name = \"{name}\" RETURN m.name"
    result = tx.run(query).data()

    if len(result) == 0:
        return {}

    department_name = result[0]['m.name']
    query = f"MATCH (n :Department)-[]-(m :Employee) WHERE n.name = \"{department_name}\" RETURN m.name"

    results = tx.run(query).data()
    employees = [employee['m.name'] for employee in results]

    query = f"MATCH (n :Department)-[:MANAGES]-(m :Employee) WHERE n.name = \"{department_name}\" RETURN m.name"

    result = tx.run(query).data()

    if len(result) == 0:
        return {
            "name": department_name,
            "employees": len(employees),
            "manager": ''
        }
    else:
        return {
            "name": department_name,
            "employees": len(employees),
            "manager": result[0]['m.name']
        }
