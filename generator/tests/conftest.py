from datetime import date

import pytest

from hr_generator import GeneratorConfig, generate
from hr_generator.stats import Stats

AS_OF = date(2026, 9, 30)


@pytest.fixture(scope="session")
def dataset():
    return generate(GeneratorConfig(seed=42, as_of_date=AS_OF))


@pytest.fixture(scope="session")
def stats(dataset):
    return Stats(dataset)


@pytest.fixture(scope="session")
def tables(dataset):
    return dataset.tables
