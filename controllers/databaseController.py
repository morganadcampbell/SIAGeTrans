from configs import configs
from datetime import datetime
from enum import Enum
import mysql.connector
import json

class EventType(Enum):
    FLOODED_ROAD = 1
    PARTIAL_ROAD_CLOSURE = 2
    TOTAL_ROAD_CLOSURE = 3
    ROAD_ACCIDENT = 4

class DatabaseObject:
    def __init__(self, tableName : str, row : list[str]):
        self.tableName = tableName ## setting table metadata as attributes of the instance
        self.columnHeaders,self.columnTypes = columnHeaders,columnTypes = tuple(map(list, list(zip(*DatabaseController.getTableMetadata().get(tableName)))))
        for c in range(len(row)): ## setting row info as attributes of the instance
            exec(f'self.{columnHeaders[c]} = {columnTypes[c]}(\'{row[c]}\')')

    def row(self): return list(self.__dict__.values())[3:]

class DatabaseController:
    def __init__(self):
        self.dbconnector = mysql.connector.connect(**configs.mysql_connection_config)
        self.dbcursor = self.dbconnector.cursor() ## creating cursor
        self.tableColumns = DatabaseController.getTableMetadata()

    @staticmethod
    def getTableMetadata() -> dict:
        with open('files/databaseMetadata.json') as tableMetadata: ## retrieving metadata from tableMetadata.json
            tableColumns = json.load(tableMetadata)
        return tableColumns

    def select(self, tableName : str, id : int) -> DatabaseObject:
        columnHeaders,columnTypes = tuple(map(list, list(zip(*self.tableColumns.get(tableName))))) ## retrieving table metadata
        query = f"select {','.join(columnHeaders)} from {tableName} where id = {id}" ## composing the query
        self.dbcursor.execute(query) ## executing query
        row = self.dbcursor.fetchall()[0] ## retrieving table data
        return DatabaseObject(tableName, list(map(str, row))) ## instantiating an object with retrieved data

    def insert(self, object : DatabaseObject) -> int:
        rowValues = list(map(lambda x,y : str(x) if y == 'int' or x == "Null" else '\'' + str(x) + '\'' , object.row()[1:], object.columnTypes[1:])) ## adding apostrophes for text and datetime columns
        self.dbcursor.execute(f"insert into {object.tableName} ({','.join(object.columnHeaders[1:])}) values ({','.join(rowValues)})") ## executing query
        self.dbconnector.commit() ## commit updates
        object.id = self.dbcursor.lastrowid ## updating object's id
        return self.dbcursor.lastrowid
        
    def delete(self, object : DatabaseObject) -> int:
        self.dbcursor.execute(f"delete from {object.tableName} where {object.columnHeaders[0]} = {object.id}") ## executing query
        self.dbconnector.commit() ## commit updates
        return self.dbcursor.rowcount ## retrieving deleted rows count
    
    def update(self, object : DatabaseObject) -> int:
        rowValues = list(map(lambda x,y : str(x) if y == 'int' else 'Null' if x == "None" else '\'' + str(x) + '\'' , object.row()[1:], object.columnTypes[1:])) ## adding apostrophes for text and datetime columns
        settingList = ','.join([x + "=" + y for x,y in zip(object.columnHeaders[1:], rowValues)]) ## composing the list of columns to be updated
        self.dbcursor.execute(f"update {object.tableName} set {settingList} where id = {object.id}") ## executing query
        self.dbconnector.commit() ## commit updates
        return self.dbcursor.rowcount ## retrieving updated rows count

