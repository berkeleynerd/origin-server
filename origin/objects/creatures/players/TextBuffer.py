# coding=utf-8

#
# Player's output buffer. Output is organized into paragraphs to allow for later formatting.
#
class TextBuffer(object):

    class Paragraph(object):
        def __init__(self):
            self.lines = []

        def add(self, line):
            self.lines.append(line)

        def text(self):
            return "\n".join(self.lines) + "\n"

    def __init__(self):
        self.init()

    def init(self):
        self.paragraphs = []
        self.in_paragraph = False


    # Terminates a paragraph and begins a new one.
    def new_paragraph(self):
        if not self.in_paragraph:
            self.__new_paragraph()
        self.in_paragraph = False


    def __new_paragraph(self):
        p = TextBuffer.Paragraph()
        self.paragraphs.append(p)
        self.in_paragraph = True
        return p


    #
    # Write a line of text with a single space inserted between each line.
    # Text is minimally formatted for output as appropriate.
    #
    def print(self, line):

        if self.in_paragraph:
            p = self.paragraphs[-1]
        else:
            p = self.__new_paragraph()

        line = line.strip()
        p.add(line)


    def get_paragraphs(self, clear=True):
        paragraphs = [p.text() for p in self.paragraphs]
        if clear:
            self.init()
        return paragraphs