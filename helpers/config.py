import os
import yaml


def loadConfig():
    with open('config.yaml', 'r') as yamlFile:
        config = yaml.safe_load(yamlFile)
        for section in config:
            sectionDict = config[section]
            for key, value in sectionDict.items():
                os.environ[key] = value
