from django.db import models


class Msg(models.Model):
    msg_text = models.TextField(max_length=200)
    msg_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
       return '{} ({})'.format(self.msg_text, self.msg_time)
