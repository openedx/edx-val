# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Video.created'
        db.add_column('edxval_video', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, default=datetime.datetime(2014, 11, 17, 0, 0), blank=True),
                      keep_default=False)

        # Adding field 'Video.status'
        db.add_column('edxval_video', 'status',
                      self.gf('django.db.models.fields.CharField')(default='File Complete', max_length=255, db_index=True),
                      keep_default=False)


        # Changing field 'Video.edx_video_id'
        db.alter_column('edxval_video', 'edx_video_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100))

        # Changing field 'EncodedVideo.url'
        db.alter_column('edxval_encodedvideo', 'url', self.gf('django.db.models.fields.CharField')(max_length=200))

    def backwards(self, orm):
        # Deleting field 'Video.created'
        db.delete_column('edxval_video', 'created')

        # Deleting field 'Video.status'
        db.delete_column('edxval_video', 'status')


        # Changing field 'Video.edx_video_id'
        db.alter_column('edxval_video', 'edx_video_id', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True))

        # Changing field 'EncodedVideo.url'
        db.alter_column('edxval_encodedvideo', 'url', self.gf('django.db.models.fields.URLField')(max_length=200))

    models = {
        'edxval.coursevideo': {
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
            'url': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
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
            'client_video_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '255', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'duration': ('django.db.models.fields.FloatField', [], {}),
            'edx_video_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        }
    }

    complete_apps = ['edxval']