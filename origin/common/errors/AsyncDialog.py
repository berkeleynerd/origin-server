# coding=utf-8

#
# An asynchronous dialog is required to continue
#
class AsyncDialog(Exception):

    def __init__(self, dialog, *args):

        self.dialog = dialog
        self.args = args