from kiwi_keg.annotated_mapping import AnnotatedMapping, AnnotatedPrettyPrinter


class TestAnnotatedMapping:
    def setup_method(self):
        self.mapping = AnnotatedMapping(
            {
                'some_key': 'foo',
                '__hidden_key__': 'bar'
            }
        )

    def test_init_empty(self):
        am = AnnotatedMapping()
        assert am._mapping == {}

    def test_getitem(self):
        assert self.mapping['some_key'] == 'foo'

    def test_setitem_plain(self):
        self.mapping['another_key'] = 'baz'

    def test_setitem_dict(self):
        self.mapping['dict_key'] = {'key': 'value'}

    def test_delitem(self):
        del self.mapping['some_key']
        assert not self.mapping.get('some_key')

    def test_iteration(self):
        for i in self.mapping:
            assert not i.startswith('__')

    def test_len(self):
        assert len(self.mapping) == 2

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

    def test_update_dict(self):
        self.mapping.update({'__hidden_key__': 'new_bar'})
        assert self.mapping == AnnotatedMapping(
            {
                'some_key': 'foo',
                '__hidden_key__': 'new_bar'
            }
        )

    def test_update_annotated_mapping(self):
        self.mapping.update(AnnotatedMapping({'__hidden_key__': 'new_bar'}))
        assert self.mapping == AnnotatedMapping(
            {
                'some_key': 'foo',
                '__hidden_key__': 'new_bar'
            }
        )

    def test_to_plain_list(self):
        data = [1, 'a', AnnotatedMapping({'key': 'val', '__hidden_key__': 'hidden_val'})]
        assert self.mapping._to_plain(data) == [1, 'a', {'key': 'val'}]

    def test_to_plain_dict(self):
        assert self.mapping._to_plain(self.mapping) == {
            'some_key': 'foo'
        }

    def test_pprint(self, capsys):
        ap = AnnotatedPrettyPrinter()
        ap.pprint(self.mapping)
        cap = capsys.readouterr()
        assert cap.out == "{'__hidden_key__': 'bar', 'some_key': 'foo'}\n"
