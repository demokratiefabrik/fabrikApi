# import datetime
from fabrikApi import models


def test_assembly():
    # earlier = datetime.datetime(2010, 1, 1, 0, 0, 0)
    # later = datetime.datetime(2040, 1, 1, 0, 0, 0)

    # def __init__(self, title="",
    #              identifier="", caption="")
    assembly = models.DBAssembly(title="testdigikon30", identifier="digikon30", location="Digikon2030")
    assert assembly.identifier is not None
