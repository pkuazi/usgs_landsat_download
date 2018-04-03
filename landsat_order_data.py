# coding: utf-8
'''
Created on Jan 18, 2016

@author: root
'''
import datetime, os, time, subprocess
import threading
import pgsql
# from usgs_landsat_download import pgsql
import usgsutils
from usgs_download_entities import entity_download

MSG_OK = "Success"  # OK
MSG_EORDER = "Order"
MSG_SKIP = "Skip"  # SKIP
MSG_EDATA = "Error"  # File error

print("before database")

def get_pg_src():
    pg_src = pgsql.Pgsql("10.0.138.20", "postgres", "", "gscloud")
    return pg_src
def get_pg_metadata():
    pg_metadata = pgsql.Pgsql("10.0.138.20", "postgres", "", "gscloud_metadata")
    return pg_metadata

cache_root = "/dev/shm"
# data_root = "/mnt/gscloud/LANDSAT"
data_root = "/mnt"

print("after database")


class User(object):
    def __init__(self, userid):
        self.userid = userid
        self.ctime = datetime.datetime.now()

class UserOrderManager(object):
    info_sql = "select ordernumber, userid from gscloud_order_info where laststate in (0, 1, 2) order by level desc, submitdate asc limit 3 offset %s" 
    data_sql = '''select id, dataname, laststate, retry_times, statestr, usgs_ordernumber from gscloud_order_data where productid in (241, 242, 243, 244, 245, 411) and 
                        infoid = %s and retry_times < 4 and laststate in (0, 11, -2, -3) order by level desc , submitdate asc'''
    def __init__(self,):
        self.user_list = {}
        
    def reset_state(self):
        pg_src = get_pg_src()
        pg_src.update("update gscloud_order_data set laststate = -2 where laststate = 1 and productid in (241, 242, 243, 244, 245, 411)")
    
    def query_user(self, userid):
        # if self.user_list.has_key(userid):
        if userid in self.user_list:
            return True
        else:
            return False
        
    def remove_user(self, userid):
        # if self.user_list.has_key(userid):
        if userid in self.user_list:
            self.user_list.pop(userid)

    
    def register_user(self, userid):
        # if not self.user_list.has_key(userid):
        if userid in self.user_list:
            self.user_list[userid] = User(userid)
    
    def test_targz(self, std_file):
        r = subprocess.Popen("tar -tvf %s" % std_file, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        r.wait()
        # print(r.stderr.read())
        if r.stderr.read().decode("utf-8").find("Error") > 0:
            return False
        return True 
    
    def update_dataexists(self, dataid):
        pg_src = get_pg_src()
        pg_metadata = get_pg_metadata()
        try:
            pg_metadata.update("update metadata_landsat set dataexists = 1 where dataid = %s", [dataid, ])
            pg_src.update("update gscloud_order_data set startdate = %s, laststate = 2 where dataname = %s and startdate is null and laststate != 2", [datetime.datetime.now(), dataid])
            pg_src.update("update gscloud_order_data set finishdate= %s, laststate = 2 where dataname = %s and finishdate is null", [datetime.datetime.now(), dataid])
        except Exception as e:
            print(e)
            pass

    def update_laststate(self, data_id, laststate, retry_times, statestr, usgs_ordernumber, update_startdate= False):
        pg_src = get_pg_src()
        try:
            pg_src.update("update gscloud_order_data set laststate = %s, retry_times = %s, statestr = %s, usgs_ordernumber = %s where id = %s", [laststate, retry_times, statestr, usgs_ordernumber, data_id, ])
            if update_startdate:
                pg_src.update("update gscloud_order_data set startdate = %s where id = %s", [datetime.datetime.now(), data_id])
            if laststate in (-1, 2):
                pg_src.update("update gscloud_order_data set finishdate = %s where id = %s", [datetime.datetime.now(), data_id])
        except Exception as e:
            print( str(e))

    def download_landsat(self, landsat_datas):
        icount = 0
        for landsat_data in landsat_datas:
            data_id, dataid, laststate, retry_times, statestr, usgs_ordernumber = landsat_data
            dst_file = usgsutils.parse_Landsat_filename(data_root, dataid)
            if os.path.exists(dst_file):
                if not self.test_targz(dst_file):
                    os.unlink(dst_file)
                else:
                    self.update_dataexists( dataid )
                    self.update_laststate( data_id, 2, retry_times, statestr, usgs_ordernumber, True)
                    continue
                
            outfile = os.path.join(cache_root, "%s.tar.gz" % dataid) 
            print( "save to: ", outfile )
 
            retry_times = retry_times + 1
            self.update_laststate( data_id, 1, retry_times, statestr, usgs_ordernumber, laststate==0)
            laststate = -2
            msg_code, return_code, statestr = entity_download(dataid, outfile)

            if msg_code == None:
                laststate = return_code
            elif msg_code == MSG_EDATA:
                laststate = -3
            elif msg_code == MSG_EORDER:
                laststate = 10
                usgs_ordernumber = return_code
            elif msg_code == MSG_OK:
                laststate = 2
               
            if os.path.exists(outfile):
                if not self.test_targz(outfile):                 
                    if laststate==2:
                        laststate = -3
                    if os.path.exists(outfile):
                        os.unlink(outfile)
                        
                else:   
                    basedir = os.path.dirname( dst_file )
                    if not os.path.exists( basedir ) :
                        os.makedirs( basedir  )
        
                    cmd = "mv %s %s" % (outfile, dst_file)   
                    
                    print (cmd)
                    os.system(cmd)
        
                    if os.path.exists(outfile):
                        os.unlink(outfile)
        
                    self.update_dataexists( dataid )
            else:
                if laststate == 2:
                    laststate = -3
                if os.path.exists(outfile):
                    os.unlink(outfile)    

            self.update_laststate( data_id, laststate, retry_times, statestr, usgs_ordernumber)
            icount += 1
            if icount > 4:
                break 
    
    def run(self):
        self.reset_state()
        icount = 0
        while True:
            pg_src = get_pg_src()
            datas = pg_src.getAll(self.info_sql, (icount,))
            if len(datas) == 0:
                icount = 0
                self.reset_state()
                for user in self.user_list.values():
                    self.remove_user(user.userid)
                print( "程序休眠5分钟")
                time.sleep(300)
                continue
            print( len(datas), "orders")

            for data in datas:
                print (data)
                ordernumber, userid = data
                if self.query_user(userid) and userid != 2:
                    print( "continue")
                    continue
                print (self.data_sql)
                pg_src = get_pg_src()
                landsat_datas = pg_src.getAll(self.data_sql, (ordernumber,))
                if len(landsat_datas) > 0:
                    self.register_user(userid)
                    print (landsat_datas)
                    self.download_landsat(landsat_datas)
            icount = icount + 3

            pg_src = get_pg_src()
            pg_src.update("update gscloud_order_data set laststate = 11 where laststate = 10 and date_part('day', now() - startdate::timestamp ) > 9")
            pg_src.update("update gscloud_order_data set retry_times = 0 where productid in (241, 242, 243, 244, 245, 411) and retry_times = 4 and laststate in (11, -2, -3) and date_part('day', now() - startdate::timestamp ) > 1")
            user_list = self.user_list.values()
            delta = datetime.timedelta(days=1)

            for user in user_list:
                if datetime.datetime.now() - user.ctime > delta:
                    self.remove_user(user.userid)

if __name__ == "__main__":
    print("start thread ")
    
    usermanager = UserOrderManager()
    usermanager.run()
    
