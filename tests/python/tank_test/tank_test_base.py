# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Base class for engine and app testing
"""

import os
import time
import shutil
import pprint
import tempfile

from .mockgun import Shotgun as MockGun_Shotgun 

from mock import Mock
import unittest2 as unittest

import sgtk
import tank
from tank_vendor import yaml

TANK_TEMP = None
TANK_SOURCE_PATH = None

__all__ = ['setUpModule', 'TankTestBase', 'tank']

def setUpModule():
    """
    Creates studio level directories in temporary location for tests.
    """
    global TANK_TEMP
    global TANK_SOURCE_PATH

    # determine tests root location 
    temp_dir = tempfile.gettempdir()
    # make a unique test dir for each file
    temp_dir_name = "tankTemporaryTestData"
    # Append time to the temp directory name
    temp_dir_name += "_%f" % time.time()

    TANK_TEMP = os.path.join(temp_dir, temp_dir_name)
    # print out the temp data location
    msg = "Tank test data location: %s" % TANK_TEMP
    print "\n" + "="*len(msg)
    print msg
    print "="*len(msg) + "\n"

    # move tank directory if left by previous tests
    _move_data(TANK_TEMP)
    os.makedirs(TANK_TEMP)

    # create studio level tank directories
    studio_tank = os.path.join(TANK_TEMP, "tank")

    # make studio level subdirectories
    os.makedirs(os.path.join(studio_tank, "config", "core"))
    os.mkdir(os.path.join(studio_tank, "doc"))
    install_dir = os.path.join(studio_tank, "install")

    # copy tank engine code into place
    TANK_SOURCE_PATH = os.path.abspath(os.path.join( os.path.dirname(__file__), "..", "..", ".."))
    os.makedirs(os.path.join(install_dir, "engines"))





class TankTestBase(unittest.TestCase):
    """Test base class which manages fixtures for tank related tests."""
    
    def __init__(self, *args, **kws):
        super(TankTestBase, self).__init__(*args, **kws)
        
        # Below are attributes which will be set during setUp

        # Path to temp directory
        self.tank_temp = None
        # fake project enity dictionary
        self.project = None
        self.project_root = None
        # alternate project roots for multi-root tests
        self.alt_root_1 = None
        self.alt_root_2 = None
        # path to tank source code
        self.tank_source_path = None
        # project level config directories
        self.project_config = None

    def setUp(self, project_tank_name = "project_code"):
        """Creates and registers test project."""
        self.tank_temp = TANK_TEMP
        self.tank_source_path = TANK_SOURCE_PATH

        # define entity for test project
        self.project = {"type": "Project",
                        "id": 1,
                        "tank_name": project_tank_name,
                        "name": "project_name"}

        self.project_root = os.path.join(self.tank_temp, self.project["tank_name"].replace("/", os.path.sep) )
          
        # create project directory
        self._move_project_data()
        
        os.makedirs(self.project_root)
        
        project_tank = os.path.join(self.project_root, "tank")
        os.mkdir(project_tank)

        # project level config directories
        self.project_config = os.path.join(project_tank, "config")

        # create project cache directory
        project_cache_dir = os.path.join(project_tank, "cache")
        os.mkdir(project_cache_dir)

        # create back-link file from project storage
        data = "- {darwin: '%s', linux2: '%s', win32: '%s'}" % (project_tank, project_tank, project_tank) 
        self.create_file(os.path.join(project_tank, "config", "tank_configs.yml"), data)

        # add files needed by the pipeline config
        
        pc_yml = os.path.join(project_tank, "config", "core", "pipeline_configuration.yml")
        pc_yml_data = "{ project_name: %s, pc_id: 123, project_id: 1, pc_name: Primary}\n\n" % self.project["tank_name"]        
        self.create_file(pc_yml, pc_yml_data)
        
        loc_yml = os.path.join(project_tank, "config", "core", "install_location.yml")
        loc_yml_data = "Windows: '%s'\nDarwin: '%s'\nLinux: '%s'" % (project_tank, project_tank, project_tank)
        self.create_file(loc_yml, loc_yml_data)
        
        roots = {"primary": {}}
        for os_name in ["windows_path", "linux_path", "mac_path"]:
            #TODO make os specific roots
            roots["primary"][os_name] = self.tank_temp        
        roots_path = os.path.join(project_tank, "config", "core", "roots.yml")
        roots_file = open(roots_path, "w") 
        roots_file.write(yaml.dump(roots))
        roots_file.close()        
        
        self.pipeline_configuration = sgtk.pipelineconfig.from_path(project_tank)
        self.tk = tank.Tank(self.pipeline_configuration)
        self.tk._Tank__sg = MockGun_Shotgun("http://unit_test_mock_sg", "mock_user", "mock_key")

        # add project to mock sg and path cache db
        self.add_production_path(self.project_root, self.project)
        
        
        
        
    def tearDown(self):
        """Cleans up after tests."""
        self._move_project_data()
        
    def setup_fixtures(self, core_config="default_core"):
        
        
        
        test_data_path = os.path.join(self.tank_source_path, "tests", "data")
        core_source = os.path.join(test_data_path, core_config)
        core_target = os.path.join(self.project_config, "core")
        self._copy_folder(core_source, core_target)

        for config_dir in ["env", "hooks", "test_app", "test_engine"]:
            config_source = os.path.join(test_data_path, config_dir)
            config_target = os.path.join(self.project_config, config_dir)
            self._copy_folder(config_source, config_target)
        
        # Edit the test environment with correct hard-coded paths to the test engine and app
        src = open(os.path.join(test_data_path, "env", "test.yml"))
        dst = open(os.path.join(self.project_config, "env", "test.yml"), "w")
        
        test_app_path = os.path.join(self.project_config, "test_app")
        test_engine_path = os.path.join(self.project_config, "test_engine")
        
        for line in src:
            tmp = line.replace("TEST_APP_LOCATION", test_app_path)
            dst.write(tmp.replace("TEST_ENGINE_LOCATION", test_engine_path))
        
        src.close()
        dst.close()
        
        if core_config != "multi_root_core":
            # setup_multi_root_fixtures is messing a bunch with the 
            # templates so it does a separate reload
            self.tk.reload_templates()
                
    
    def setup_multi_root_fixtures(self):

        self.setup_fixtures(core_config="multi_root_core")
        
        # Add multiple project roots
        project_name = os.path.basename(self.project_root)
        self.alt_root_1 = os.path.join(self.tank_temp, "alternate_1", project_name)
        self.alt_root_2 = os.path.join(self.tank_temp, "alternate_2", project_name)
        
        # add backlink files to storage
        tank_code = os.path.join(self.project_root, "tank")
        data = "- {darwin: '%s', linux2: '%s', win32: '%s'}" % (tank_code, tank_code, tank_code) 
        self.create_file(os.path.join(self.alt_root_1, "tank", "config", "tank_configs.yml"), data)
        self.create_file(os.path.join(self.alt_root_2, "tank", "config", "tank_configs.yml"), data)


        # Write roots file
        roots = {"primary": {}, "alternate_1": {}, "alternate_2": {}}
        for os_name in ["windows_path", "linux_path", "mac_path"]:
            #TODO make os specific roots
            roots["primary"][os_name]     = os.path.dirname(self.project_root)
            roots["alternate_1"][os_name] = os.path.dirname(self.alt_root_1)
            roots["alternate_2"][os_name] = os.path.dirname(self.alt_root_2)
        roots_path = os.path.join(self.project_root, "tank", "config", "core", "roots.yml")     
        roots_file = open(roots_path, "w") 
        roots_file.write(yaml.dump(roots))
        roots_file.close()
        
        # need a new PC object that is using the new roots def file we just created
        self.pipeline_configuration = sgtk.pipelineconfig.from_path(os.path.join(self.project_root, "tank"))
        # push this new PC into the tk api
        self.tk._Tank__pipeline_config = self.pipeline_configuration 
        
        # force reload templates
        self.tk.reload_templates()
        
        # add project root folders
        # primary path was already added in base setUp
        self.add_production_path(self.alt_root_1, self.project)
        self.add_production_path(self.alt_root_2, self.project)
        
        self.tk.create_filesystem_structure("Project", self.project["id"])

        
    def add_production_path(self, path, entity=None):
        """
        Creates project directories, populates path cache and mocked shotgun from a
        path an entity.
        
        :param path: Path of directory to create, relative to it's project.
        :param entity: Entity to add to path cache, mocked shotgun and for which
                       to write an entity file. Should be dictionary with 'type',
                       'name', and 'id' keys.
        """
        full_path = os.path.join(self.project_root, path)
        if not os.path.exists(full_path):
            # create directories
            os.makedirs(full_path)
        if entity:
            # add to path cache
            self.add_to_path_cache(path, entity)
            # populate mock sg
            self.add_to_sg_mock_db(entity)

    def add_to_path_cache(self, path, entity):
        """
        Adds a path and entity to the path cache sqlite db. 

        :param path: Absolute path to add.
        :param entity: Entity dictionary with values for keys 'id', 'name', and 'type'
        """
        
        # fix name/code discrepancy
        if "code" in entity:
            entity["name"] = entity["code"]
        
        path_cache = tank.path_cache.PathCache(self.tk)
        
        data = [ {"entity": {"id": entity["id"], 
                             "type": entity["type"], 
                             "name": entity["name"]}, 
                  "metadata": [],
                  "path": path, 
                  "primary": True } ]
        path_cache.add_mappings(data, None, [])
        
        # On windows path cache has persisted, interfering with teardowns, so get rid of it.
        path_cache.close()
        del(path_cache)
                       
    def debug_dump(self):
        
        print ""
        print "-----------------------------------------------------------------------------"
        print " Shotgun contents:"
        
        print pprint.pformat(self.tk.shotgun._db)
        print ""
        print ""
        print "Path Cache contents:"
        
        path_cache = tank.path_cache.PathCache(self.tk)
        c = path_cache._connection.cursor()
        for x in list(c.execute("select * from path_cache" )):
            print x
        c.close()
        path_cache.close()
        
        print "-----------------------------------------------------------------------------"
        print ""
                                
    def add_to_sg_mock_db(self, entities):
        """
        Adds an entity or entities to the mocked shotgun database.

        :param entities: A shotgun style dictionary with keys for id, type, and name
                         defined. A list of such dictionaries is also valid.
        """        
        # make sure it's a list
        if isinstance(entities, dict):
            entities = [entities] 
        for entity in entities:
            # entity: {"id": 2, "type":"Shot", "name":...}
            # wedge it into the mockgun database            
            et = entity["type"]
            eid = entity["id"]
            
            # special retired flag for mockgun
            entity["__retired"] = False
            
            # turn any dicts into proper type/id/name refs
            for x in entity:
                if isinstance(entity[x], dict):
                    # make a std sg link dict with name, id, type
                    link_dict = {"type": entity[x]["type"], "id": entity[x]["id"] }
                    
                    # most basic case is that there already is a name field,
                    # in that case we are done
                    if "name" in entity[x]:
                        link_dict["name"] = entity[x]["name"]
                    
                    elif entity[x]["type"] == "Task":
                        # task has a 'code' field called content
                        link_dict["name"] = entity[x]["content"]  
                    
                    elif "code" not in entity[x]:
                        # auto generate a code field
                        link_dict["name"] = "mockgun_autogenerated_%s_id_%s" % (entity[x]["type"], entity[x]["id"])
                    
                    else:
                        link_dict["name"] = entity[x]["code"]  
                    
                    # print "Swapping link dict %s -> %s" % (entity[x], link_dict) 
                    entity[x] = link_dict
            
            self.tk.shotgun._db[et][eid] = entity            

    def create_file(self, file_path, data=""):
        """Creates a file on disk with specified data. First the file's directory path will be 
        created, and then a file with contents matching input data.

        :param file_path: Absolute path to the file.
        :param data: (Optional)Data to be written in the file. 
        """
        if not file_path.startswith(self.tank_temp):
            raise Exception("Only files in the test data area should be created with this method.")

        dir_path = os.path.dirname(file_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        open_file = open(file_path, "w") 
        open_file.write(data)
        open_file.close()
            
    def check_error_message(self, Error, message, func, *args, **kws):
        """
        Check that the correct exception is raised with the correct message.

        :param Error: The exception that is expected.
        :param message: The expected message on the exception.
        :param func: The function to call.
        :param args: Arguments to be passed to the function.
        :param kws: Keyword arguments passed to the function.

        :rasies: Exception if correct exception is not raised, or the message on the exception
                 does not match that specified.
        """
        self.assertRaises(Error, func, *args, **kws)

        try:
            func(*args, **kws)
        except Error, e:
            self.assertEquals(message, e.message)

    def _move_project_data(self):
        """
        Calls _move_data for all project roots.
        """
        _move_data(self.project_root)
        _move_data(self.alt_root_1)
        _move_data(self.alt_root_2)

    def _copy_folder(self, src, dst): 
        """
        Alternative implementation to shutil.copytree
        Copies recursively with very open permissions.
        Creates folders if they don't already exist.
        """
        files = []
        
        if not os.path.exists(dst):
            os.mkdir(dst, 0777)
    
        names = os.listdir(src) 
        for name in names:
    
            srcname = os.path.join(src, name) 
            dstname = os.path.join(dst, name) 
                    
            if os.path.isdir(srcname): 
                files.extend( self._copy_folder(srcname, dstname) )             
            else: 
                shutil.copy(srcname, dstname)
                files.append(srcname)
                # if the file extension is sh, set executable permissions
                if dstname.endswith(".sh") or dstname.endswith(".bat"):
                    # make it readable and executable for everybody
                    os.chmod(dstname, 0777)        
        
        return files
    





def _move_data(path):
    """
    Rename directory to backup name, if backup currently exists replace it.
    """
    if path and os.path.exists(path):
        dirname, basename = os.path.split(path)
        new_basename = "%s.old" % basename
        backup_path = os.path.join(dirname, new_basename)
        if os.path.exists(backup_path):
            shutil.rmtree(backup_path)

        try: 
            os.rename(path, backup_path)
        except WindowsError:
            # On windows intermittent problems with sqlite db file occur
            pc = sgtk.pipelineconfig.from_path(path)
            db_path = pc.get_path_cache_location()
            if os.path.exists(db_path):
                print 'Removing db %s' % db_path
                # Importing pdb allows the deletion of the sqlite db sometimes...
                import pdb
                # try multiple times, waiting longer in between
                for count in range(5):
                    try:
                        os.remove(db_path)
                        break
                    except WindowsError:
                        time.sleep(count*2) 
            os.rename(path, backup_path)
