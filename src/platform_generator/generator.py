
from cdk8s import App, Chart
from .runtime import Worker, Api
from .loader import load_retailers
import os

def get(name):
    for retailer in load_retailers():
        for service in retailer.services:
            for component in service.components:
                if component.name == name:
                    return component

class Scratch(Chart):
    def __init__(self, scope, id):
        super().__init__(scope, id)
        Api(self, "http", component=get("http"))
        Worker(self, "worker", component=get("worker"))

app = App()

chart = Scratch(app, "scratch")

app.synth()