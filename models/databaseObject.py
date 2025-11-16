
from datetime import datetime
from enum import Enum

class DatabaseObject:
    def __init__(self, tableName : str, **kwargs):
        self.__tableName = tableName
        self.__id = kwargs.get('id', None)
        kwargs.pop('id', None)
        for k in kwargs.keys(): ## setting row info as attributes of the instance
            exec(f'self.{k} = \'\' if \'{kwargs[k]}\' == \'None\' else \'{kwargs[k]}\'')
    def attributes(self) -> dict: return {x : y for x,y in self.__dict__.items() if "__" not in x}
    def orderedRow(self, orderedHeaders) -> list: return [y for x,y in sorted(self.attributes().items(), key = lambda d : orderedHeaders.index(d[0]))]
    def getId(self) -> str: return self.__id
    def setId(self, id): self.__id = id
    def getTableName(self) -> str: return self.__tableName

