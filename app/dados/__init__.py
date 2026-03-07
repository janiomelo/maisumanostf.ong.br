from .base import db, inicializar_camada_de_dados, migrate
from .modelos import WikiPagina

__all__ = ["db", "migrate", "inicializar_camada_de_dados", "WikiPagina"]
