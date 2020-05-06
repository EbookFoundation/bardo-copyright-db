import os
import yaml
from flask import Flask, jsonify
from flasgger import Swagger
from prints.swagger.swag import SwaggerDoc
from db import db
from elastic import elastic
from prints import base, search, uuid

def loadConfig():
    with open('config.yaml-dist', 'r') as yamlFile:
        config = yaml.safe_load(yamlFile)
        for section in config:
            sectionDict = config[section]
            for key, value in sectionDict.items():
                os.environ[key] = value

try:
    loadConfig()
except FileNotFoundError:
    pass

application = Flask(__name__)
application.register_blueprint(base.bp)
application.register_blueprint(search.search)
application.register_blueprint(uuid.uuid)
application.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://{}:{}@{}:{}/{}'.format(
    os.environ['DB_USER'],
    os.environ['DB_PSWD'],
    os.environ['DB_HOST'],
    os.environ['DB_PORT'],
    os.environ['DB_NAME']
)
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

application.config['ELASTICSEARCH_INDEX_URI'] = '{}:{}'.format(
    os.environ['ES_HOST'],
    os.environ['ES_PORT']
)
# print(application.config['ELASTICSEARCH_INDEX_URI'])
application.config['SWAGGER'] = {'title': 'CCE Search'}
db.init_app(application)
elastic.init_app(application)
docs = SwaggerDoc()
swagger = Swagger(application, template=docs.getDocs())
