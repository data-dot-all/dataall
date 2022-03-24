from diagrams import Cluster, Diagram
from diagrams.onprem.network import Nginx
from diagrams.onprem.compute import Server
from diagrams.onprem.client import Client
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.queue import Celery


with Diagram('Network Settings', show=False, filename='../assets/simplified'):
    app = Server('App')
    bg = Celery('Background Worker')
    state = PostgreSQL('Shared State')
    Client('Web App ') >> Nginx('WebServer') >> app
    app >> bg
    app >> state
    bg >> state
