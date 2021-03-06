from dockitcms.models import FilteredCollectionIndex, CollectionFilter, CollectionParam, FilteredModelIndex, ModelFilter, ModelParam, Collection, Application
from dockitcms import fields

from dockit import backends

from django.utils import unittest
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

class IndexTest(unittest.TestCase):
    def setUp(self):
        app = Application(name='test')
        app.save()
        self.application = app
    
    def create_test_collection(self, **kwargs):
        active_mixins = kwargs.pop('active_mixins', [])
        params = {'application':self.application,
                  'key':'testcollection',
                  'title':'Test Collection',
                  'fields':[fields.CharField(name='title', null=False, blank=True),
                            fields.BooleanField(name='published', blank=True),
                            fields.BooleanField(name='featured', blank=True),],}
        params.update(kwargs)
        collection = Collection(**params)
        collection.save()
        
        document = collection.get_document()
        document = collection.register_collection()
        assert 'published' in document._meta.fields, str(document._meta.fields.keys()) + str(collection.fields)
        
        return collection
    
    def test_filtered_collection_index(self):
        collection = self.create_test_collection()
        index = FilteredCollectionIndex(collection=collection,
                                        inclusions=[CollectionFilter(key='featured', value='true', operation='exact', value_type='boolean')],
                                        exclusions=[CollectionFilter(key='published', value='false', operation='exact', value_type='boolean')],
                                        parameters=[CollectionParam(key='title', operation='exact')],)
        index.save()
        query_hash = index.get_index()._index_hash()
        collection_name = collection.get_document()._meta.collection
        
        #assert the backend was notified of the index
        self.assertTrue(query_hash in backends.INDEX_ROUTER.registered_querysets[collection_name], str(backends.INDEX_ROUTER.registered_querysets[collection_name]))
        
        document = collection.get_document()
        document.objects.all().delete() #why did i get 2?
        
        doc = document(title='foo', published=True, featured=True)
        doc.save()
        self.assertEqual(document.objects.all().count(), 1)
        
        query = index.get_index()
        msg = str(query.queryset.query.queryset.query)
        self.assertEqual(query.count(), 1, msg)
    
    def test_filtered_model_index(self):
        index = FilteredModelIndex(model=ContentType.objects.get_for_model(User),
                                   inclusions=[ModelFilter(key='is_staff', value='true', operation='exact', value_type='boolean')],
                                   exclusions=[ModelFilter(key='is_active', value='false', operation='exact', value_type='boolean')],
                                   parameters=[ModelParam(key='username', operation='exact')],)
        index.save()
        index.get_index().count()

