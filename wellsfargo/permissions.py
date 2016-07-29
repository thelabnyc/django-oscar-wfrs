from oscarapicheckout.permissions import PaymentMethodPermission


class IsAuthenticated(PaymentMethodPermission):
    def is_permitted(self, request=None, user=None):
        return (user and user.is_authenticated())
