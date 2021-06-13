import datetime
from fabrikApi import models


def test_defaultobject_mixin_by_assembly():
    earlier = datetime.datetime(2010, 1, 1, 0, 0, 0)
    later = datetime.datetime(2040, 1, 1, 0, 0, 0)

    assembly = models.DBAssembly(title="testdigikon30", identifier="digikon30", caption="Digikon2030")
    assert assembly.identifier is not None

    # initialize Default Values
    assembly.deleted = False
    assembly.disabled = False
    assembly.date_end = None
    assembly.date_start = None

    assert assembly.is_active is True

    # Disabling/Enabling
    assembly.disable()
    assert assembly.disabled is True
    assert assembly.is_active is False

    assembly.enable()
    assert assembly.disabled is False
    assert assembly.is_active is True

    # Deleting objects
    assembly.delete()
    assert assembly.deleted is True
    assert assembly.is_active is False
    assembly.deleted = False
    assert assembly.is_active is True

    # date end
    assembly.date_end = earlier
    assert assembly.is_active is False
    assembly.date_end = later
    assert assembly.is_active is True

    # date start
    assembly.date_start = later
    assert assembly.is_active is False
    assembly.date_start = earlier
    assert assembly.is_active is True


def test_progressionobject_mixin_by_assembly_progression():
    earlier = datetime.datetime(2010, 1, 1, 0, 0, 0)

    assemblyprog = models.DBAssemblyProgression(user_id=1, assembly_id=1)
    assert assemblyprog.user_id is not None
    assert assemblyprog.assembly_id is not None

    # initialize Default Values
    assemblyprog.completed = False
    # assemblyprog.locked = False
    assemblyprog.date_initiated = None
    
    assert assemblyprog.is_active == True

    # Quitting (by user)
    assemblyprog.complete()
    assert assemblyprog.comleted is True
    assert assemblyprog.is_active == False
    assemblyprog.completed = False
    assert assemblyprog.is_active == True

    # SKIPPING (by admin)
    assemblyprog.lock()
    assert assemblyprog.skipped is True
    assert assemblyprog.is_active == False
    # assemblyprog.locked = False
    assert assemblyprog.is_active == True

    # date inializing date
    assemblyprog.date_initiated = earlier
    assert assemblyprog.is_active == True
    assemblyprog.date_initiated = None
    assert assemblyprog.is_active == True
    # assert assemblyprog.status == models.DBAssemblyProgression.STATUS_ASSIGNED
