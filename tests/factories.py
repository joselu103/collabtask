# tests/factories.py
import uuid

import factory

from src.organizations.models import Organization
from src.users.models import User
from src.users.security import hash_password


class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.LazyFunction(uuid.uuid4)
    email = factory.Faker("email")
    username = factory.Faker("user_name")
    hashed_password = factory.LazyAttribute(lambda a: hash_password(a.email))
    is_active = True


class OrganizationFactory(factory.Factory):
    class Meta:
        model = Organization

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Faker("company")
    slug = factory.LazyAttribute(lambda a: "-".join(a.name.lower().split()))
