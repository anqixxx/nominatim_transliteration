import pytest
from src.normalization import parse_languages

def test_parsing_en():
    """ Base HTML Header Parsing test to see if it can properly concatanate and 
        extract the proper naming conventions

        Checks if the prototype can differentiate between English Variants
    """
    test_header = "en-CA,en-GB;q=0.9,en-US;q=0.8,en;q=0.7"
    output = parse_languages(test_header)
    assert output == ['en']


def test_parsing_zh():
    """ Base HTML Header Parsing test to see if it can properly concatanate and 
        extract the proper naming conventions

        Checks if the prototype can differentiate between Chinese Variants
    """
    test_header = "zh;q=0.9,zh-cn;q=0.8,zh-Hans-CN;q=0.7"
    output = parse_languages(test_header)
    assert output == ['zh-Hans', 'zh-Hant', 'yue']


def test_parsing_zh_en():
    """ Base HTML Header Parsing test to see if it can properly concatanate and 
        extract the proper naming conventions

        Checks if the prototype can differentiate between Chinese Variants and English Variants
    """
    test_header = "zh;q=0.4, en-US, zh-cn;q=0.8,zh-Hans-CN;q=0.7, en-UK;q=0.1"
    output = parse_languages(test_header)
    assert output == ['en', 'zh-Hans', 'zh-Hant', 'yue']
