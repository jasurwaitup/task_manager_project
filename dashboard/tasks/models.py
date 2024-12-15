from django.db import models

# Create your models here.
class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ]
    name = models.CharField(max_length=200)
    description = models.TextField(max_length=2000)
    users = models.TextField(max_length=1000)
    started_on = models.CharField(max_length=200)
    ends_on = models.CharField(max_length=200)
    number_of_files = models.IntegerField(max_length=10)
    completeness = models.FloatField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name
