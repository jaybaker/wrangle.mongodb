import pymongo
import pandas as pd
import numpy as np
from ggplot import *
from datetime import datetime, timedelta

EPOCH = datetime(1970, 1, 1)
DT_FRMT = '%Y-%m-%dT%H:%M:%SZ' # ex. 2008-10-31T13:10:04Z

def month(timestamp):
    """ Given a timestamp, what ordinal month is it? """
    month_diff = timestamp.month - EPOCH.month
    year_diff  = timestamp.year - EPOCH.year
    diff = 12 * year_diff + month_diff
    return diff

def aggregate_by_month(coll):
    data = [x for x in coll.find()]
    index = [datetime.strptime(x['created']['timestamp'], DT_FRMT) for x in data]
    df = pd.DataFrame(dict(month=[month(x) for x in index], count=[1 for x in index]), index=index)
    month_count = df.groupby('month', as_index=False).aggregate(np.count_nonzero)
    print month_count
    print ggplot(aes(x='month', y='count'), data=month_count) + geom_bar(stat='identity') + labs(title='By Count') + ylab('Num Records')

def num_cities(coll):
    pipeline = [
        {'$match': {'address.city': {'$exists':1}}},
        {'$group': {'_id':'$address.city', 'count':{'$sum':1} }},
    ]
    results = coll.aggregate(pipeline)['result']
    print '%i different cities' % len(results)
    for doc in results:
        print doc


def main():
    client = pymongo.MongoClient()
    db = client.plano
    collection = db.osm
    #aggregate_by_month(collection)
    num_cities(collection)

def test():
    # testing boundary conditions on month, what month is it?
    assert(month(EPOCH) == 0)
    assert(month(EPOCH + timedelta(days=1)) == 0)
    assert(month(EPOCH + timedelta(days=365)) == 12)
    assert(month(EPOCH + timedelta(days=365+1)) == 12)
    assert(month(EPOCH + timedelta(days=365+32)) == 13)

if __name__ == '__main__':
    main()
    #test()
