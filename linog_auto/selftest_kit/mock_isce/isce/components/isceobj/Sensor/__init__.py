"""MOCK isceobj.Sensor (linog_auto self-test only)."""


def createSensor(name):
    if name != 'ALOS_SLC':
        raise ValueError('mock ISCE has ALOS_SLC only, not %s' % name)
    from isceobj.Sensor.ALOS_SLC import ALOS_SLC
    return ALOS_SLC()
