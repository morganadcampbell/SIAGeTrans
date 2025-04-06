import os, sys
sys.path.insert(1, "/".join(os.path.realpath(__file__).split("/")[0:-2])) ## adding folders to path

from configs import configs
from datetime import datetime
from models.databaseObject import DatabaseObject
import mysql.connector
import json

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
        attributes = dict(zip(columnHeaders,self.dbcursor.fetchall()[0])) ## retrieving table data
        return DatabaseObject(tableName, **attributes) ## instantiating an object with retrieved data

    def insert(self, object : DatabaseObject) -> int:
        columnHeaders,columnTypes = tuple(map(list, list(zip(*self.tableColumns.get(object.getTableName()))))) ## retrieving table metadata
        rowValues = list(map(lambda x,y : x if y in ('int', 'float') else 'Null' if x == "" else '\'' + str(x) + '\'' , object.orderedRow(columnHeaders), columnTypes[1:])) ## adding apostrophes for text and datetime columns
        self.dbcursor.execute(f"insert into {object.getTableName()} ({','.join(columnHeaders[1:])}) values ({','.join(rowValues)})") ## executing query
        self.dbconnector.commit() ## commit updates
        object.setId(self.dbcursor.lastrowid) ## updating object's id
        return self.dbcursor.lastrowid
        
    def delete(self, object : DatabaseObject) -> int:
        self.dbcursor.execute(f"delete from {object.getTableName()} where id = {object.getId()}") ## executing query
        self.dbconnector.commit() ## commit updates
        return self.dbcursor.rowcount ## retrieving deleted rows count
    
    def update(self, object : DatabaseObject) -> int:
        columnHeaders,columnTypes = tuple(map(list, list(zip(*self.tableColumns.get(object.getTableName()))))) ## retrieving table metadata
        rowValues = list(map(lambda x,y : str(x) if y in ('int', 'float') else 'Null' if x == '' else '\'' + str(x) + '\'' , object.orderedRow(columnHeaders), columnTypes[1:])) ## adding apostrophes for text and datetime columns
        settingList = ','.join([x + "=" + y for x,y in zip(columnHeaders[1:], rowValues)]) ## composing the list of columns to be updated
        self.dbcursor.execute(f"update {object.getTableName()} set {settingList} where id = {object.getId()}") ## executing query
        self.dbconnector.commit() ## commit updates
        return self.dbcursor.rowcount ## retrieving updated rows count

