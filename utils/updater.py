#!/usr/bin/env python3

import git
import os
import inspect
import time
import shutil

from git.exc import GitCommandError

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Printer():

    def __getTime(self):
        return time.asctime(time.localtime())

    def debug(self, msg):
        print('{} - DEBUG - {}'.format(self.__getTime(), msg))

    def warning(self, msg):
        print('{} - WARNING - {}'.format(self.__getTime(), msg))

    def info(self, msg):
        print('{} - INFO - {}'.format(self.__getTime(), msg))

class Updater():
    def __init__(self, log=None):
        if log:
            self.log = log
        else:
            self.log = Printer()

    def __get_calling_file(self):
        '''
        This function will go through the python call stack and find
        the script that originally called into this file. Returns a 
        tuple where the first element is a string that is the folder
        containing the calling script, and the second element is the
        name of the file name of the calling script. If a file can not
        be found for some reason a LookupError is raised to indicate
        that an external script could not be found.
        '''
        stack = inspect.stack()
        this_file = stack[0][1]
        for i in range(1, len(stack)):
            if stack[i][1] != this_file:
                complete_path = os.path.normpath(os.getcwd() + "/" + stack[i][1])
                self.log.debug("Module was called from: {}".format(complete_path))
                return os.path.split(complete_path)

        self.log.warning("Module was not called by an external script.")
        raise LookupError("Module was not called by an external script.")

    def __get_file_diffs(self, repo):
        '''
        Simple function that takes in a pointer to the repo
        and returns a list of files that contain changes 
        between the remote and local repo.
        '''
        assert type(repo) is git.repo.base.Repo, "Passed in repo needs to be of type 'git.repo.base.Repo'"
        diff = str(repo.git.diff("--name-only")).splitlines()
        if len(diff) == 0:
            self.log.debug("No diff found")
        else:
            msg = "Found {} diffs in files:".format(len(diff))
            for conflict in diff:
                msg += "\n  {}".format(conflict)
            self.log.debug(msg)
        return diff

    def __find_current_branch(self, repo):
        '''
        Simple function that returns the name of the current branch. 
        If for some reason the function fails to find the current branch
        an IOError is raised to indicate something has gone wrong. 
        '''
        assert type(repo) is git.repo.base.Repo, "Passed in repo needs to be of type 'git.repo.base.Repo'"
        branches = str(repo.git.branch()).splitlines()
        for branch in branches:
            # asterisk represents current branch, search for it
            if branch[0] == "*":
                self.log.debug("Found current branch to be: {}".format(branch[2:]))
                return branch[2:]
        self.log.warning("Failed to find current branch")
        raise  IOError("Failed to find current branch")

    def __is_dev_env(self, directory, suppress_errors=False):
        '''
        This function will return 'True' if the git repo is setup to 
        be a selfupdate development environment. This indicates that 
        functions that perform destructive file manipulation will be 
        limited in scope as to not cause the script to complicate 
        development efforts when using the selfupdate library. A 
        selfupdate development environment is configured by placeing
        an empty file in the root directory of the repo simply named
        '.devenv'. This file must also be included in the .gitignore
        or a EnvironmentError will be raised. This is to avoid the 
        propagation of the development environment file to the main 
        repo and any other local repositories that would then pull 
        this file down and turn themselves into development 
        environments. This error can be suppressed by setting the 
        argument 'suppress_errors' to 'True' when calling is_dev_env().
        Suppressing this error can cause remote repos that rely on 
        selfupdate to no longer update successfully without direct
        user input. You have been warned! 
        '''
        directory = os.path.normpath(directory)
        # see if the .devenv file even exists
        if os.path.isfile(directory + "/.devenv"):
            # it exists, so make sure a .gitignore exists and it includes .devenv
            if os.path.isfile(directory + "/.gitignore"):
                with open(directory + "/.gitignore", 'r') as gitignore:
                    for line in gitignore.readlines():
                        if ".devenv" in line:
                            self.log.debug("Found valid development environment")
                            return True
            #raise error here
            self.log.warning("'.devenv' found but not included in '.gitignore'.")
            if not suppress_errors:
                raise EnvironmentError("'.devenv' found but not included in '.gitignore'.")
        else:
            self.log.debug("No '.devenv' file found in the root directory of the repo")

        return False

    def __find_repo(self):
        '''
        This function will go figure out if the calling python script
        is inside a git repo, and if so, return a string that is the 
        location of the base of the git repo. If the script is not, a 
        LookupError is raised to indicate it could not find the repo
        '''
        if os.path.exists(os.path.join(APP_ROOT, u'.git')):
            self.log.debug('APP_ROOT is git repo: {}'.format(APP_ROOT))
            return APP_ROOT
        # # file_path, file_name = __get_calling_file()
        # file_path, _ = self.__get_calling_file()
        # # walk up the file tree looking for a valid git repo, stop when we hit the base
        # while True:
        #     if os.path.samefile(os.path.normpath(file_path), os.path.normpath("/")):
        #         self.log.warning("Calling script is not in a valid git repo")
        #         raise LookupError("Calling script is not in a valid git repo")

        #     try:
        #         git.Repo(file_path)
        #         self.log.debug("Found root of repo located at: {}".format(os.path.normpath(file_path)))
        #         return os.path.normpath(file_path)
        #     except git.InvalidGitRepositoryError:
        #         file_path = os.path.normpath(file_path + "/..")

    def __clean_pycache(self, rootDir):
        '''
        This function will remove all '__pycache__' directories.
        IOError is raised if unable
        '''
        self.log.info('Cleaning pycache directories')
        for root, dirs, _ in os.walk(os.path.abspath(rootDir)):
            for directory in dirs:
                if directory == '__pycache__':
                    path = os.path.join(root, directory)
                    if os.path.isdir(path):
                        self.log.debug('Removing: "{}"'.format(path))
                        try:
                            shutil.rmtree(path)
                        except IOError as e:
                            self.log.warning('Could not remove "{}" ERROR: {}'.format(path, e))

    def __get_repo(self):
        repo = git.Repo(APP_ROOT)
        try:
            assert not repo.bare
        except AssertionError:
            self.log.critical('This is not a valid git repository. Unable to auto update.')
            return None
        return repo

    def pull(self, force=False, check_dev=True):
        '''
        This function will attempt to pull any remote changes down to 
        the repository that the calling script is contained in. If 
        there are any file conflicts the pull will fail and the function
        will return. This function is *safe* and does not perform 
        destructive actions on the repo it is being called on. This 
        function returns a tuple containing 2 fields. The first is a
        boolean value that indicates if the pull was successful or not. 
        The second field contains a list of the files that were effected
        by the pull. If the pull was successful, this is the files that 
        were updated by the pull action. If the pull was unsuccessful, 
        this list contains the files that have conflicts and stopped the
        pull. All files listed in the case of a success or failure are 
        referenced relative to the base of the repository. This function 
        attempts to capture git errors but it is entirely possible that 
        it does not handle a git error correctly in which case it will be 
        raised again to be potentially handled higher up. 
        '''
        self.log.info('Checking Git for updates.')
        repo = self.__get_repo()
        if not force:
            try:
                resp = str(repo.git.pull()).splitlines()
                if resp[0] == "Already up-to-date.":
                    self.log.info("Repository is already up to date.")
                    return (False, [])

                files = [a.split("|")[0][1:-1] for a in resp[2:-1]]
                self.__clean_pycache(APP_ROOT)
                self.log.debug("Files that were updated: " + "\n  ".join(files))
                return (True, files)
            except GitCommandError as err:
                err_list = str(err).splitlines()

                # this is a poor and rudimentary way to tell if there was a specific error TODO: fix
                if err_list[3] == "  stderr: 'error: Your local changes to the following files would be overwritten by merge:":
                    files = [a[1:] for a in err_list[4:-2]]
                    self.log.warning("Pull failed. Files with conflicts:" + "\n  ".join(files))
                    return (False, files)
                # we got an error we didn't expect, pass it back up
                raise

            return (True, [])
        else:
            if check_dev and self.__is_dev_env(APP_ROOT):
                self.log.info("Detected development environment. Aborting hard pull")
                return (False, [])
            branch = self.__find_current_branch(repo)

            # record the diff, these will all replaced
            diffs = self.__get_file_diffs(repo)

            if len(diffs) == 0:
                return (False, [])

            # fetch all
            fetch_resp = str(repo.git.fetch("--all"))
            self.log.debug("Fetched any and all changes with response: {}".format(fetch_resp))
            # reset
            reset_resp = str(repo.git.reset("--hard", "origin/{}".format(branch)))
            self.log.info("Completed hard pull with response: {}".format(reset_resp))
            # clean
            clean_resp = str(repo.git.clean("-f"))
            self.log.info("Completed clean with response: {}".format(clean_resp))
            self.__clean_pycache(APP_ROOT)
            return (True, diffs)