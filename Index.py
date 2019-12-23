class Index:

    def __init__(self):
        self.frequency = 0
        self.index_dic = {}

    def add(self, doc_id, position):

        if doc_id in self.index_dic:
            self.index_dic[doc_id].append(position)
        else:
            self.index_dic[doc_id] = [position]
            self.frequency += 1
