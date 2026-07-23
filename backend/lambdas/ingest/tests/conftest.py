import os
import sys

# bedrock.py no es un paquete instalable, asi que se agrega su carpeta al path
# para poder importarlo directo desde los tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
