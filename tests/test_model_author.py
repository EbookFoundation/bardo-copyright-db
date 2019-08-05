from model.author import Author


class TestModelAuthor(object):
    def test_authorCreate(self):
        testAuthor = Author()
        testAuthor.name = 'Tester'
        testAuthor.primary = True

        assert str(testAuthor) == '<Author(name=Tester, primary=True)>'
