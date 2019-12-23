class Highlight:
    def __init__(self, word, is_highlight):
        self.word = word
        self.is_highlight = is_highlight

    def highlight(self):
        self.is_highlight = True
