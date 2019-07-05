import os
import yaml
from flask import Flask, jsonify
from flasgger import Swagger
from api.prints.swagger.swag import SwaggerDoc
from api.db import db
from api.elastic import elastic
from api.prints import base, search, uuid

def loadConfig():
    with open('config.yaml', 'r') as yamlFile:
        config = yaml.safe_load(yamlFile)
        for section in config:
            sectionDict = config[section]
            for key, value in sectionDict.items():
                os.environ[key] = value

def create_app():
    loadConfig()
    
    app = Flask(__name__)
    app.register_blueprint(base.bp)
    app.register_blueprint(search.search)
    app.register_blueprint(uuid.uuid)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://{}:{}@{}:{}/{}'.format(
        os.environ['DB_USER'],
        os.environ['DB_PSWD'],
        os.environ['DB_HOST'],
        os.environ['DB_PORT'],
        os.environ['DB_NAME']
    )
    app.config['ELASTICSEARCH_INDEX_URI'] = '{}:{}'.format(
        os.environ['ES_HOST'],
        os.environ['ES_PORT']
    )
    app.config['SWAGGER'] = {'title': 'CCE Search'}
    db.init_app(app)
    elastic.init_app(app)
    docs = SwaggerDoc()
    swagger = Swagger(app, template=docs.getDocs())
    return app


if __name__ == '__main__':
    create_app()