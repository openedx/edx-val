#!/usr/bin/env python
"""
Migration script for existing courses.
This script exports courses from studio, looking for videos in the xml and associating them with
videos already in VAL -- using either filename convention or looking up youtube ids in VAL.
Then it (optionally) uploads the migrated course to studio.
"""
import tarfile
import sys
from xml.etree.cElementTree import fromstring, tostring
import io
import os.path
import getpass
import requests
import argparse
import pprint
import time
import logging


class MissingVideo(Exception):
    pass


class Migrator(object):
    def __init__(self,
            course_id=None,
            studio_url='https://studio.edx.org',
            lms_url='https://courses.edx.org'):
        self.studio_url = studio_url
        self.val_url = '{}/api/val/v0'.format(self.studio_url)
        self.lms_url = lms_url
        self.course_id = course_id
        self.sess = requests.Session()
        self.course_vids = []
        self.log = logging.getLogger('migrator')

    def get_csrf(self, url):
        """
        return csrf token retrieved from the given url
        """
        response = self.sess.get(url)
        csrf = response.cookies['csrftoken']
        return {'X-CSRFToken': csrf, 'Referer': url}


    def get_course_val_videos(self, course_id=None):
        """
        Retrieve VAL info for this course
        """
        course_id = course_id or self.course_id
        url = self.val_url + '/videos/'
        self.log.debug('Getting VAL info from %s', url)
        videos = self.sess.get(url, params={'course': self.course_id}).json()
        # HACK for messed up ids
        if self.course_id == 'MITx/6.002x_4x/3T2014' and not videos:
            videos = self.get_course_val_videos('MITx/6.002_4x/3T2014')
        self.course_vids = videos

    def match_video(self, youtube_id=None, client_id=None):
        """
        Find a matching VAL video based on either youtube id or 'client id'
        """
        for vid in self.course_vids:
            if youtube_id:
                for enc in vid['encoded_videos']:
                    if enc['profile'] == 'youtube' and enc['url'].strip() == youtube_id:
                        return vid['edx_video_id']
            if vid['client_video_id'] == client_id:
                return vid['edx_video_id']

    def import_tgz(self, tgz, course_id=None):
        """
        Upload tgz to studio
        """
        course_id = course_id or self.course_id
        url = '{}/import/{}'.format(self.studio_url, course_id)
        self.log.info('Importing {} to {} from {}'.format(course_id, url, tgz))
        headers = self.get_csrf(url)
        headers['Accept'] = 'application/json'
        with open(tgz, 'rb') as upload:
            filename = os.path.basename(tgz)
            start = 0
            upload.seek(0, 2)
            end = upload.tell()
            upload.seek(0, 0)

            while 1:
                start = upload.tell()
                data = upload.read(2 * 10**7)
                if not data:
                    break
                stop = upload.tell() - 1
                files = [
                    ('course-data', (filename, data, 'application/x-gzip'))
                ]
                headers['Content-Range'] = crange = '%d-%d/%d' % (start, stop, end)
                self.log.debug(crange)
                response = self.sess.post(url, files=files, headers=headers)
                self.log.debug(response.status_code)
            # now check import status
            self.log.info('Checking status')
            import_status_url = '{}/import_status/{}/{}'.format(self.studio_url, course_id, filename)
            status = 0
            while status != 4:
                status = self.sess.get(import_status_url).json()['ImportStatus']
                self.log.debug(status)
                time.sleep(3)
            self.log.info('Uploaded!')

    def login(self, email, password, do_lms=False):
        """
        Log in to studio or lms
        """
        if do_lms:
            signin_url = '{}/login'.format(self.lms_url)
            login_url = '{}/login_ajax'.format(self.lms_url)
        else:
            signin_url = '{}/signin'.format(self.studio_url)
            login_url = '%s/login_post' % self.studio_url

        headers = self.get_csrf(signin_url)
        self.log.info('Logging in to %s' % login_url)

        response = self.sess.post(login_url, {
            'email': email,
            'password': password,
            'honor_code': 'true'
            }, headers=headers)
        
        if response.status_code != 200 or not response.json()['success']:
            raise Exception(str(response))

    def export_tgz(self):
        """
        Export course from studio
        returns response
        """
        export_url = '{studio_url}/export/{course}'.format(
                    studio_url=self.studio_url,
                    course=self.course_id)

        self.log.info('Exporting from %s', export_url)
        response = self.sess.get(
            export_url,
            params={'_accept': 'application/x-tgz'},
            headers={'Referer': export_url},
            stream=True)
        self.log.debug(response.status_code)
        return response

    def get_id(self, path):
        """
        Guess edx_video_id from path
        """
        split = path.split('/')[-1]
        return split.split('_')[0]

    def process_video(self, xml):
        """
        Process video xml
        """
        source = xml.get('source') or ''
        edx_video_id = xml.get('edx_video_id')
        youtube_id = xml.get('youtube_id_1_0')

        for elt in xml.findall('./source'):
            src = elt.get('src')
            if src:
                edx_video_id = self.get_id(src)
                source = src
                break
        else:
            if source:
                edx_video_id = self.get_id(source)

        if self.course_id.startswith(('MITx', 'DelftX', 'LouvainX/Louv1.1x')) or not edx_video_id:
            # for mit, the filename will be the client id
            client_id = edx_video_id
            vid = self.match_video(client_id=client_id, youtube_id=youtube_id)
            if vid:
                edx_video_id = vid
            elif source:
                # try different client id
                source = source.split('/')[-1].rsplit('.', 1)[0]
                vid = self.match_video(client_id=source)
                if not vid:
                    # try again!
                    vid = self.match_video(client_id=source.replace('_', '-'))
                if vid:
                    edx_video_id = vid
                else:
                    raise MissingVideo(source)
            else:
                raise MissingVideo(source)

        if edx_video_id:
            self.log.debug('Found %s', edx_video_id)
            if youtube_id:
                for vid in self.course_vids:
                    if vid['edx_video_id'] == edx_video_id:
                        for enc in vid['encoded_videos']:
                            if enc['profile'] == 'youtube':
                                if enc['url'].strip() != youtube_id:
                                    self.log.info('youtube mismatch %s %s %s', edx_video_id, youtube_id, enc['url'])
                        break
            xml.set('edx_video_id', edx_video_id)

            xml = tostring(xml)
            return xml

    def process_export(self, infile, outfile):
        """
        Process exported tgz, adding edx_video_id to video xml and 
        writing a new tgz
        """
        kwargs = {}
        fname = infile
        if hasattr(infile, 'read'):
            kwargs['fileobj'] = infile
            fname = ''
        else:
            self.log.info('Processing exported archive %s', infile)

        intar = tarfile.TarFile.gzopen(fname, **kwargs)
        outtar = tarfile.TarFile.gzopen(outfile, mode='w')

        has_course = bool(self.course_id)

        not_found = []

        if has_course:
            self.get_course_val_videos()

        videos = 0
        processed = 0
        for finfo in intar:
            if not has_course:
                course_xml = intar.extractfile(os.path.join(finfo.name, 'course.xml')).read()
                course_xml = fromstring(course_xml)
                self.course_id = '%s/%s/%s' % (course_xml.get('org'), course_xml.get('course'), course_xml.get('url_name'))
                self.log.info('Found course.xml for %s', self.course_id)
                has_course = True
                self.get_course_val_videos()

            infile = intar.extractfile(finfo.name)
            if '/video/' in finfo.name:
                videos += 1
                xml = fromstring(infile.read())
                try:
                    new_xml = self.process_video(xml)
                except MissingVideo as e:
                    new_xml = None
                    not_found.append(xml)

                if new_xml:
                    infile = io.BytesIO(new_xml)
                    finfo.size = len(new_xml)
                    processed += 1
                else:
                    infile.seek(0)
            outtar.addfile(finfo, fileobj=infile)

        self.log.info('Converted %d videos out of %d', processed, videos)
        if not_found:
            self.log.warn('%s missing videos', len(not_found))
            return [(xml.get('youtube_id_1_0'), xml.get('display_name', u'').encode('utf8')) for xml in not_found]

    def find_missing_videos(self):
        """
        Use REST API to return list of videos that don't have VAL info
        """
        api_url = '{}/api/mobile/v0.5/video_outlines/courses/{}/missing'.format(self.lms_url, self.course_id)
        response = self.sess.get(api_url).json()
        if response:
            self.log.warn('%d missing videos (from API)', len(response))

        for vid in response:
            info = []
            info.append(('EVID', vid['summary']['video_id']))
            info.append(('Name', vid['summary']['name']))
            info.append(('Path', '/'.join(vid['named_path'])))
            info.append(('Section', vid['section_url']))
            info.append(('Unit', vid['unit_url']))
            info.append(('URL', vid['summary']['video_url']))
            if vid['summary']['missing_transcripts']:
                info.append(('Missing Transcripts', vid['summary']['missing_transcripts']))
            yield info

    def migrate_course(self, course_id, default_import=False):
        """
        Migrate course id:
        export tgz from studio, process tgz, import back to studio
        prints list of missing videos after re-import
        """
        self.course_id = course_id
        response = self.export_tgz()


        infile = io.BytesIO(response.content)

        outfile = '%s.tar.gz' % self.course_id.replace('/', '_')
        self.log.info('Saving to %s', outfile)
        missing = self.process_export(infile, outfile)
        response = infile = None

        if missing:
            for youtube_id, name in missing:
                if youtube_id:
                    print 'http://youtu.be/{}\t\t"{}"'.format(youtube_id, name)
                else:
                    print '"{}"'.format(name)

        if default_import or raw_input('\n\nImport course? [y/N] ').lower().strip() == 'y':
            self.import_tgz(outfile)
            for missing in self.find_missing_videos():
                for key, value in missing:
                    print '\t{}\t{}'.format(key, value)
                print '\n'

    def migrate_many(self, courses):
        """
        Migrate several courses
        """
        for line in courses:
            course_id = line.strip()
            if course_id.startswith('#') or not course_id:
                continue
            self.migrate_course(course_id)


def main():
    parser = argparse.ArgumentParser()
    parser.usage = '''
    {cmd} -c org/course/run [-e email@domain]
or
    {cmd} -f path/to/exported.tar.gz
'''.format(cmd=sys.argv[0])
    parser.description = 'prints counts of xblock types per course'
    parser.add_argument('-c', '--course', help='Course', default='')
    parser.add_argument('-i', '--courses', type=argparse.FileType('rb'), default=None)
    parser.add_argument('-f', '--export', help='Path to export file', default='')
    parser.add_argument('-e', '--email', help='Studio email address', default='')
    parser.add_argument('-l', '--lms', help='LMS URL', default='https://courses.edx.org')
    parser.add_argument('-s', '--studio', help='Studio URL', default='https://studio.edx.org')
    parser.add_argument('-v', '--verbose', help='verbose', default=False, action='store_true')

    args = parser.parse_args()
    if not (args.export or args.course or args.courses):
        parser.print_usage()
        return -1

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    email = args.email or raw_input('Studio email address: ')
    password = getpass.getpass('Studio password: ')

    mig = Migrator(studio_url=args.studio, lms_url=args.lms)
    mig.login(email, password)
    mig.login(email, password, do_lms=True)

    if args.export:
        infile = args.export
        indir, fname = os.path.split(infile)
        outfile = os.path.join(indir, 'NEW_' + fname)
        print '\nSaving to %s' % outfile
        mig.process_export(infile, outfile)
    elif args.course or args.courses:
        courses = args.courses or [args.course]
        mig.migrate_many(courses)


if __name__ == '__main__':
    sys.exit(main())
