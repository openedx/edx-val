# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Profile'
        db.create_table('edxval_profile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('profile_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('extension', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('width', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('height', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('edxval', ['Profile'])

        # Adding model 'Video'
        db.create_table('edxval_video', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('edx_video_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('client_video_id', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('duration', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('edxval', ['Video'])

        # Adding model 'CourseVideo'
        db.create_table('edxval_coursevideo', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('course_id', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('video', self.gf('django.db.models.fields.related.ForeignKey')(related_name='courses', to=orm['edxval.Video'])),
        ))
        db.send_create_signal('edxval', ['CourseVideo'])

        # Adding unique constraint on 'CourseVideo', fields ['course_id', 'video']
        db.create_unique('edxval_coursevideo', ['course_id', 'video_id'])

        # Adding model 'EncodedVideo'
        db.create_table('edxval_encodedvideo', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('file_size', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('bitrate', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('profile', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['edxval.Profile'])),
            ('video', self.gf('django.db.models.fields.related.ForeignKey')(related_name='encoded_videos', to=orm['edxval.Video'])),
        ))
        db.send_create_signal('edxval', ['EncodedVideo'])

        # Adding model 'Subtitle'
        db.create_table('edxval_subtitle', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('video', self.gf('django.db.models.fields.related.ForeignKey')(related_name='subtitles', to=orm['edxval.Video'])),
            ('fmt', self.gf('django.db.models.fields.CharField')(max_length=20, db_index=True)),
            ('language', self.gf('django.db.models.fields.CharField')(max_length=8, db_index=True)),
            ('content', self.gf('django.db.models.fields.TextField')(default='')),
        ))
        db.send_create_signal('edxval', ['Subtitle'])


    def backwards(self, orm):
        # Removing unique constraint on 'CourseVideo', fields ['course_id', 'video']
        db.delete_unique('edxval_coursevideo', ['course_id', 'video_id'])

        # Deleting model 'Profile'
        db.delete_table('edxval_profile')

        # Deleting model 'Video'
        db.delete_table('edxval_video')

        # Deleting model 'CourseVideo'
        db.delete_table('edxval_coursevideo')

        # Deleting model 'EncodedVideo'
        db.delete_table('edxval_encodedvideo')

        # Deleting model 'Subtitle'
        db.delete_table('edxval_subtitle')


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