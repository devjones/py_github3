import requests
import json
import os
import sys


#Login credentials for basic authentication only
#OAuth will be implemented very soon as an alternative
class Github(object):
    base_url = "https://api.github.com"

    def __init__(self,*args,**kwargs):
        self.user = kwargs.get('user')
        self.repo = kwargs.get('repo')
        self.branch = kwargs.get('branch','master')

        '''
        git_root is the parent location of the git repository
        if the .git folder is located at /home/sampleuser/projects/demo/.git, then the git_root would be: /home/sampleuser/projects/demo
        '''
        self.git_root = kwargs.get('git_root')

        self.auth = kwargs.get('auth',None)

        if self.auth == None:
            try:
                self.access_token = kwargs.get('access_token')
            except:
                '''User is not authorized'''
                self.access_token = None

    def _git_get(self,url):
        if self.auth:
            response = requests.get(self.base_url + url, auth=self.auth)
        elif self.access_token:
            response = requests.get(self.base_url + url + "?access_token=" + self.access_token)
        else:
            response = requests.get(self.base_url + url)




        return response

    def _git_post(self,url,data):

        headers = {}
        headers['content-type'] = 'application/json'

        if self.auth:
            response = requests.post(self.base_url + url,data=json.dumps(data), headers = headers, auth=self.auth)
        else:
            response = requests.post(self.base_url + url + "?access_token=" + self.access_token,data=json.dumps(data), headers = headers, auth=self.auth)



        return response

    def _get_tree_items(self,path_list):
        '''
        Returns a list of metadata about each item found in the path_list.
        An 'item' is a generic file object. It can be a normal file, executable file, directory, symlink.
        This function which analyze each item and 1) classify each item into one of the above options 2)Get either the file contents or a sha1 checksum id for each item
        '''


        #List of all items
        tree_items = []


        #TODO: Check if item_type is commit?
        for item_path in path_list:
            item_meta_data = {}
            full_item_path = self.git_root + "/" + item_path


            #determine the file mode in oct. Only get the last 6 digits
            raw_file_mode = oct(os.lstat(full_item_path).st_mode)[-6:]

            file_type = raw_file_mode[:3]
            file_permission = raw_file_mode[-3:]

            #only files are allowed to have permissions for the github api
            #file
            if file_type == '100':

                #check if the file is executable.  If not, default to normal file mode
                if file_permission == '755':
                    item_mode = '100755'
                else:
                    item_mode = '100644'

                item_type = 'blob'

            #directory
            elif file_type == '040':
                item_mode = '040000'
                item_type = 'tree'

            #symlink
            elif file_type == '120':
                item_mode = '120000'

                if os.path.isdir(full_item_path):
                    item_type = 'tree'
                else:
                    item_type = 'blob'


            #Get the contents of any blobs
            if item_type == "blob":

                f = open(full_item_path,'r')
                file_content = f.read()
                f.close()

                item_content = file_content
                item_meta_data['content'] = item_content
            else:
                #TODO: How to get the SHA?
                item_meta_data['sha'] = ""

            item_meta_data.update({'path':item_path,'mode':item_mode,'type':item_type})


            tree_items.append(item_meta_data)

        return tree_items




    def get_latest_commit(self):
        '''Returns the sha of the latest commit'''

        url = "/repos/%(user)s/%(repo)s/git/refs/heads/%(branch)s" % {'user':self.user,'repo':self.repo,'branch':self.branch}
        response = self._git_get(url)
        latest_commit = json.loads(response.content)
        sha_latest_commit = latest_commit['object']['sha']

        return sha_latest_commit

    def get_base_tree(self,sha_latest_commit):
        '''Returns the sha of the base tree for the last commit'''
        url = "/repos/%(user)s/%(repo)s/git/commits/%(sha_latest_commit)s" % {'user':self.user,'repo':self.repo,'sha_latest_commit':sha_latest_commit}
        response = self._git_get(url)
        base_tree = json.loads(response.content)
        sha_base_tree = base_tree['tree']['sha']

        return sha_base_tree

    def get_tree_contents(self,sha_tree):
        '''
        Returns an objects with the recursive contents from a tree(branch)
        Note: the sha_tree ought to be a unique identifier for the tree.
        This can be an actual sha.  Or in the case of a branch it can be a git 'treeish', i.e., refs/heads/master
        We will use 'treeishes' to get branches
        '''


        url = "/repos/%(user)s/%(repo)s/git/trees/%(sha_tree)s" % {'user':self.user,'repo':self.repo,'sha_tree':sha_tree}
        response = self._git_get(url)
        tree_contents = response['tree']

        return tree_contents


    def post_to_tree(self,sha_base_tree,path_list):
        url = "/repos/%(user)s/%(repo)s/git/trees" % {'user':self.user,'repo':self.repo}


        tree_items = self._get_tree_items(path_list)
        data = {
                'base_tree':sha_base_tree,
                'tree':tree_items,
                }


        response = self._git_post(url,data)

        new_tree = json.loads(response.content)
        sha_new_tree = new_tree['sha']

        return sha_new_tree



    def post_commit(self,sha_latest_commit,sha_new_tree,commit_message):

        url = "/repos/%(user)s/%(repo)s/git/commits" % {'user':self.user,'repo':self.repo}

        data = {
                'message':commit_message,
                'tree':sha_new_tree,
                'parents':[sha_latest_commit],
                }

        response = self._git_post(url,data)

        new_commit = json.loads(response.content)
        sha_new_commit = new_commit['sha']

        return sha_new_commit

    def post_ref(self,sha_new_commit):
        url = "/repos/%(user)s/%(repo)s/git/refs/heads/master" % {'user':self.user,'repo':self.repo}

        #may need to set force = True
        data = {
                'sha':sha_new_commit,
                'force':True,
                }

        response = self._git_post(url,data)

        return

