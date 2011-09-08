
"""
populate.py: Populate the Beta Testers database with a bunch of values
"""

from uuid import uuid4

from actions import User, Device, Build, Platform, Carrier

def populate():
    for obj in Device.all() + User.all() + Build.all() + Platform.all() + Carrier.all():
        obj.destroy()

    carrier = Carrier()
    carrier.name = 'AT&T'
    carrier.identifier = 'att'
    carrier.save()

    platform = Platform()
    platform.name = 'Android'
    platform.identifier = 'android'
    platform.owner_email = 'android@localhost'
    platform.save()

    platform = Platform()
    platform.name = 'Windows Phone 7'
    platform.identifier = 'wp7'
    platform.owner_email = 'wp7@localhost'
    platform.save()

    platform = Platform()
    platform.name = 'iOS'
    platform.identifier = 'ios'
    platform.owner_email = 'ios@localhost'
    platform.save()

    build = Build()
    build.build_number = '1.0'
    build.platform = platform
    build.classification = 'official'
    build.save()

    beta_build = Build()
    beta_build.build_number = '1.1beta'
    beta_build.platform = platform
    beta_build.classification = 'beta'
    beta_build.save()
    
    user = User()
    user.name = 'User 1'
    user.email = 'user1@localhost'
    user.save()

    device = Device()
    device.owner = user
    device.unique_identifier = str(uuid4())
    device.current_build = build
    device.carrier = carrier
    device.platform = platform
    device.save()

    for i in range(20):
        build = Build()
        build.build_number = '1.1.' + str(i) + 'dev'
        build.platform = platform
        build.classification = 'rolling'
        build.save()

    for i in range(100):
        device = Device()
        device.owner = user
        device.unique_identifier = str(uuid4())
        device.current_build = beta_build
        device.carrier = carrier
        device.platform = platform
        device.save()

    for i in range(100):
        user = User()
        user.email = str(uuid4()) + '@localhost'
        user.save()

        device = Device()
        device.owner = user
        device.unique_identifier = str(uuid4())
        device.current_build = beta_build
        device.carrier = carrier
        device.platform = platform
        device.save()

if __name__ == '__main__': populate()
