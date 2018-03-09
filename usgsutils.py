'''
Created on May 16, 2013

@author: root
'''
  
import datetime
import re
import sys


def parse_modisl1b_filename(root, dataid):

#     MOD021KM.A2014018.1755.005
    
    if root.endswith("/"):
        root = root[:-1]
    
    ids = dataid.split(".") 

    if ids[0][:3] == "MOD":
        root = root + "/" + "MOLT"
    elif ids[0][:3] == "MYD":
        root = root + "/" + "MOLA"
    else:
        return None

    root = root + "/" + ids[0] + "." + ids[-1]

    sdate = ids[1]
    if len(sdate) != len("A2010001"):
#         print("invalid dataid:", dataid)
        return None

    year = int(sdate[1:5])
    days = int(sdate[-3:])

    root = root + "/" + str(year)

    odate = datetime.datetime(year=year, month=1, day=1) + datetime.timedelta(days=days - 1)

    root = root + "/" + odate.strftime("%Y.%m.%d") + "/" + dataid + ".hdf"

    return root

def parse_modisland_filename(root, dataid):

#     MOD09A1.A2013145.h35v10.005
    if root.endswith("/"):
        root = root[:-1]
    ids = dataid.split(".")
#    root = "/mnt/gscloud/modis_land/data"

    if ids[0][:3] == "MOD":
        root = root + "/" + "MOLT"
    elif ids[0][:3] == "MYD":
        root = root + "/" + "MOLA"
    else:
        return None

    root = root + "/" + ids[0] + "." + ids[-1]

    sdate = ids[1]
    if len(sdate) != len("A2010001"):
#         print("invalid dataid:", dataid)
        return None

    year = int(sdate[1:5])
    days = int(sdate[-3:])

    root = root + "/" + str(year)

    odate = datetime.datetime(year=year, month=1, day=1) + datetime.timedelta(days=days - 1)

    root = root + "/" + odate.strftime("%Y.%m.%d") + "/" + dataid + ".hdf"

    return root

def parse_Landsat_filename(root, dataid):
    if root.endswith("/"):
        root = root[:-1]
    
    sensor = parseSensor(dataid)
    
    def r():    
        if sensor in ["LT4", "LT5"]: 
            return "L45TM"  
        
        if  sensor in ["LC8", "LO8"]:
            return "OLI_TIRS"     
        
        if  "LE7ON" == sensor:
            return "L7slc-on" 
        
        if  "LE7OFF" == sensor:
            return "L7slc-off"      
            
        if sensor in [ "LM4", "LM5"]:     
            return "L45MSS"
        
        if sensor in ["LM1", "LM2", "LM3"]:     
            return 'L123MSS'
        
        return None

    dtype = r()
    if dtype is None:
        return None    

    path = int(dataid[3:6])
    row = int(dataid[6:9])
    year = int(dataid[9:13])    
    
    return "%s/%s/%s/%s/%s/%s.tar.gz" % (root, dtype, path, row, year, dataid)

    
def parseSensor(dataid) :    
    if  dataid.startswith("EO1A") :
        return "EO1A" 
    elif  dataid.startswith("EO1H"):
        return "EO1H"
    
    elif dataid.startswith("LE7") :
        
        year = dataid[9:13] 
        days = dataid[13:16]  
                
        ddate = datetime.datetime(year=int(year), month=1, day=1) + datetime.timedelta(days=int(days) - 1)
        cdate = datetime.datetime.strptime("2003-06-01", "%Y-%m-%d")   
        
        if ddate > cdate:
            return "LE7OFF"
        else:
            return "LE7ON" 
        
    elif dataid.startswith("LC8"):
        return "LC8"
    elif dataid.startswith("LO8"):
        return "LO8"    
    elif dataid.startswith("LT8"):
        return "LO8"
    
    elif dataid.startswith("LT5"):
        return "LT5"
    elif dataid.startswith("LT4"):
        return "LT4"
    
    elif dataid.startswith("LM5"):
        return "LM5"
    elif dataid.startswith("LM4"):
        return "LM4"
    elif dataid.startswith("LM3"):
        return "LM3"
    elif dataid.startswith("LM2"):
        return "LM2"
    elif dataid.startswith("LM1"):
        return "LM1" 
    
    return None
   
def parse_Usgs_DatasetName(dataid) :
    
    sensor = parseSensor(dataid)
 
    if  "EO1A" == sensor :
        return "EO1_ALI_PUB" 
    
    if  "EO1H" == sensor  :
        return "EO1_HYP_PUB"  
    
    if sensor in ["LT4", "LT5"]: 
        return "LANDSAT_TM"  
    
    if  sensor in ["LC8", "LO8"]:
        return "LANDSAT_8"     
    
    if  "LE7ON" == sensor:
        return "LANDSAT_ETM" 
    
    if  "LE7OFF" == sensor:
        return "LANDSAT_ETM_SLC_OFF"      
        
    if sensor in ["LM1", "LM2", "LM3", "LM4", "LM5"]:     
        return "LANDSAT_MSS"
    
    return None

def parse_Usgs_fileext(dataid):
    sensor = parseSensor(dataid)
    
    if sensor in ["LC8", "LO8", "LT4", "LT5", "LE7ON", "LE7OFF", "LM1", "LM2", "LM3", "LM4", "LM5"]:
        return ".tar.gz"
    
    if sensor in [ "EO1A", "EO1H"  ] :
        return ".tgz"    
    
    return ""
         
def parse_Usgs_DatasetId(dataid) :
    sensor = parseSensor(dataid);

    if  "EO1A" == sensor:
        return 1852 
    
    if  "EO1H" == sensor:
        return 1854  
    
    if  sensor in ["LC8", "LO8"]:
        return 12864    
    
    if sensor in ["LT4", "LT5"]: 
        return 12266  
    
    if  "LE7ON" == sensor:
        return 12267 
    
    if  "LE7OFF" == sensor:
        return 12267
    
    if sensor in ["LM1", "LM2", "LM3", "LM4", "LM5"]:   
        return 3120 
    
    return -1

if __name__ == '__main__':  
 
    dataid = "MOD09A1.A2013145.h22v17.005"        
    print(parse_modisland_filename("", dataid))
    
 
    dataid = "MOD021KM.A2014018.1755.005"        
    print(parse_modisl1b_filename("", dataid))
    
#     print  is_china_region(s)
