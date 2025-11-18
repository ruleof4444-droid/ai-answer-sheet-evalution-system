from pymongo import MongoClient

m = MongoClient('mongodb://localhost:27017')
db = m['schema_db']
col = db['schema_extracted_answers']

print('Total schema records:', col.count_documents({}))
rec = col.find_one()
if rec:
    print('\nRecord keys:', list(rec.keys()))
    print('examId:', rec.get('examId'))
    print('fileName:', rec.get('fileName'))
    print('\nAll values:')
    for k, v in rec.items():
        if k != '_id':
            print(f'  {k}: {v}')
else:
    print('No records found')
