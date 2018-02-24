#! /usr/bin/env python3

import os, sys, psycopg2, argparse, csv, json
from Bio import Entrez
from collections import OrderedDict
  
def main():

    author = args.author
        
    results = searchHutchAuthor(author)
    id_list = results['IdList']
    papers = None
    try:
        papers = fetch_details(id_list)
    except:
        pass
    if not papers:
        print("no papers found")
        return False 
        
    j=0
    rank = 0
    month=""
    year=""
    for i, paper in enumerate(papers['PubmedArticle']):
        article = paper['MedlineCitation']['Article']
        journal = article['Journal']
        authors = article['AuthorList']
        aids=article['ELocationID']
        journalinfo = paper['MedlineCitation']['MedlineJournalInfo']
        
        if len(authors) > 0:
            rank, author = authorRank(authors, author)
        #if rank == 0 or (rank > 1 and rank < len(authors)-3):
            #only show pubs with first and last author 
        #    continue
        #if len(aids)==0:
        #    continue
        if 'Month' in journal['JournalIssue']['PubDate']:
            month=journal['JournalIssue']['PubDate']['Month']
            year=journal['JournalIssue']['PubDate']['Year']
        
        if year == '' or year < args.sinceyear:
            continue
        
        j+=1
        print("%d) %s" % (j, article['ArticleTitle']))    
        
        ISSN = ''
        if 'ISSNLinking' in journalinfo:
            ISSN = journalinfo['ISSNLinking']
        if len(aids)>0: 
            print("    ID: %s" % aids[0])
        print("    Journal: %s, ISSN: %s" % (journal['Title'], ISSN))
        
        print("    Year: %s, Month: %s" % (year, month))
            
        #print(json.dumps(article, indent=2))
        #sys.exit()
        
        print("    # of Authors: ", len(authors))   
        print("    %s rank: %s" % (author, rank) )             
        
        
        if 'GrantList' in article:
            ret = getgrants(article['GrantList'])
                      
        
def getgrants (grants):
    for g in grants:
        if 'GrantID' in g:
            print("    ",g['GrantID'],"(",g['Agency'],")")
        
    
def authorRank (authors, author):
    lastname = ''
    forename = ''
    initials = ''
    pos = author.find(' ')
    if pos > 0:
        lastname = author[:pos]
        forename = author[pos+1:]
    else:
        lastname = author
    i=0
    for a in authors:
        i+=1
        #if a['AffiliationInfo']:
        #    print ("  ", a['AffiliationInfo'][0]['Affiliation'])            
        if 'LastName' in a:
            if 'ForeName' in a and 'Initials' in a:
                if a['LastName'].lower() == lastname.lower() and a['ForeName'].startswith(forename):
                    return [i, a['LastName'] + ' ' + a['ForeName']]
                elif a['LastName'].lower() == lastname.lower():
                    return [i, a['LastName'] + ' ' + a['ForeName'] + ' (' + a['Initials'] + ')']
            elif 'Initials' in a:
                if a['LastName'] == lastname and initials in a['Initials']:
                    return [i, a['LastName'] + ' ' + a['Initials']]
                
def search(query):
    Entrez.email = 'your.email@example.com'
    handle = Entrez.esearch(db='pubmed', 
                            sort='relevance', 
                            retmax='2000',
                            retmode='xml', 
                            term=query)
    results = Entrez.read(handle)
    return results

def searchHutchAuthor(author):
    query = "Fred Hutch*[Affiliation] AND %s[Author]" % author
    #query = "%s[Author]" % author
    Entrez.email = 'your.email@example.com'
    handle = Entrez.esearch(db='pubmed', 
                            sort='relevance', 
                            retmax='2000',
                            retmode='xml', 
                            term=query)
    results = Entrez.read(handle)
    return results

def fetch_details(id_list):
    ids = ','.join(id_list)
    Entrez.email = 'your.email@example.com'
    handle = Entrez.efetch(db='pubmed',
                           retmode='xml',
                           id=ids)
    results = Entrez.read(handle)
    return results


    #pgpass = os.getenv('PGPASSFILE', os.path.expanduser('~/.pgpass'))
    #if not os.path.exists(pgpass):
        #print('You need to create file ~/.pgpass that contains at least one line:')
        #print('hostname:port:database:username:password')
        #print('and has restricted permissions: chmod 600 ~/.pgpass')
        #print('Also please check https://www.postgresql.org/docs/current/static/libpq-pgpass.html')
        #return False
        
    ##args.dsn == 'postgresql://dirk@mydb:32063/petersen'
    ##args.csvfile = '/home/petersen/sc/data/slurm_jobs.csv'
    
    #if not args.dsn.startswith('postgresql://'):
        #dl = args.dsn.split(':')
        #args.dsn = 'postgresql://%s@%s:%s/%s' % (dl[3], dl[0], dl[1], dl[2])
    
    #try:
        #conn = psycopg2.connect(args.dsn)
        #cur = conn.cursor()
    #except (Exception, psycopg2.DatabaseError) as error:
        #print('Database error:', error)
        #return False

    #with open(args.csvfile, 'rb') as fh:        
        #table_set = CSVTableSet(fh)
        #row_set = table_set.tables[0]
        ##print row_set.sample.next()
        #offset, headers = headers_guess(row_set.sample)
        #row_set.register_processor(headers_processor(headers))
        #row_set.register_processor(offset_processor(offset + rowtocheck))
        #types = type_guess(row_set.sample, strict=True)

    #myd = dict (zip (headers, types))
    #print("\nDetected columns & types:\n", myd, '\n')
    
    #table = os.path.splitext(os.path.basename(args.csvfile))[0]
    #table = table.replace('-','_')
    #table = table.replace(' ','_')
    #create_sql = "CREATE TABLE %s (" % table
    #idh = 0
    #for h in headers:
        #myt = "TEXT"
        #if str(types[idh]) == 'Integer':
            #myt = 'BIGINT'
        #elif str(types[idh]) == 'Bool':
             #myt = 'BIGINT'
        #elif str(types[idh]) == 'Decimal':
             #myt = 'DECIMAL'
        
        #create_sql += "%s %s, " % (h,myt)
        #idh += 1
    #create_sql = create_sql[:-2] + ');'

    #print("\ncreating postgres table '%s':\n" % table, create_sql, '\n')
    #try:
        #if args.overwrite:
            #drop_sql = 'DROP TABLE IF EXISTS %s' % table
            #cur.execute(drop_sql)
            #conn.commit()
        #cur.execute(create_sql)
        #conn.commit()
    #except (Exception, psycopg2.DatabaseError) as error:
        #print('Database error:', error)
        #sys.exit()

    #print("\nloading data .... ")

    #with open(args.csvfile, 'rb') as fh:
        #sample_text = ''.join(str(fh.readline()) for x in range(3))
        #try:
            #dialect = csv.Sniffer().sniff(sample_text)
            #if dialect.delimiter == 't':
                #delim = '\t'
            #else:
                #delim = dialect.delimiter            
        #except:
            #delim = ","
        #copy_sql = "COPY %s FROM stdin WITH CSV HEADER DELIMITER as '%s'" % \
                   #(table, delim)        
        #try:
            #cur.copy_expert(sql=copy_sql, file=fh)
            #conn.commit()
            #cur.close()
        #except (Exception, psycopg2.DatabaseError) as error:
            #print('Database error:', error)
            
    #print('Done !')


def parse_arguments():
    """
    Gather command-line arguments.
    """
    parser = argparse.ArgumentParser(prog='pubmed',
        description='a tool for quickly searching ' + \
        'pubmed publications per hutch author')
    parser.add_argument('author', action='store', 
        help='Please enter search as "Doe J" or "Doe John" ' + \
         '!')
    parser.add_argument('sinceyear', action='store', nargs='?', default='',  
        help=' search for authorship since year ' + \
         '!')  
    #parser.add_argument('dsn', action='store', 
        #help='postgres connection string, format postgresql://username@hostname:port/database ' + \
         #'or ~/.pgpass style credentials such as hostname:port:database:username')
    #parser.add_argument('csvfile', action='store', 
        #help='csv file you want to upload to postgres ' + \
            #'the delimiter can be a tab, pipe or a comma')
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