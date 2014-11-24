"""
The Video Migration Script!

Takes the export tarfile from studio (old data), converts it using VAL, and
then optionally imports the new tarfile (converted data) back into studio.
The old data will be processed by either adding an edx_video_id, updating,
or comparing the edx_video_id against the Video Abstraction Layer (VAL). The
tarfile export is the same as a studio course tarfile where the information
we are interested in is in the videos folder of the tarfile.

Possible conditions when processing videos:

Matching URLs:
    Old video has an edx_video_id and matches in VAL.
        Great!
    Old video has an edx_video_id that does not match in VAL. Matching urls
        This is possible if the edx_video_id was manually input. Update old
        edx_video_id with VAL edx_video_id.
    Old video does not have an edx_video_id.
        The urls for the video will be compared against VAL and the
        edx_video_id will be added accordingly.

URL mismatch:
    Old video has an edx_video_id and matches in VAL, but urls do not match.
        There could be broken/outdated links, or the wrong edx_video_id
        altogether. Defaults to studio urls.
    #TODO Old video's edx_video_id is found, but there are missing urls.
        Sometimes there will be missing encodings for
        a video, i.e., there exists a desktop version but no mobile version.

Not found:
    Old video has no edx_video_id and no urls can be found in VAL.
        A report should be made to fix this issue. This means that there are
        videos (which also could be broken/outdated) that VAL isn't aware of.
"""
#!/usr/bin/env python
import argparse
import sys
import getpass
import os
import requests
import io
import tarfile
import logging
from xml.etree.cElementTree import fromstring, tostring
import shutil
import time


class EdxVideoIdError(Exception):
    """
    Cannot find an edx_video_id
    """
    pass


class PermissionsError(Exception):
    """
    Permissions Error
    """
    pass


class ExportError(Exception):
    """
    Failure when exporting data
    """
    pass


class Migrator(object):
    """
    Migration class.

    Because we want to be able to take a list of course_ids and process them
    in one session, the Migrator object only needs to log in once.
    """
    def __init__(self,
                 course_id=None,
                 studio_url=None):
        self.studio_url = studio_url
        self.val_url = '{}/api/val/v0'.format(self.studio_url)
        self.sess = requests.Session()
        self.log = logging.getLogger('migrator')
        self.log.info(50*"=")
        self.log.info(50*"=")
        self.log.info(50*"=")
        self.course_id = course_id
        self.course_videos = []
        self.videos_processed = 0

    def get_csrf(self, url):
        """
        return csrf token retrieved from the given url
        """
        response = self.sess.get(url)
        csrf = response.cookies['csrftoken']
        return {'X-CSRFToken': csrf, 'Referer': url}

    def login_to_studio(self, email, password):
        """
        Use given credentials to login to studio.

        Attributes:
            email (str): Login email
            password (str): Login password
        """
        signin_url = '%s/signin' % self.studio_url
        headers = self.get_csrf(signin_url)

        login_url = '%s/login_post' % self.studio_url
        print 'Logging in to %s' % self.studio_url

        response = self.sess.post(login_url, {
            'email': email,
            'password': password,
            'honor_code': 'true'
        }, headers=headers).json()

        if not response['success']:
            raise Exception(str(response))

        print 'Login successful'

    def import_tar_to_studio(self, file_path):
        """
        Uploads given tar (file_path) to studio.
        """
        course_id = self.get_course_id_from_tar(file_path)
        url = '{}/import/{}'.format(self.studio_url, course_id)
        self.log.info(
            'Importing {} to {} from {}'.format(course_id, url, file_path)
        )
        print 'Importing {} to {} from {}'.format(course_id, url, file_path)
        print 'Upload may take a while depending on size of the course'
        headers = self.get_csrf(url)
        headers['Accept'] = 'application/json'
        with open(file_path, 'rb') as upload:
            filename = os.path.basename(file_path)
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
                headers['Content-Range'] = crange = '%d-%d/%d'\
                                                    % (start, stop, end)
                self.log.debug(crange)
                response = self.sess.post(url, files=files, headers=headers)
                self.log.debug(response.status_code)
            # now check import status
            self.log.info('Checking status')
            import_status_url = '{}/import_status/{}/{}'.format(
                self.studio_url, course_id, filename)
            status = 0
            while status != 4:
                status = self.sess.get(import_status_url).json()['ImportStatus']
                self.log.debug(status)
                time.sleep(3)
            self.log.info('Uploaded!')
            print 'Uploaded!'

    def convert_courses_from_studio(self, courses):
        """
        Takes a single course or courses and converts them from studio

        Conversion involves adding an edx_video_id to the old course data which
        may or may not have an edx_video_id.

        Attributes:
            courses (list): a list of courses. Could be a single course

        """
        for course in courses:

            course_id = course.strip()
            self.course_id = course_id

            response = self.export_course_data_from_studio(course_id)

            if response.status_code != 200:
                if response.status_code == 500:
                    self.log.error(
                        "%s: Cannot find course in studio %s" %
                        (course_id, response)
                    )
                else:
                    self.log.error(
                        "%s: Error %s" % (course_id, response)
                    )
            else:
                old_course_data = io.BytesIO(response.content)

                outfile = '%s.tar.gz' % self.course_id.replace('/', '_')
                print 'Saving to %s' % outfile
                print "Processing videos. This may take a while depending on" \
                      "the number of videos in the course."
                try:
                    self.process_course_data(old_course_data, outfile)
                    print "Course processed"
                except ExportError as e:
                    self.log.error("%s: Could not read export data"
                                   % self.course_id)
                    print "Could not read export data for %s" \
                          % self.course_id

    def export_course_data_from_studio(self, course_id):
        """
        Given the URL, gets the data for the given course_id from studio

        Returns:
            response (Response object)
        """
        export_url = '{studio_url}/export/{course}'.format(
            studio_url=self.studio_url,
            course=course_id)
        print 'Exporting from %s' % export_url
        print "This may take a while depending on course size."
        response = self.sess.get(
            export_url,
            params={'_accept': 'application/x-tgz'},
            headers={'Referer': export_url},
            stream=True)
        return response

    def process_course_data(self, old_course_data, new_filename):
        """
        Process the old_course_data to include the edx_video_id, then saves it
        """
        #Opens old_course_data and creates new tarfile to write to
        kwargs = {}
        file_name = old_course_data
        if hasattr(old_course_data, 'read'):
            kwargs['fileobj'] = old_course_data
            file_name = ''
        try:
            old_data = tarfile.TarFile.gzopen(file_name, **kwargs)
        except tarfile.ReadError:
            raise ExportError
        converted_tar = tarfile.TarFile.gzopen(
            ("converted_tarfiles/"+new_filename), mode='w'
        )

        #Sets course_id and then populates course_videos from val.
        if self.course_id is None:
            course_xml = old_data.extractfile(os.path.join(
                old_data.getnames()[0],
                'course.xml')).read()
            course_xml = fromstring(course_xml)
            self.course_id = '%s/%s/%s' % (
                course_xml.get('org'),
                course_xml.get('course'),
                course_xml.get('url_name')
            )
        self.course_videos = self.get_course_videos_from_val()

        #Process videos, and save to tarfile
        not_found = []

        for item in old_data:
            infile = old_data.extractfile(item.name)
            if '/video/' in item.name:
                video_xml = fromstring(infile.read())
                try:
                    new_xml = self.add_edx_video_id_to_video(video_xml)
                except EdxVideoIdError as e:
                    new_xml = None
                    not_found.append(video_xml)

                if new_xml:
                    infile = io.BytesIO(new_xml)
                    item.size = len(new_xml)
                else:
                    infile.seek(0)
            converted_tar.addfile(item, fileobj=infile)

        #Logs videos that were not found
        if not_found:
            self.log.info("%s: %s Missing videos:"
                          % (self.course_id, len(not_found)))
            for video_xml in not_found:
                youtube_id = video_xml.get('youtube_id_1_0')
                display_name = video_xml.get('display_name', u'').encode('utf8')
                url_name = video_xml.get("url_name")
                self.log.info(
                    '\t"url_name:"{}"\tyoutube_id:"{}"\tdisplay_name:"{}"'
                    .format(url_name,youtube_id,display_name)
                )
        self.log.info("%s: %s Videos have been processed"
                      % (self.course_id, self.videos_processed))
        self.videos_processed = 0

    def get_course_videos_from_val(self, course_id=None):
        """
        Calls VAL api to get all available videos in given course_id

        Returns:
            videos (str): videos in json
        """
        course_id = course_id or self.course_id
        url = self.val_url + '/videos/'
        response = self.sess.get(url, params={'course': self.course_id})
        if response.status_code == 403:
            raise(PermissionsError)
        videos = response.json()
        # # HACK for messed up ids
        if self.course_id == 'MITx/6.002x_4x/3T2014' and not videos:
            videos = self.get_course_youtube_videos('MITx/6.002_4x/3T2014')
        return videos

    def add_edx_video_id_to_video(self, video_xml):
        """
        Takes a video's xml and compares/sets edx_video_id
        """
        source = video_xml.get('source') or ''
        studio_edx_video_id = video_xml.get('edx_video_id')
        youtube_id = video_xml.get('youtube_id_1_0')

        edx_video_id_found = False

        #Gets edx_video_id by parsing a url
        for line in video_xml.findall('./source'):
            source_url = line.get('src')
            if source_url:
                edx_video_id = self.get_edx_video_id_from_url(source_url)
                source = source_url
                edx_video_id_found = True
                break
        else:
            if source:
                edx_video_id = self.get_edx_video_id_from_url(source)
                edx_video_id_found = True

        #Looking for edx_video_id via youtube_id/client_id
        if self.course_id.startswith(('MITx', 'DelftX', 'LouvainX/Louv1.1x')) \
                or edx_video_id_found is False:
            # for mit, the filename will be the client id
            client_id = studio_edx_video_id
            edx_video_id_found, edx_video_id =\
                self.get_edx_video_id_from_ids(
                    client_id=client_id,
                    youtube_id=youtube_id
                )

        #Looking for edx_video_is via source, else report missing
        if edx_video_id_found is False:
            source = source.split('/')[-1].rsplit('.', 1)[0]
            edx_video_id_found, edx_video_id =\
                self.get_edx_video_id_from_ids(client_id=source)
            if edx_video_id_found is False:
                edx_video_id_found, edx_video_id =\
                    self.get_edx_video_id_from_ids(
                        client_id=source.replace('_', '-')
                    )
                if edx_video_id_found is False:
                    raise EdxVideoIdError(source)

        #Set edx_video_id and log issues
        else:
            if studio_edx_video_id == '' or studio_edx_video_id is None:
                self.log.debug("%s: Empty edx_video_id in studio for %s"
                              % (self.course_id, edx_video_id))
            elif studio_edx_video_id != edx_video_id:
                self.log.error(
                    "%s: Mismatching edx_video_ids - Studio: %s VAL: %s"
                    % (self.course_id, studio_edx_video_id, edx_video_id))
            if youtube_id:
                self.get_youtube_mismatch(edx_video_id, youtube_id)
            video_xml.set('edx_video_id', edx_video_id)
            video_xml = tostring(video_xml)
            self.videos_processed += 1
            return video_xml

    def get_youtube_mismatch(self, edx_video_id, youtube_id):
        """
        Given a youtube_id and edx_video_id, logs mismatched in url

        Currently mismatches will default to saving the studio urls to the
        tarfile.
        """
        for vid in self.course_videos:
            if vid['edx_video_id'] == edx_video_id:
                for enc in vid['encoded_videos']:
                    if enc['profile'] == 'youtube':
                        if enc['url'].strip() != youtube_id:
                            val_url = enc['url']
                            self.log.error("%s: Mismatching youtube URLS for"
                                          " edx_video_id: %s - Studio: %s VAL:"
                                          " %s" % (self.course_id, edx_video_id
                                          , youtube_id, val_url))

    def get_edx_video_id_from_url(self, path):
        """
        Parses the edx_video_id from a source url

        Returns:
            (str): the edx_video_id
        """
        split = path.split('/')[-1]
        return split.split('_')[0]

    def get_edx_video_id_from_ids(self, youtube_id=None, client_id=None):
        """
        Gets edx_video_id by searching course_videos with youtube or client ids

        Returns:
            Boolean, edx_video_id (bool, str): If successful returns True and
             the edx_video_id. Else, returns false, and an empty string.
        """
        for video in self.course_videos:
            if youtube_id:
                for enc in video['encoded_videos']:
                    if enc['profile'] == 'youtube' and enc['url'].strip() == youtube_id:
                        return True, video['edx_video_id']
            if video['client_video_id'] == client_id:
                return True, video['edx_video_id']
        return False, ''

    def get_course_id_from_tar(self, file_path):
        """
        Given a file_path to a tarfile, returns the course_id

        Returns:
            course_id (str): course_id parsed from course.xml in tar
        """
        kwargs = {}
        file_name = file_path
        if hasattr(file_path, 'read'):
            kwargs['fileobj'] = file_path
            file_name = ''
        old_data = tarfile.TarFile.gzopen(file_name, **kwargs)
        course_xml = old_data.extractfile(os.path.join(
            old_data.getnames()[0],
            'course.xml')).read()
        course_xml = fromstring(course_xml)
        course_id = '%s/%s/%s' % (
            course_xml.get('org'),
            course_xml.get('course'),
            course_xml.get('url_name')
        )
        return course_id


def main():
    """
    Exports data from studio, processes it, then optionally imports to studio

    Takes login credentials for studio where we will pull course data. This data
    will be processed through VAL. This data will be packed into a tar that can
    be optionally imported to studio.
    """

    parser = argparse.ArgumentParser()
    parser.usage = '''
    {cmd} -c org/course/run [-e email@domain]
    or
    {cmd} -f path/to/exported.tar.gz
    or
    {cmd} --import

    To export a course, use -c "course_id".
    To export a list of courses, use -l path/to/courses.txt
    To upload courses in the convert_tarfiles directory, use -u
    '''.format(cmd=sys.argv[0])
    parser.add_argument('-c', '--course', help='Course', default='')
    parser.add_argument('-l', '--courses', type=argparse.FileType('rb'), default=None)
    parser.add_argument('-f', '--export', help='Path to export file', default='')
    parser.add_argument('-e', '--email', help='Studio email address', default='')
    parser.add_argument('-s', '--studio', help='Studio URL', default='http://studio.mobile3.m.sandbox.edx.org')
    parser.add_argument('-v', '--verbose', help='verbose', default=False, action='store_true')
    parser.add_argument('-u', '--upload', help='Upload to studio', default=False, action='store_true')

    args = parser.parse_args()

    if not (args.export or args.course or args.courses or args.upload):
        parser.print_usage()
        return -1

    logging.basicConfig(
        filename='migrator_log.txt',
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    migration = Migrator(studio_url=args.studio)

    email = args.email or raw_input('Studio email address: ')
    password = getpass.getpass('Studio password: ')
    migration.login_to_studio(email, password)

    if not args.upload:
        folder = "converted_tarfiles"
        if not os.path.exists(folder):
            os.makedirs(folder)
        elif raw_input('Empty converted_tarfiles folder? When importing, '
                       'all files in this folders will be marked for upload'
                       ' [y/n] ').lower().strip() == 'y':
            shutil.rmtree(folder)
            os.makedirs(folder)

        if args.export:
            export_data = args.export
            indir, fname = os.path.split(export_data)
            new_filename = os.path.join('NEW_' + fname)
            print '\nSaving to %s' % new_filename
            migration.process_course_data(export_data, new_filename)
        elif args.courses or args.course:
            courses = args.courses or [args.course]
            migration.convert_courses_from_studio(courses)

        possible_issues = open('migrator_log.txt', 'r')

        print "Logged issues:"
        for line in possible_issues:
            print line

        print "Check the issues in migrator_log.txt before importing"

    upload_query = 'Upload courses in converted_tarfiles directory to %s [y/n] ' % args.studio
    if raw_input(upload_query) == 'y':
        upload_message = "*"*20+"Starting uploads"+"*"*20
        logging.info(upload_message)
        for filename in os.listdir(folder):
            file_path = "%s/%s" % (folder, filename)
            migration.import_tar_to_studio(file_path)
    return

if __name__ == "__main__":
    sys.exit(main())

