from flask import Flask, g
from neo4j import GraphDatabase

from routes.department_routes import department_blueprint
from routes.employee_routes import employees_blueprint

app = Flask(__name__)

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "test1234"), database="neo4j")

app.register_blueprint(employees_blueprint, url_prefix='/employees')
app.register_blueprint(department_blueprint, url_prefix='/departments')


@app.before_request
def before_request():
    g.driver = driver


if __name__ == '__main__':
    app.run()
