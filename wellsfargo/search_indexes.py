from haystack import indexes
from .models import AccountOwner


class AccountOwnerAutocompleteIndex(indexes.SearchIndex, indexes.Indexable):
    user_id = indexes.IntegerField(model_attr='pk', indexed=False, stored=True)
    username = indexes.CharField(model_attr='username', indexed=False, stored=True)
    first_name = indexes.CharField(model_attr='first_name', indexed=False, stored=True)
    last_name = indexes.CharField(model_attr='last_name', indexed=False, stored=True)
    email = indexes.CharField(model_attr='email', indexed=False, stored=True)
    text = indexes.EdgeNgramField(
        document=True,
        use_template=True,
        template_name='search/indexes/wellsfargo/accountowner_text.txt')

    def get_model(self):
        return AccountOwner

    def index_queryset(self, using=None):
        return self.get_model().objects.all()
