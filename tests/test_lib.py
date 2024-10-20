from youbet import lib
import random
import pytest


def test_generate_password():
    length = random.randint(5, 10)
    password = lib.generate_password(length)
    assert len(password) == length


def test_generate_salt():
    salt = lib.generate_salt()
    assert len(salt) == 32


def test_hash_password():
    password = lib.generate_password()
    salt = lib.generate_salt()
    password_hash, salt = lib.hash_password(password, salt, as_str=True)
    assert lib.verify_password(password_hash, salt, password)


def test_hash_length():
    password = lib.generate_password(random.randint(1, 100))
    salt = lib.generate_salt()
    password_hash, salt = lib.hash_password(password, salt)
    assert len(password_hash) == 128
    assert len(salt) == 32


def test_hash_as_str():
    password = lib.generate_password()
    password_hash, salt = lib.hash_password(password, as_str=True)
    assert type(password_hash) == str
    assert type(salt) == str


def test_salt_as_str():
    salt = lib.generate_salt()
    result = lib.bytes_to_str(salt)
    assert type(result) == str
    assert lib.str_to_bytes(result) == salt


def test_byte_conversion():
    data = "helloWORLD123!@#"
    as_bytes = lib.coerce_to_bytes(data)
    assert type(as_bytes) == bytes

    as_str = lib.coerce_to_str(as_bytes)
    assert type(as_str) == str

    assert data == as_str


def test_all_password_characters():
    password = ''.join([chr(x) for x in range(48, 123)])
    assert lib.validate_password(password)
    pwd, salt = lib.hash_password(password, as_str=True)
    assert lib.verify_password(pwd, salt, password)


VALIDATE_ODDS_DATA = [
    ("1:1", True),
    ("2:1", True),
    ("1:2", True),
    ("1.5:1", True),
    ("1.5:2.65312", True),
    ("a", False),
    ("a:1", False),
    ("1:a", False),
]

@pytest.mark.parametrize(["odds", "expected_result"], VALIDATE_ODDS_DATA)
def test_validate_odds(odds, expected_result):
    assert lib.validate_odds(odds) is expected_result


SOLVE_ODDS_DATA = [
    (100, "1:1", 100, False),
    (100, "2:1", 200, False),
    (100, "4:2", 200, False),
    (100, "1:2", 50, False),
    (100, "1:1", 100, True),
    (100, "2:1", 50, True),
    (100, "4:2", 50, True),
    (100, "1:2", 200, True),
]

@pytest.mark.parametrize(["amount", "odds", "expected_result", "reverse"], SOLVE_ODDS_DATA)
def test_solve_odds(amount, odds, expected_result, reverse):
    assert lib.solve_odds(odds=odds, amount=amount, reverse_odds=reverse) == expected_result
    