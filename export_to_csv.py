#!/usr/bin/python3
import os
import argparse
import csv
try:
    import fdb_embedded as fdb
    # from fdb_embedded import services
    FDB_AVAILABLE = True
except ImportError:
    FDB_AVAILABLE = False


class MainClass:
    """Standalone script to export a VVV database
    to CSV format"""

    def __init__(self):
        #Constants
        self.cwd = os.getcwd()
        self.ofile_path = self.cwd
        self.input_filepath = ""
        self.outputpath = ""
        self.sepvalue = ","


    def main(self):
        """main"""
        
        argparser = argparse.ArgumentParser(description=\
        "Exports firebird database to CSV file")

        # group = argparser.add_mutually_exclusive_group()

        argparser.add_argument("input", type=str, metavar="INPUT", help=\
        "FDB input file to export")
        argparser.add_argument("-o", "--outputdir", dest="outputdir", type=str, metavar="path", help=\
        "target path where to create csv file (default is current working dir)", default=self.ofile_path)
        argparser.add_argument("-p", "--security", dest="securitypath", type=str, metavar="path", help=\
        "path to security2.fdb (required)", default=self.cwd)
        argparser.add_argument("-s", "--separator", dest="separator", type=str, metavar="sep", help=\
        "separator to use in CSV format (deault is tab)", default="\t")

        args = argparser.parse_args()

        input_filepath = args.input #TODO: sanitize for valid file
        outputpath = str(args.outputdir).rstrip("/") + os.sep + os.path.basename(input_filepath) + ".csv"
        securitypath = str(args.securitypath) #TODO: test if security2.fdb is really there
        separator = str(args.separator)
        print("DEBUG:")
        print("input_filepath:" + input_filepath)
        print("outputpath:" + outputpath)
        print("securitypath:" + securitypath)


        FDBquery.setup_environmentvars(self, securitypath, input_filepath)
        # FDBquery.get_set_from_search(self, "test")
        FDBquery.export_to_csv(self, outputpath, separator)

class FDBquery():
    """Handles querying VVV firebird databases locally"""

    def __init__(self):
        self.db_filepath = ""

    def setup_environmentvars(self, path, mydbfilepath):
        """Sets up the FIREBIRD env var for securty2.fdb lookup"""

        if not FDB_AVAILABLE:
            print(BColors.WARNING + "Warning: fdb_embedded couldn't be imported! " \
            + "\nMake sure you've installed fdb_embedded correctly." + BColors.ENDC)
            return False

        os.environ['FIREBIRD'] = path
        self.db_filepath = mydbfilepath
        return True

    def export_to_csv(self, outputfilepath, separator):
        """export the ENTIRE DB to a CSV formatted file"""

        con = fdb.connect(
            database=self.db_filepath,
            # dsn='localhost:~/test/CGI.vvv', #localhost:3050
            user='sysdba', password='masterkey'
            #charset='UTF8' # specify a character set for the connection
        )
        cur = con.cursor()
        statement = "select * from FILES"
        cur.execute(statement)
        # Retrieve all rows as a sequence and print that sequence:
        print(cur.fetchall())

        # VVV export format: Volume,Path,Name,Size,Ext,Last modified,Description

        with open(outputfilepath, 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([ i[0] for i in cur.description ]) 
            writer.writerows(cur.fetchall())

    def get_set_from_search(self, word):
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
                print("found: ", row[1])
                found_set.add(row[1])
                found_count += 1

            print("found_count:", found_count)
            con.close()
            return found_set, found_count

        except Exception as identifier:
            errormesg = "Error while looking up: " + word + "\n" + str(identifier)
            print(BColors.FAIL + errormesg + BColors.ENDC)
            return found_set, found_count


class BColors:
    """Color codes for stdout"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    BLUEOK = OKBLUE + "[OK]: " + ENDC



if __name__ == "__main__":
    MAINOBJ = MainClass()
    MAINOBJ.main()