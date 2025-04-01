import mysql.connector
from datetime import datetime
import json

class DatabaseObject:
    def __init__(self, tableName : str, columnHeaders : list[str], columnTypes : list[str], row : list[str]):
        self.tableName = tableName ## setting table metadata as attributes of the instance
        self.columnHeaders = columnHeaders
        self.columnTypes = columnTypes
        for c in range(len(row)): ## setting row info as attributes of the instance
            exec(f'self.{columnHeaders[c]} = {columnTypes[c]}(\'{row[c]}\')')

class DatabaseController:
    @staticmethod
    def getTableMetadata() -> dict:
        with open('tableMetadata.json') as tableMetadata: ## retrieving metadata from tableMetadata.json
            tableColumns = json.load(tableMetadata)
        return tableColumns
    
    def __init__(self, host : str = "localhost", user : str = "lsiagetrans", password : str = "123abc", database : str = "siagetrans"):
        self.host = host ## setting parameters
        self.user = user
        self.password = password
        self.database = database
        self.dbconnector = mysql.connector.connect( ## setting up connection
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    auth_plugin='mysql_native_password'
                    )
        self.dbcursor = self.dbconnector.cursor() ## creating cursor
        self.tableColumns = DatabaseController.getTableMetadata()

    def select(self, tableName : str, id : int) -> DatabaseObject:
        columnHeaders,columnTypes = tuple(map(list, list(zip(*self.tableColumns.get(tableName))))) ## retrieving table metadata
        query = f"select {','.join(columnHeaders)} from {tableName} where {columnHeaders[0]} = {id}" ## composing the query
        self.dbcursor.execute(query) ## executing query
        row = self.dbcursor.fetchall()[0] ## retrieving table data
        return DatabaseObject(tableName, columnHeaders, columnTypes, list(map(str, row))) ## instantiating an object with retrieved data

    def insert(self, tableName : str, row : list) -> int:
        columnHeaders,columnTypes = tuple(map(list, list(zip(*self.tableColumns.get(tableName))))) ## retrieving table metadata
        rowValues = list(map(lambda x,y : str(x) if y == 'int' or x == "Null" else '\'' + str(x) + '\'' , row, columnTypes[1:])) ## adding apostrophes for text and datetime columns
        query = f"insert into {tableName} ({','.join(columnHeaders[1:])}) values ({','.join(rowValues)})" ## composing the query
        self.dbcursor.execute(query) ## executing query
        self.dbconnector.commit() ## commit updates
        return self.dbcursor.lastrowid ## retrieving inserted row id
        
    def delete(self, tableName : str, id : int) -> int:
        columnHeaders = [x for x,y in self.tableColumns.get(tableName)] ## retrieving table metadata
        query = f"delete from {tableName} where {columnHeaders[0]} = {id}"
        print(query)
        self.dbcursor.execute(query) ## executing query
        self.dbconnector.commit() ## commit updates
        return self.dbcursor.rowcount ## retrieving deleted rows count
    
    def update(self, tableName : str, databaseObject : DatabaseObject) -> int:
        columnHeaders,columnTypes = tuple(map(list, list(zip(*self.tableColumns.get(tableName))))) ## retrieving table metadata
        rowValues = list(map(lambda x,y : str(x) if y == 'int' else 'Null' if x == "None" else '\'' + str(x) + '\'' , list(databaseObject.__dict__.values())[4:], columnTypes[1:])) ## adding apostrophes for text and datetime columns
        settingList = ','.join([x + "=" + y for x,y in zip(columnHeaders[1:], rowValues)]) ## composing the list of columns to be updated
        query = f"update {tableName} set {settingList} where {columnHeaders[0]} = {databaseObject.__dict__.get(columnHeaders[0])}"
        self.dbcursor.execute(query) ## executing query
        self.dbconnector.commit() ## commit updates
        return self.dbcursor.rowcount ## retrieving updated rows count

