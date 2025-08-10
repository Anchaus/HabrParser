import pymongo

class MongoConnector():
    def __init__(self):
        self.connection = pymongo.MongoClient("localhost", 27017)
        self.data_base = self.connection.habr_negative
        self.collection = self.data_base.articles

    def new_docs(self, docs : list):
        self.collection.insert_many(docs)

    def search(self, attributes):
        result = self.collection.find(attributes)
        return list(result)


if __name__ == '__main__':
    connection1 = MongoConnector()

    output = connection1.search({"author": 'Mike'})
    print(output)

