#!usr/bin/python
'''matcherrors contains classes for MatchBot-specific errors.

Error -- base class for exceptions
MatchError -- match cannot be found
'''

class Error(Exception):
    '''base class for exceptions in this module'''
    pass

class MatchError(Error):
    ''' Exception raised when a match cannot be found    

    Attributes:
        msg -- explanation of the error

    '''
    def __init__(self, msg = 'No match found'):
        self.msg = msg
