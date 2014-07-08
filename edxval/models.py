from django.db import models

class Video(models.Model):
    edx_uid = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255, db_index=True)
    #TODO Creation date
    #TODO modified date

class Profile(models.Model):
    title = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=50, unique=True)
    ext_name = models.CharField(max_length=50)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    bitrate = models.PositiveIntegerField()

class Encoding(models.Model):
    video = models.ForeignKey(Video)
    profile = models.ForeignKey(Profile)
    file_size = models.PositiveIntegerField()
    duration = models.FloatField()



