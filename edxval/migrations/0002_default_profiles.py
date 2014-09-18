# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        orm.Profile.objects.bulk_create([
            orm.Profile(profile_name="desktop_mp4",  width=1280, height= 720, extension="mp4"),
            orm.Profile(profile_name="desktop_webm", width=1280, height= 720, extension="webm"),
            orm.Profile(profile_name="mobile_high",  width= 960, height= 540, extension="mp4"),
            orm.Profile(profile_name="mobile_low",   width= 640, height= 360, extension="mp4"),
            orm.Profile(profile_name="youtube",      width=1920, height=1080, extension="mp4"),
        ])
        # Note: Remember to use orm['appname.ModelName'] rather than "from appname.models..."

    def backwards(self, orm):
        "Write your backwards methods here."
        orm.Profile.objects.filter(
            profile_name__in=["desktop_mp4", "desktop_webm", "mobile_high", "mobile_low", "youtube"]
        ).delete()

    models = {
        'edxval.coursevideos': {
            'Meta': {'unique_together': "(('course_id', 'video'),)", 'object_name': 'CourseVideo'},
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'courses'", 'to': "orm['edxval.Video']"})
        },
        'edxval.encodedvideo': {
            'Meta': {'object_name': 'EncodedVideo'},
            'bitrate': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'file_size': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'profile': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['edxval.Profile']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'encoded_videos'", 'to': "orm['edxval.Video']"})
        },
        'edxval.profile': {
            'Meta': {'object_name': 'Profile'},
            'extension': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'height': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'profile_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'width': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'edxval.subtitle': {
            'Meta': {'object_name': 'Subtitle'},
            'content': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'fmt': ('django.db.models.fields.CharField', [], {'max_length': '20', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '8', 'db_index': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'subtitles'", 'to': "orm['edxval.Video']"})
        },
        'edxval.video': {
            'Meta': {'object_name': 'Video'},
            'client_video_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'duration': ('django.db.models.fields.FloatField', [], {}),
            'edx_video_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['edxval']
    symmetrical = True
