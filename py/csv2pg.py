#! /usr/bin/env python3

import os, sys, psycopg2, argparse, csv
from messytables import CSVTableSet, type_guess, \
  types_processor, headers_guess, headers_processor, \
  offset_processor, any_tableset
  
rowtocheck = 5

def main():
    
    pgpass = os.getenv('PGPASSFILE', os.path.expanduser('~/.pgpass'))
    if not os.path.exists(pgpass):
        print('You need to create file ~/.pgpass that contains at least one line:')
        print('hostname:port:database:username:password')
        print('and has restricted permissions: chmod 600 ~/.pgpass')
        print('Also please check https://www.postgresql.org/docs/current/static/libpq-pgpass.html')
        return False
        
    #args.dsn == 'postgresql://dirk@mydb:32063/petersen'
    #args.csvfile = '/home/petersen/sc/data/slurm_jobs.csv'
    
    if not args.dsn.startswith('postgresql://'):
        dl = args.dsn.split(':')
        args.dsn = 'postgresql://%s@%s:%s/%s' % (dl[3], dl[0], dl[1], dl[2])
    
    try:
        conn = psycopg2.connect(args.dsn)
        cur = conn.cursor()
    except (Exception, psycopg2.DatabaseError) as error:
        print('Database error:', error)
        return False

    with open(args.csvfile, 'rb') as fh:        
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        #print row_set.sample.next()
        offset, headers = headers_guess(row_set.sample)
        row_set.register_processor(headers_processor(headers))
        row_set.register_processor(offset_processor(offset + rowtocheck))
        types = type_guess(row_set.sample, strict=True)

    myd = dict (zip (headers, types))
    print("\nDetected columns & types:\n", myd, '\n')
    
    table = os.path.splitext(os.path.basename(args.csvfile))[0]
    table = table.replace('-','_')
    table = table.replace(' ','_')
    create_sql = "CREATE TABLE %s (" % table
    idh = 0
    for h in headers:
        myt = "TEXT"
        if str(types[idh]) == 'Integer':
            myt = 'BIGINT'
        elif str(types[idh]) == 'Bool':
             myt = 'BIGINT'
        elif str(types[idh]) == 'Decimal':
             myt = 'DECIMAL'
        
        create_sql += "%s %s, " % (h,myt)
        idh += 1
    create_sql = create_sql[:-2] + ');'

    print("\ncreating postgres table '%s':\n" % table, create_sql, '\n')
    try:
        if args.overwrite:
            drop_sql = 'DROP TABLE IF EXISTS %s' % table
            cur.execute(drop_sql)
            conn.commit()
        cur.execute(create_sql)
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print('Database error:', error)
        sys.exit()

    print("\nloading data .... ")

    with open(args.csvfile, 'rb') as fh:
        sample_text = ''.join(str(fh.readline()) for x in range(3))
        try:
            dialect = csv.Sniffer().sniff(sample_text)
            if dialect.delimiter == 't':
                delim = '\t'
            else:
                delim = dialect.delimiter            
        except:
            delim = ","
        copy_sql = "COPY %s FROM stdin WITH CSV HEADER DELIMITER as '%s'" % \
                   (table, delim)        
        try:
            cur.copy_expert(sql=copy_sql, file=fh)
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print('Database error:', error)
            
    print('Done !')


def parse_arguments():
    """
    Gather command-line arguments.
    """
    parser = argparse.ArgumentParser(prog='csv2pg',
        description='a tool for quickly loading csv files into Postgres ' + \
        'with limited schema detection capabilties (BIGINT & TEXT)')
    parser.add_argument( '--overwrite', '-o', dest='overwrite', action='store_true', default=False,
        help="drop existing table if already exist.")
    parser.add_argument('--settype', '-s', dest='settype', action='store', default='', 
        help='list of comma separated postgres type overwrites for field names, for example ' + \
              '--settype name:varchar(30),year:int,startdate:date')
    parser.add_argument('dsn', action='store', 
        help='postgres connection string, format postgresql://username@hostname:port/database ' + \
         'or ~/.pgpass style credentials such as hostname:port:database:username')
    parser.add_argument('csvfile', action='store', 
        help='csv file you want to upload to postgres ' + \
            'the delimiter can be a tab, pipe or a comma')

    #parser.add_argument('--mailto', '-m', dest='mailto', action='store', default='', 
        #help='send email address to notify of a new deployment.')

    return parser.parse_args()

if __name__=="__main__":
    args = parse_arguments()
    try:
        main()
    except KeyboardInterrupt:
        print ('Exit !')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
