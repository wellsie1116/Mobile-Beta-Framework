import unittest

from actions import User, Device, Build, Platform

def destroy_everything():
    for db_object in Device.all() + User.all() + Build.all() + Platform.all():
        db_object.destroy()

class TestUserModel(unittest.TestCase):

    def setUp(self):
        destroy_everything()

    def test_user_smoke_test(self):
        user = User()
        user.name = 'Smoke Test'
        user.save()

    def test_user_attributes(self):
        user = User(name='Attributes Test', email='attributestest@localhost')
        user.save()

        user = User.from_email(user.email)
        self.assertEquals(user.name, user.name)
        self.assertEquals(user.email, user.email)

    def test_user_verification_code(self):
        user = User(name='Verification Code Test', email='verificationcodetest@localhost')
        user.save()

        user = User.from_email(user.email)
        self.assertTrue(user.verification_code == user.verification_code)

    def test_user_verify(self):
        user = User(name='Verify Test', email='verifytest@localhost')
        user.save()

        user = User.from_email(user.email)
        self.assertFalse(user.verified)
        user.verify(user.verification_code)
        user.save()

        user = User.from_email(user.email)
        self.assertTrue(user.verified)

    def test_user_name_change_code(self):
        user = User(name='Name Change Code Test', email='namechangecodetest@localhost')
        user.save()

        user = User.from_email(user.email)
        self.assertTrue(user.name_change_code == user.name_change_code)

    def test_user_change_name(self):
        user = User(name='Name Change Test', email='namechangetest@localhost')
        user.save()

        user = User.from_email(user.email)
        user.changeName(user.name_change_code, 'New Name Change Test')
        user.save()

        user = User.from_email(user.email)
        self.assertEquals(user.name, 'New Name Change Test')

    def test_user_retrieval(self):
        user = User()
        user.email = 'testuserretrieval@localhost'
        user.save()

        new_user = User.from_verification_code(user.verification_code)
        self.assertEquals(new_user.email, user.email)

        new_user = User.from_name_change_code(user.name_change_code)
        self.assertEquals(new_user.email, user.email)

    def tearDown(self):
        destroy_everything()


class TestDeviceModel(unittest.TestCase):
    
    def setUp(self):
        destroy_everything()
        self.default_user = User()
        self.default_user.name = 'Default User'
        self.default_user.email = 'defaultuser@localhost'

        self.default_platform = Platform()
        self.default_platform.name = 'Default Platform'
        self.default_platform.identifier = 'default'
        self.default_platform.owner_email = 'defaultowner@localhost'
        self.default_platform.save()

        self.default_build = Build()
        self.default_build.platform = self.default_platform
        self.default_build.build_number = '1.0.0'
        self.default_build.classification = 'official'
        self.default_build.save()

        self.default_device = Device()
        self.default_device.unique_identifier = 'default_device_unique_identifier'
        self.default_device.owner = self.default_user
        self.default_device.current_build = self.default_build
        self.default_device.platform = self.default_platform
        self.default_device.save()

        self.default_user.devices.append(self.default_device)
        self.default_user.save()

    def test_device_smoke_test(self):
        device = Device()
        device.unique_identifier = 'test_device_smoke_test'
        device.owner = self.default_user
        device.current_build = self.default_build
        device.platform = self.default_platform
        device.save()

    def test_device_attributes(self):
        device = Device()
        device.unique_identifier = 'test_device_attributes'
        device.model = 'test_device_attributes_model'
        device.operating_system = 'test_device_attributes_os_version'
        device.additional_info = 'test_device_attributes_additional_info'
        device.owner = self.default_user
        device.current_build = self.default_build
        device.platform = self.default_platform
        device.save()

        new_device = Device.from_unique_identifier(device.unique_identifier)
        self.assertEquals(new_device.model, device.model)
        self.assertEquals(new_device.operating_system, device.operating_system)
        self.assertEquals(new_device.additional_info, device.additional_info)

    def test_device_owner_relation(self):
        user = User()
        user.email = 'tesdevicerelations@localhost'
        user.save()

        device = Device()
        device.unique_identifier = 'test_device_relations'
        device.owner = user
        device.current_build = self.default_build
        device.platform = self.default_platform
        device.save()

        device = Device.from_unique_identifier(device.unique_identifier)
        self.assertEquals(device.owner.email, user.email)

    def test_device_retrieval(self):
        device = Device()
        device.operating_system = 'test_device_retrieval_os'
        device.unique_identifier = 'test_device_retrieval'
        device.owner = self.default_user
        device.current_build = self.default_build
        device.platform = self.default_platform
        device.save()

        new_device = Device.from_auth_token(device.auth_token)
        self.assertEquals(new_device.operating_system, device.operating_system)

        new_device = Device.from_verification_code(device.verification_code)
        self.assertEquals(new_device.operating_system, device.operating_system)

    def tearDown(self):
        destroy_everything()

if __name__ == '__main__':
    unittest.main()
