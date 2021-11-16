import unittest

from jellyfin_alexa_skill.alexa.util import get_similarity


class TestSimilarity(unittest.TestCase):
    def test_similarity_empty(self):
        s1 = ""
        s2 = ""
        similarity = get_similarity(s1, s2)

        self.assertEqual(similarity, 1.0)

    def test_similarity(self):
        # same string
        with self.subTest():
            s1 = "Hello"
            similarity = get_similarity(s1, s1)

            self.assertEqual(similarity, 1.0)

        # everything different
        with self.subTest():
            s1 = "Hello"
            s2 = "abcd"
            similarity = get_similarity(s1, s2)

            self.assertEqual(similarity, 0.0)

        # one char is equal
        with self.subTest():
            s1 = "Test"
            s2 = "Hey"
            similarity = get_similarity(s1, s2)

            self.assertEqual(similarity, 2 * 1 / (len(s1) + len(s2)))

        # one word different
        with self.subTest():
            s1 = "Hello world"
            s2 = "Hello Alexa"
            similarity = get_similarity(s1, s2)

            self.assertEqual(similarity, 2 * 7 / (len(s1) + len(s2)))

        # space have no effect
        with self.subTest():
            s1 = "abc def"
            s2 = "ghi jkl"
            similarity = get_similarity(s1, s2)

            self.assertEqual(similarity, 0.0)

        # only special characters are equal, the punctuation or spaces have to be ignored
        with self.subTest():
            s1 = "abc def, gh & ij"
            s2 = "kl, mno & pqr"
            similarity = get_similarity(s1, s2)

            self.assertEqual(similarity, 0.0)

        # common song title pattern
        with self.subTest():
            s1 = "artist art, artist - song name name"
            s2 = "artist art, artist ft. artist two - song name name"
            similarity = get_similarity(s1, s2)

            self.assertEqual(similarity, 2 * 35 / (len(s1) + len(s2)))


if __name__ == '__main__':
    unittest.main()
