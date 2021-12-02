from kiwi_keg.annotated_mapping import AnnotatedMapping, AnnotatedPrettyPrinter


class TestAnnotatedMapping:
    def setup(self):
        self.mapping = AnnotatedMapping(
            {
                'some_key': 'foo',
                '__hidden_key__': 'bar'
            }
        )

    def test_iteration(self):
        for i in self.mapping:
            assert not i.startswith('__')

    def test_all_items(self):
        items = list(self.mapping.all_items())
        assert items == [('some_key', 'foo'), ('__hidden_key__', 'bar')]

    def test_all_keys(self):
        keys = list(self.mapping.all_keys())
        assert keys == ['some_key', '__hidden_key__']

    def test_dict_conv(self):
        self.mapping['new_dict'] = {'new_key': 'baz'}
        assert isinstance(self.mapping['new_dict'], AnnotatedMapping)

    def test_repr(self):
        assert repr(self.mapping) == "AnnotatedMapping{'some_key': 'foo', '__hidden_key__': 'bar'}"

    def test_str(self):
        assert str(self.mapping) == "{'some_key': 'foo', '__hidden_key__': 'bar'}"

    def test_update(self):
        self.mapping.update({'__hidden_key__': 'new_bar'})
        assert self.mapping == AnnotatedMapping(
            {
                'some_key': 'foo',
                '__hidden_key__': 'new_bar'
            }
        )

    def test_pprint(self, capsys):
        ap = AnnotatedPrettyPrinter()
        ap.pprint(self.mapping)
        cap = capsys.readouterr()
        assert cap.out == "{'__hidden_key__': 'bar', 'some_key': 'foo'}\n"
