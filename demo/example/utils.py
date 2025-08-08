from django.db.models import Func, FloatField


class MySqrt(Func):
    """
    A custom Django database function
    """
    function = 'SQRT'
    template = '%(function)s(%(expressions)s)'
    output_field = FloatField()
