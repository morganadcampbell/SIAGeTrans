from configs import configs
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
        columnHeaders = [x for x,y in self.tableColumns.get('trafficlights')] ## retrieving table metadata
        query = f"select * from {tableName} where id = {id}" ## composing the query
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

    def getTrafficLightsAtIntersection(self, intersectionId : int):
        columnHeaders = [x for x,y in self.tableColumns.get('trafficlights')] ## retrieving table metadata
        query = f"select t.* from trafficlights t join roadsections r on t.id_roadsection = r.id join intersections i on r.id_intersection = i.id where i.id = {intersectionId}" ## composing the query
        self.dbcursor.execute(query) ## executing query
        managedTrafficLights = list()
        for t in self.dbcursor.fetchall():
            attributes = dict(zip(columnHeaders,t)) ## composing attributes with retrieved data
            managedTrafficLights.append(DatabaseObject('trafficlights', **attributes)) ## instantiating an object with retrieved data
        return managedTrafficLights
        
        
