# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # The extension, width, and height fields of the Profile model are
        # removed, but we want this migration to be non-destructive. Thus, the
        # columns are simply altered to allow null values.
        db.alter_column('edxval_profile', 'width', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, default=1))
        db.alter_column('edxval_profile', 'extension', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, default='mp4'))
        db.alter_column('edxval_profile', 'height', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, default=1))

        # On MySQL, attempts to insert new model instances (which lack values
        # for the removed fields) results in a warning about a lack of a default
        # value. Because django does not have a mechanism for specifying the
        # default value in the database, we must manually alter the table here.
        if db.backend_name == 'mysql':
            db.execute("ALTER TABLE edxval_profile MODIFY extension VARCHAR(10) DEFAULT 'mp4'")
            db.execute("ALTER TABLE edxval_profile MODIFY width INT(10) UNSIGNED DEFAULT 1")
            db.execute("ALTER TABLE edxval_profile MODIFY height INT(10) UNSIGNED DEFAULT 1")

    def backwards(self, orm):
        # Remove database-level defaults applied above
        if db.backend_name == 'mysql':
            db.execute("ALTER TABLE edxval_profile MODIFY extension VARCHAR(10)")
            db.execute("ALTER TABLE edxval_profile MODIFY width INT(10) UNSIGNED")
            db.execute("ALTER TABLE edxval_profile MODIFY height INT(10) UNSIGNED")

        # Because the forward migration is non-destructive and simply alters the
        # extension, width, and height columns of the Profile model to allow
        # null values, values from before the forward migration will still be
        # present in the table. The backward migration restores the non-null
        # restriction to each column and provides dumb defaults for any profiles
        # that were created between the application of the forward migration and
        # backward migration.
        db.alter_column('edxval_profile', 'width', self.gf('django.db.models.fields.PositiveIntegerField')(default=1))
        db.alter_column('edxval_profile', 'extension', self.gf('django.db.models.fields.CharField')(default='mp4', max_length=10))
        db.alter_column('edxval_profile', 'height', self.gf('django.db.models.fields.PositiveIntegerField')(default=1))

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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'profile_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
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
