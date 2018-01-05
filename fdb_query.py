#!/usr/bin/python3
import os
# from fdb import services
from constants import BColors
try:
    import fdb_embedded as fdb
    # from fdb_embedded import services
    FDB_AVAILABLE = True
except ImportError:
    FDB_AVAILABLE = False

class FDBquery():
    """Handles querying VVV firebird databases locally"""

    def __init__(self):
        self.db_filepath = ""

    def setup_environmentvars(self, path, mydbfilepath):
        """Sets up the FIREBIRD env var for securty2.fdb lookup"""
        # Point to our current VVV firebird database (for security2.fdb)
        # os.environ['FIREBIRD'] = '~/INSTALLED/VVV-1.3.0-x86_64/firebird'
        # Alternatively, use a copy of the security2.fdb:

        if not FDB_AVAILABLE:
            print(BColors.WARNING + "Warning: fdb_embedded couldn't be imported, \
            skipping checking FDB database in " + mydbfilepath \
            + "\nMake sure you've installed fdb_embedded correctly." + BColors.ENDC)
            return False

        os.environ['FIREBIRD'] = path
        self.db_filepath = mydbfilepath
        return True

    def get_set_from_result(self, word):
        """Search our FDB for word"""
        found_set = set()
        found_count = 0
        # con1 = services.connect(user='sysdba', password='masterkey')
        # print("Security file for database is: ", con1.get_security_database_path() + "\n")

        con = fdb.connect(
            database=self.db_filepath,
            # dsn='localhost:~/test/CGI.vvv', #localhost:3050
            user='sysdba', password='masterkey'
            #charset='UTF8' # specify a character set for the connection
        )

        # Create a Cursor object that operates in the context of Connection con:
        cur = con.cursor()

        if "'" in word: # we need to add an extra for SQL statements
            word = word.replace("'", "''")

        SELECT = "select * from FILES WHERE FILE_NAME LIKE '%" + word + ".%'" # adding period to include start of extension

        try:
            cur.execute(SELECT)


            for row in cur:
                # print("found: ", row[1])
                found_set.add(row[1])
                found_count += 1

            # print("found_count:", found_count)
            con.close()
            return found_set, found_count

        except Exception as identifier:
            errormesg = "Error while looking up: " + word + "\n" + str(identifier)
            print(BColors.FAIL + errormesg + BColors.ENDC)
            return found_set, found_count



# MEMO:
# not used:
# os.putenv("FIREBIRD", "~/INSTALLED/VVV-1.3.0-x86_64/")
# os.system("export FIREBIRD='~/INSTALLED/VVV-1.3.0-x86_64/firebird'")

# print('INFO:', con.db_info(fdb.isc_info_user_names))

# Execute the SELECT statement on tables:
# "FILE_NAME, FILE_EXT, FILE_SIZE, FILE_DATETIME, PATH_FILE_ID, PATH_ID, FILE_DESCRIPTION) VALUES ("
# LIKE, STARTING WITH, CONTAINING, SIMILAR TO

# Look for fields containing word (with any number of chars before and after), if only starting with, use word% instead
# SELECT2 = "select * from FILES WHERE FILE_NAME LIKE (?)" # Suggestion: use STARTING WITH instead of LIFE?
# wordparam = list()
# wordparam.append(word)
# cur.execute(SELECT2, wordparam) #requires a list or tuple

# Look for ANY of the words
# SELECT = "select * from FILES WHERE FILE_NAME LIKE '%word1%' OR FILE_NAME LIKE '%word2%'"

# Look for BOTH words to be present
# SELECT = "select * from FILES WHERE FILE_NAME LIKE '%word1%' AND FILE_NAME LIKE '%word2%'"

# Retrieve all rows as a sequence and print that sequence:
# print(cur.fetchall())