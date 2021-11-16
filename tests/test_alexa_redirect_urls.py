import unittest

from jellyfin_alexa_skill.config import VALID_ALEXA_REDIRECT_URLS_REGEX


class TestAlexaRedirectUrls(unittest.TestCase):
    def test_valid_alexa_redirect_urls_regex_layla(self):
        with self.subTest():
            url = "https://layla.amazon.com/spa/skill/account-linking-status.html?vendorId=12345"
            valid = VALID_ALEXA_REDIRECT_URLS_REGEX.match(url)
            self.assertTrue(valid)

    def test_valid_alexa_redirect_urls_regex_pitangui(self):
        with self.subTest():
            url = "https://pitangui.amazon.com/spa/skill/account-linking-status.html?vendorId=12345"
            valid = VALID_ALEXA_REDIRECT_URLS_REGEX.match(url)
            self.assertTrue(valid)

    def test_valid_alexa_redirect_urls_regex_alexa_co_jp(self):
        with self.subTest():
            url = "https://alexa.amazon.co.jp/spa/skill/account-linking-status.html?vendorId=12345"
            valid = VALID_ALEXA_REDIRECT_URLS_REGEX.match(url)
            self.assertTrue(valid)

    def test_invalid_alexa_redirect_urls_regex(self):
        # wrong subdomain
        with self.subTest():
            url = "https://alexa.amazon.com/spa/skill/account-linking-status.html?vendorId=12345"
            valid = VALID_ALEXA_REDIRECT_URLS_REGEX.match(url)
            self.assertFalse(valid)

        # wrong tld
        with self.subTest():
            url = "https://alexa.amazon.ai/spa/skill/account-linking-status.html?vendorId=12345"
            valid = VALID_ALEXA_REDIRECT_URLS_REGEX.match(url)
            self.assertFalse(valid)

        # wrong tld
        with self.subTest():
            url = "https://alexa.amazon.ai/spa/skill/account-linking-status.html?vendorId=12345"
            valid = VALID_ALEXA_REDIRECT_URLS_REGEX.match(url)
            self.assertFalse(valid)

        # no vendor id
        with self.subTest():
            url = "https://pitangui.amazon.com/spa/skill/account-linking-status.html"
            valid = VALID_ALEXA_REDIRECT_URLS_REGEX.match(url)
            self.assertFalse(valid)

        # wrong path
        with self.subTest():
            url = "https://pitangui.amazon.com/random/path/test.html?vendorId=12345"
            valid = VALID_ALEXA_REDIRECT_URLS_REGEX.match(url)
            self.assertFalse(valid)


if __name__ == '__main__':
    unittest.main()
