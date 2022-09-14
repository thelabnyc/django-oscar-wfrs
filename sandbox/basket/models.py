from oscar.apps.basket.abstract_models import AbstractBasket, AbstractLine
from oscarbluelight.mixins import BluelightBasketMixin, BluelightBasketLineMixin


class Basket(BluelightBasketMixin, AbstractBasket):
    pass


class Line(BluelightBasketLineMixin, AbstractLine):
    pass


from oscar.apps.basket.models import *  # noqa
