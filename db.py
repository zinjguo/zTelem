from collections.abc import Iterable
from msilib import schema
import sqlite3
from typing import Any

class Plane:
    def __init__(self, sim="DCS", plane="Default", gainXMin=10, gainXMax=10, gainYMin=0, gainYMax=255, gainVs=10, gainVne=200, gainEnable=1, gunEnable=1, gunGain=255, AOAEnable=1, AOAGain=255, AOAMin = 8, AOAMax=13, windEnable=1, windMin=5, windMax=180):
        self.sim = str(sim)
        self.plane = str(plane)
        self.gainXMin = int(gainXMin)
        self.gainXMax = int(gainXMax)
        self.gainYMin = int(gainYMin)
        self.gainYMax = int(gainYMax)
        self.gainVs = int(gainVs)
        self.gainVne = int(gainVne)
        self.gainEnable = int(gainEnable)
        self.gunEnable = int(gunEnable)
        self.gunGain = int(gunGain)
        self.AOAEnable = int(AOAEnable)
        self.AOAGain = int(AOAGain)
        self.AOAMin = int(AOAMin)
        self.AOAMax = int(AOAMax)
        self.windEnable = int(windEnable)
        self.windMin = int(windMin)
        self.windMax = int(windMax)
    
    def __str__(self):
        members = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]
        return ", ".join([f"{member}: {getattr(self, member)}" for member in members])
            
class DbHandler:
    def __init__(self):
        self.conn = sqlite3.connect('db.sqlite3')
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.dbVersion = 1
        self.createSchema()
        print(self.getPlane())
        

    def getData(self, query):
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def insertData(self, query):
        self.cursor.execute(query)
        self.conn.commit()
        
    def deleteData(self, query):
        self.cursor.execute(query)
        self.conn.commit()
        
    def insertPlane(self, plane:Plane):
        members = [attr for attr in dir(plane) if not callable(getattr(plane, attr)) and not attr.startswith("__")]
        columns = ", ".join(members)
        values = ", ".join([f":{member}" for member in members])
        self.cursor.execute(f"""INSERT INTO planes ({columns}) 
                            VALUES ({values})""", 
                            {'sim': plane.sim, 'plane': plane.plane, 'gainXMin': plane.gainXMin, 'gainXMax': plane.gainXMax, 
                             'gainYMin': plane.gainYMin, 'gainYMax': plane.gainYMax, 'gainVs': plane.gainVs, 'gainVne': plane.gainVne, 
                             'gainEnable': plane.gainEnable, 'gunEnable': plane.gunEnable, 'gunGain': plane.gunGain, 'AOAEnable': plane.AOAEnable, 
                             'AOAGain': plane.AOAGain, 'AOAMin': plane.AOAMin, 'AOAMax': plane.AOAMax, 'windEnable': plane.windEnable, 
                             'windMin': plane.windMin, 'windMax': plane.windMax})
        self.conn.commit()
        
    def getPlane(self, sim="DCS", plane="Default"):
        self.cursor.execute("SELECT * FROM planes WHERE sim = ? AND plane = ?", (sim, plane))
        row = self.cursor.fetchone()
        plane = Plane()
        for key in row.keys():
            setattr(plane, key, row[key])
        return plane
    
    def updatePlane(self, plane:Plane):
        members = [attr for attr in dir(plane) if not callable(getattr(plane, attr)) and not attr.startswith("__")]
        columns = ", ".join([f"{member} = :{member}" for member in members])
        self.cursor.execute(f"""UPDATE planes 
                            SET {columns} 
                            WHERE sim = :sim AND plane = :plane""", 
                            {'sim': plane.sim, 'plane': plane.plane, 'gainXMin': plane.gainXMin, 'gainXMax': plane.gainXMax, 
                             'gainYMin': plane.gainYMin, 'gainYMax': plane.gainYMax, 'gainVs': plane.gainVs, 'gainVne': plane.gainVne, 
                             'gainEnable': plane.gainEnable, 'gunEnable': plane.gunEnable, 'gunGain': plane.gunGain, 'AOAEnable': plane.AOAEnable, 
                             'AOAGain': plane.AOAGain, 'AOAMin': plane.AOAMin, 'AOAMax': plane.AOAMax, 'windEnable': plane.windEnable, 
                             'windMin': plane.windMin, 'windMax': plane.windMax})
        self.conn.commit()

    def __del__(self):
        self.conn.close()
        
    def createSchema(self):
        currentDbVersion = self.cursor.execute('pragma user_version').fetchone()[0]
        if(currentDbVersion == 0):
            plane = Plane()
            members = [attr for attr in dir(plane) if not callable(getattr(plane, attr)) and not attr.startswith("__")]
            # Get the values of each attribute of plane
            schemaColumns = ""
            for member in members:
                value = getattr(plane, member)
                if type(value).__name__ == "str":
                    schemaColumns += f"{member} TEXT, "
                elif type(value).__name__ == "int":
                    schemaColumns += f"{member} INTEGER, "
        
            self.cursor.execute(f'''CREATE TABLE IF NOT EXISTS planes (
                {schemaColumns}
                PRIMARY KEY (sim, plane) 
            )''')
            
            self.cursor.execute(f'pragma user_version = {self.dbVersion}')
            
            result = self.cursor.fetchall();   
            if len(result) == 0:
                self.insertPlane(Plane())
            
            self.conn.commit()
        
        if(currentDbVersion != self.dbVersion and currentDbVersion != 0):
            raise("Database version mismatch")
        

    def upgradeSchema(self):
        pass
    