from sqlalchemy import Column, Integer
from sqlalchemy.orm.attributes import InstrumentedAttribute

from fabrikApi.models.meta import Base
from fabrikApi import models


def test_contenttree_mixin():
    """
    The mixins provides methods and foreign key to link third-party objects to an contenttree.
    """

    class DefaultModel(Base, models.contenttree.contenttreeMixin):

        __tablename__ = "testingmodel"
        id = Column(Integer, primary_key=True)
        pass

    newobject = DefaultModel
    assert newobject.id is not None
    assert newobject.contenttree_id is not None
    assert isinstance(newobject.contenttree_id, InstrumentedAttribute)
