#!/usr/bin/python3
import os
# import subprocess
# import sys
# import fdb
# from fdb import services
from constants import BColors

try:
    import fdb_embedded as fdb
    # from fdb_embedded import services
    FDB_AVAILABLE = True
except ImportError:
    FDB_AVAILABLE = False




# Point to our current VVV firebird database (for security2.fdb)
# os.environ['FIREBIRD'] = '~/INSTALLED/VVV-1.3.0-x86_64/firebird'

# Alternatively, use a copy of the security2.fdb:
os.environ['FIREBIRD'] = '~/test'

# not used:
# os.putenv("FIREBIRD", "/home/nupupun/INSTALLED/VVV-1.3.0-x86_64/")
# os.system("export FIREBIRD='/home/nupupun/INSTALLED/VVV-1.3.0-x86_64/firebird'")


def Get_Set_From_Result(word):
    """Search our FDB for word"""

    if not FDB_AVAILABLE:
        print(BColors.WARNING + "Warning: fdb_embedded couldn't be imported, skipping checking local database." + BColors.ENDC)
        return

    # con1 = services.connect(user='sysdba', password='masterkey')
    # print("Security file for database is: ", con1.get_security_database_path() + "\n")

    # The server is named 'bison'; the database file is at '/temp/test.db'.
    con = fdb.connect(
        database='~/test/CGI.vvv',
        # dsn='clevo:/home/nupupun/test/CGI.vvv', #localhost:3050
        user='sysdba', password='masterkey' #masterkey
        #charset='UTF8' # specify a character set for the connection
    )

    # print('INFO:', con.db_info(fdb.isc_info_user_names))

    # Create a Cursor object that operates in the context of Connection con:
    cur = con.cursor()

    # Execute the SELECT statement: 
    # "FILE_NAME, FILE_EXT, FILE_SIZE, FILE_DATETIME, PATH_FILE_ID, PATH_ID, FILE_DESCRIPTION) VALUES ("
    #'56430 - Resident_Evil Sheva_Alomar.jpeg'
    # '51330149_p0.jpg'
    # 55754

    # Look for fields containing word (with any number of chars before and after), if only starting with, use word% instead
    SELECT = "select * from FILES WHERE FILE_NAME LIKE '%" + word + ".%'"

    # Look for ANY of the words
    # SELECT = "select * from FILES WHERE FILE_NAME LIKE '%word1%' OR FILE_NAME LIKE '%word2%'"

    # Look for BOTH words to be present
    # SELECT = "select * from FILES WHERE FILE_NAME LIKE '%Sheva_Alomar%' AND FILE_NAME LIKE '%Resident_Evil%'"

    try:
        cur.execute(SELECT)
        found_set = set()
        found_count = 0

        for row in cur:
            #print("found: ", row[1])
            found_set.add(row[1])
            found_count += 1

        #print("found_count:", found_count)
        con.close()
        return found_set, found_count

    except Exception as identifier:
        print(identifier)
        return



    # # # Retrieve all rows as a sequence and print that sequence:
    # print(cur.fetchall())
